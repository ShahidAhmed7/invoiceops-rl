"""Static HTML replay of one saved episode: every step, its observation, and the verdict."""

from __future__ import annotations

import html
import json
from typing import Any

from invoiceops.runs import EpisodeRecord

_STYLE = """
:root { --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6a64; --line:#e3e1da; --ok:#1f7a4d;
        --bad:#b3261e; --card:#ffffff; --code:#f2f0ea; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#161614; --fg:#ecebe6; --muted:#a3a29b; --line:#33322e; --ok:#5fc48f;
          --bad:#f08a80; --card:#1f1f1c; --code:#26261f; }
}
body { background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, sans-serif;
       margin:0 auto; max-width:1000px; padding:24px 16px; }
h1 { font-size:22px; margin:0 0 4px; } .muted { color:var(--muted); }
.verdict { font-weight:600; } .ok { color:var(--ok); } .bad { color:var(--bad); }
.step { background:var(--card); border:1px solid var(--line); border-radius:8px;
        padding:10px 12px; margin:10px 0; }
.step header { display:flex; gap:12px; align-items:baseline; flex-wrap:wrap; }
pre { background:var(--code); padding:8px; border-radius:6px; overflow-x:auto;
      white-space:pre-wrap; word-break:break-word; font-size:13px; margin:6px 0 0; }
table { border-collapse:collapse; width:100%; } td, th { border-bottom:1px solid var(--line);
      text-align:left; padding:6px 4px; vertical-align:top; }
"""


def _pre(value: Any, limit: int = 3000) -> str:
    text = json.dumps(value, indent=2, ensure_ascii=False)
    if len(text) > limit:
        text = text[:limit] + "\n… (truncated)"
    return f"<pre>{html.escape(text)}</pre>"


def render(record: EpisodeRecord) -> str:
    v = record.verifier
    if v is None:
        verdict = '<span class="verdict bad">Unscorable (infrastructure error)</span>'
    elif v.passed:
        outcome = html.escape(v.matched_outcome or "")
        verdict = f'<span class="verdict ok">Passed</span> (outcome: {outcome})'
    else:
        verdict = '<span class="verdict bad">Failed</span>'
    steps = []
    for event in record.log:
        cls = "ok" if event.result_code == "ok" else "bad"
        changed = "state changed" if event.state_before != event.state_after else "no state change"
        steps.append(
            f'<section class="step"><header>'
            f"<strong>#{event.step} {html.escape(event.tool)}</strong>"
            f'<span class="{cls}">{html.escape(event.result_code)}</span>'
            f'<span class="muted">{changed}</span></header>'
            f"{_pre(event.arguments)}{_pre(event.observation)}</section>"
        )
    checks = ""
    if v is not None:
        rows = [*v.global_checks]
        best = max(
            v.outcomes, key=lambda o: (o.passed, sum(c.passed for c in o.checks)), default=None
        )
        if best is not None:
            rows += best.checks
        checks = (
            "<table><tr><th>Check</th><th>Result</th><th>Detail</th></tr>"
            + "".join(
                f'<tr><td>{html.escape(c.name)}</td><td class="{"ok" if c.passed else "bad"}">'
                f"{'pass' if c.passed else 'fail'}</td><td>{html.escape(c.detail)}</td></tr>"
                for c in rows
            )
            + "</table>"
        )
        if v.critical_violations:
            checks += (
                f'<p class="bad">Critical: {html.escape(", ".join(v.critical_violations))}</p>'
            )
    case = record.final_snapshot.get("cases", [])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Episode Replay</title><style>{_STYLE}</style></head><body>
<h1>Task {html.escape(record.task_id)} · attempt {record.attempt}</h1>
<p class="muted">Agent {html.escape(record.agent)} · run {html.escape(record.run_id)} ·
{record.steps} steps · ended: {html.escape(record.end_reason or "not ended")}</p>
<p>{verdict}</p>
<h2>Verifier</h2>{checks or "<p>No verifier result.</p>"}
<h2>Final case</h2>{_pre(case)}
<h2>Steps</h2>{"".join(steps)}
</body></html>
"""
