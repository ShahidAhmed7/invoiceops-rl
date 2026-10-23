import collections
import decimal
import json
import pathlib
import re

root=pathlib.Path(__file__).resolve().parents[4]
rows=[]
for path in sorted((root/'tasks').glob('*/*/public.json')):
    p=json.loads(path.read_text()); w=p['world']; private=json.loads(path.with_name('private.json').read_text())
    inv=next(i for i in w['invoices'] if i['id']==w['queue'][0]); vendor=next(v for v in w['vendors'] if v['id']==inv['vendor_id'])
    assert all(sum(line['quantity']*line['unit_price_minor'] for line in i['lines'])==i['total_minor'] for i in w['invoices'])
    asof=w['company']['as_of']
    policies=[]
    for doc in w['documents']:
        if doc['kind']!='policy': continue
        match=re.search(r'Effective from (\d{4}-\d{2}-\d{2})(?: until (\d{4}-\d{2}-\d{2}) \(exclusive\))?',doc['body'])
        if match and match[1]<=asof and (not match[2] or asof<match[2]): policies.append((match[1],doc))
    assert len(policies)==1
    doc=policies[0][1]; text=doc['body']
    pct=decimal.Decimal(re.search(r'no more than ([\d.]+)%',text)[1])
    cap=int(decimal.Decimal(re.search(r'and no more than\s+USD ([\d,]+\.\d{2})',text)[1].replace(',',''))*100)
    selflimit=int(decimal.Decimal(re.search(r'payments up to USD ([\d,]+\.\d{2}) without approval',text)[1].replace(',',''))*100)
    partial='pay only for the received units' in text
    po=max((po for po in w['purchase_orders'] if po['id']==inv['po_id'] and po['approved_on']<=asof),key=lambda po:po['revision'])
    polines={line['line_no']:line for line in po['lines']}
    receipts=[r for r in w['receipts'] if r['po_id']==inv['po_id']]
    receipt_qty=collections.Counter()
    def add_receipts(records):
        for r in records:
            for line in r['lines']: receipt_qty[line['po_line_no']]+=line['quantity']
    add_receipts(receipts)
    used=collections.Counter()
    paidids={x['invoice_id'] for x in w['payments'] if x['status'] in ('paid','scheduled')}
    for prior in w['invoices']:
        if prior['id'] in paidids and prior['id']!=inv['id'] and prior['po_id']==inv['po_id']:
            for line in prior['lines']: used[line['po_line_no']]+=line['quantity']
    duplicate=any(i['id']!=inv['id'] and i['vendor_id']==inv['vendor_id'] and (i['vendor_invoice_number']==inv['vendor_invoice_number'] or (i['po_id'],i['total_minor'],i['invoice_date'])==(inv['po_id'],inv['total_minor'],inv['invoice_date'])) for i in w['invoices'])
    basis=sum(line['quantity']*polines[line['po_line_no']]['unit_price_minor'] for line in inv['lines'])
    variance=inv['total_minor']-basis
    tolerance=min(cap,int((decimal.Decimal(basis)*pct/100).quantize(decimal.Decimal('1'),rounding=decimal.ROUND_HALF_UP)))
    follow=[]; amount=None; credits=[]; reasons=[]
    details=f'gross={inv["total_minor"]}; PO basis={basis}; variance={variance}; tolerance={tolerance}'
    if not vendor['verified'] or vendor['remit_account']!=inv['remit_account']:
        status='on_hold';reasons=['vendor_verification'];follow=['vendor_master']
    elif duplicate:
        status='rejected';reasons=['duplicate_invoice']
    else:
        missing=any(line['po_line_no'] not in receipt_qty for line in inv['lines'])
        if missing:
            follow.append('receiving')
            new=[r for ev in w['events'] if ev['trigger']['invoice_id']==inv['id'] and 'receiving' in ev['trigger']['recipient_roles'] and 'receipt_confirmation' in ev['trigger'].get('request_types',[]) for r in ev['effects']['receipts']]
            add_receipts(new)
        missing=any(line['po_line_no'] not in receipt_qty for line in inv['lines'])
        available={line['po_line_no']:max(0,receipt_qty[line['po_line_no']]-used[line['po_line_no']]) for line in inv['lines']}
        short=any(line['quantity']>available[line['po_line_no']] for line in inv['lines'])
        details+=f'; received={dict(receipt_qty)}; consumed={dict(used)}; available={available}; partial_policy={partial}'
        if missing:
            status='on_hold';reasons=['missing_receipt']
        elif short and not partial:
            status='on_hold';reasons=['short_receipt'];follow.append('supplier')
            if any(used.values()):reasons.append('quantity_exceeds_receipt')
        elif variance>tolerance:
            status='on_hold';reasons=['price_variance'];follow.append('procurement')
        else:
            status='ready_for_payment'; reasons=['partial_receipt_paid' if short else ('matched_within_tolerance' if variance else 'matched')]
            amount=sum(min(line['quantity'],available[line['po_line_no']])*line['unit_price_minor'] for line in inv['lines'])
            eligible=[c for c in w['credit_notes'] if c['invoice_id']==inv['id'] and c['status']=='open' and not c['applied_to_payment_id']]
            if eligible:
                amount-=sum(c['amount_minor'] for c in eligible);credits=sorted(c['id'] for c in eligible);reasons=['matched_with_credit']
    approval=amount is not None and amount>selflimit
    approver=None; decline=None
    if approval:
        covering=sorted((r for r in w['roles'] if r.get('can_approve') and r['approval_limit_minor']>=amount),key=lambda r:r['approval_limit_minor'])
        approver=covering[0]['id'] if covering else None
        details+=f'; required_approver={approver}'
        override=next((o for o in w.get('approval_overrides',[]) if o['approver_role']==approver and o['invoice_id']==inv['id']),None)
        if override:
            status='on_hold';reasons=['awaiting_approval'];amount=None;credits=[];approval=False
            decline=approver
            details+=f'; approver_declines={approver}'
    expect_types={'vendor_master':['bank_detail_verification'],'receiving':['receipt_confirmation'],'supplier':['corrected_invoice'],'procurement':['price_confirmation']}
    expected_clars=[{'roles':[role],'types':expect_types[role]} for role in follow]
    outcomes=private['expectation']['outcomes']
    matches=[]
    for o in outcomes:
        pay=o['payment']
        clar_ok=len(o['clarifications'])==len(expected_clars)
        for c in o['clarifications']:
            expected=next((e for e in expected_clars if set(e['roles'])==set(c['recipient_roles'])),None)
            clar_ok=clar_ok and expected is not None and set(c.get('request_types') or [])==set(expected['types'])
        approver_ok=(not o['approval_requested_from'] and decline is None) or o['approval_requested_from']==[approver]
        matches.append(o['status']==status and bool(set(o['reason_codes'])&set(reasons)) and ((pay is None and amount is None) or (pay is not None and pay['amount_minor']==amount and sorted(pay['credit_note_ids'])==credits)) and o['approval_required']==approval and clar_ok and approver_ok)
    rows.append(dict(task=p['task_id'],family=private['family'],split=private['split'],world=private['world_id'],variant=private['variant'],policy=doc['id'],status=status,reasons=reasons,amount=amount,credits=credits,approval=approval,approver=approver,decline=decline,follow=follow,details=details,match=any(matches)))

out=pathlib.Path(__file__).resolve().with_name('spec-crosscheck.md')
body=['# Independent policy and arithmetic cross-check (re-check)','','Recomputed all 72 task outcomes from source records and the *written policy text*, independently of the oracle, family generator, policy renderer, and verifier. Updated for the post-fix rules: section 8 approval levels (lowest covering approver; scripted budget declines via `approval_overrides` produce on_hold/awaiting_approval with no payment), structured clarification request types (policy-named type per situation, plus receipt-reply events requiring `receipt_confirmation` in their trigger). Private expectations were used only for the final comparison. All invoice header totals, including distractors, were checked against their lines. This is a review cross-check, not a replacement for independent blind solves.','','Amounts below are cents. Approval is required exactly when the independently computed net proposal exceeds the written assistant limit.','','| Task | Family | Split/world | Derived result | Arithmetic/evidence | Matches private outcome |','|---|---|---|---|---|---|---|']
for r in rows:
    result=f'{r["status"]}/{" or ".join(r["reasons"])}; amount={r["amount"]}; credits={r["credits"]}; approval={r["approval"]}; approver={r["approver"]}; decline={r["decline"]}; contacts={r["follow"]}'
    body.append(f'| {r["task"]} | {r["family"]} | {r["split"]}/{r["world"]} | {result} | {r["details"]}; policy={r["policy"]} | {r["match"]} |')
body+=['',f'{sum(r["match"] for r in rows)}/{len(rows)} primary/accepted outcomes agree with the independent calculation.']
out.write_text('\n'.join(body)+'\n')
pathlib.Path('/tmp/invoiceops-crosscheck-recheck.json').write_text(json.dumps(rows,indent=2))
print(f'{sum(r["match"] for r in rows)}/{len(rows)} match')
for r in rows:
    if not r['match']: print(json.dumps(r))
