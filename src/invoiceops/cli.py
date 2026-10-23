"""The ``invoiceops`` command line."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO

from invoiceops import __version__
from invoiceops.domain.money import format_minor
from invoiceops.episode import Episode
from invoiceops.runs import (
    RUNS_ROOT,
    find_run,
    load_episodes,
    now_iso,
    record_episode,
    save_episode,
)
from invoiceops.tasks.build import content_hash, write_suite
from invoiceops.tasks.model import TaskBundle
from invoiceops.tasks.store import DEFAULT_TASK_ROOT, load_bundle, task_ids
from invoiceops.tools.spec import TOOLS, TOOLS_BY_NAME
from invoiceops.verification.verifier import verify

MINIMUM_FAMILIES = ("F01", "F03", "F05", "F06", "F08", "F10")


def _print(text: str = "", out: TextIO | None = None) -> None:
    print(text, file=out or sys.stdout)


# -- tasks ---------------------------------------------------------------------------------


def cmd_build_tasks(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if args.check:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            write_suite(Path(tmp))
            stale = [
                str(p.relative_to(tmp))
                for p in sorted(Path(tmp).rglob("*.json"))
                if not (root / p.relative_to(tmp)).exists()
                or (root / p.relative_to(tmp)).read_text() != p.read_text()
            ]
        if stale:
            _print(f"{len(stale)} task files are out of date, e.g. {stale[:3]}")
            return 1
        _print("task files are up to date")
        return 0
    bundles = write_suite(root)
    _print(f"wrote {len(bundles)} tasks to {root}")
    return 0


def _describe_public(bundle: TaskBundle) -> list[str]:
    world = bundle.public.world
    inv = next(i for i in world.invoices if i.id == world.queue[0])
    money = world.company.currency
    return [
        f"Task {bundle.public.task_id}  (revision {content_hash(bundle)})",
        f"Company: {world.company.name} · business date {world.company.as_of}",
        "",
        "Prompt shown to the agent:",
        *("  " + line for line in bundle.public.prompt.splitlines()),
        "",
        f"Queued invoice {inv.id}: {format_minor(inv.total_minor, money)}, PO {inv.po_id}, "
        f"{len(inv.lines)} line(s)",
        f"Records: {len(world.purchase_orders)} PO revisions, {len(world.receipts)} receipts, "
        f"{len(world.invoices)} invoices, {len(world.credit_notes)} credit notes, "
        f"{len(world.payments)} payments, {len(world.documents)} documents, "
        f"{len(world.events)} scripted replies",
    ]


def _describe_private(bundle: TaskBundle) -> list[str]:
    p = bundle.private
    money = bundle.public.world.company.currency
    lines = [
        "",
        "--- PRIVATE: expected outcome (do not read before a blind solve) ---",
        f"Family {p.family} ({p.family_name}), variant {p.variant}, split {p.split}, "
        f"world {p.world_id}, difficulty hypothesis: {p.difficulty_hypothesis}",
        f"Why: {p.rationale}",
    ]
    for n, outcome in enumerate(p.expectation.outcomes, 1):
        lines.append(f"Accepted outcome {n} ({outcome.label}):")
        reasons = " or ".join(r.value for r in outcome.reason_codes)
        lines.append(f"  - case status {outcome.status.value}, reason {reasons}")
        if outcome.payment:
            credits = ", ".join(outcome.payment.credit_note_ids) or "none"
            lines.append(
                f"  - exactly one payment proposal ever, still active, of "
                f"{format_minor(outcome.payment.amount_minor, money)} (credit notes: {credits})"
            )
        else:
            lines.append("  - no payment proposal at any point")
        if outcome.approval_required:
            lines.append("  - approved by an authorised approver before the proposal")
        for req in outcome.clarifications:
            cite = "; ".join(" or ".join(g) for g in req.cite)
            types = " or ".join(t.value for t in req.request_types)
            lines.append(f"  - {types} request to {' or '.join(req.recipient_roles)} citing {cite}")
        if outcome.approval_requested_from:
            roles = " or ".join(outcome.approval_requested_from)
            lines.append(f"  - an approval request was sent to {roles}")
        if outcome.evidence:
            cite = "; ".join(" or ".join(g) for g in outcome.evidence)
            lines.append(f"  - disposition evidence cites {cite}")
    lines.append(
        "Always required: case submitted, submission consistent with the system, no "
        "source record changed, no other invoice touched, at most one proposal ever."
    )
    return lines


def cmd_show_task(args: argparse.Namespace) -> int:
    bundle = load_bundle(args.task_id, Path(args.root))
    for line in _describe_public(bundle) + (_describe_private(bundle) if args.private else []):
        _print(line)
    return 0


def cmd_show_family(args: argparse.Namespace) -> int:
    rows = [load_bundle(t, Path(args.root)) for t in task_ids(root=Path(args.root))]
    rows = [b for b in rows if b.private.family == args.family_id]
    if not rows:
        _print(f"no tasks for family {args.family_id}")
        return 1
    _print(f"Family {args.family_id}: {rows[0].private.family_name} ({len(rows)} tasks)")
    for b in sorted(rows, key=lambda b: (b.private.split, b.private.world_id)):
        outcome = b.private.expectation.outcomes[0]
        pay = format_minor(outcome.payment.amount_minor, "USD") if outcome.payment else "no payment"
        _print(
            f"- {b.public.task_id} [{b.private.split}] {b.private.world_id} v{b.private.variant}: "
            f"{outcome.status.value}/{outcome.reason_codes[0].value}, {pay}"
            f"{', approval' if outcome.approval_required else ''}. {b.private.rationale}"
        )
    return 0


def review_sample(path: str, root: Path = DEFAULT_TASK_ROOT) -> list[str]:
    candidates = [load_bundle(t, root) for t in task_ids(root=root)]
    candidates = sorted(
        (b for b in candidates if b.private.split in ("dev", "test")),
        key=lambda b: b.public.task_id,
    )
    families = sorted({b.private.family for b in candidates})
    if path == "minimum":
        families = [f for f in families if f in MINIMUM_FAMILIES]
    return [next(b.public.task_id for b in candidates if b.private.family == f) for f in families]


def cmd_review_sample(args: argparse.Namespace) -> int:
    for task_id in review_sample(args.path, Path(args.root)):
        _print(task_id)
    return 0


# -- play and grade -----------------------------------------------------------------------


PLAY_HELP = """Commands:
  tools                      list tools and their arguments
  <tool> {json arguments}    call a tool, e.g.  get_invoice {"invoice_id": "INV-123"}
  <tool> key=value ...       simple form; lists as a,b,c; e.g.  get_receipts po_id=PO-1
  help                       show this help
  quit                       stop without submitting
The task ends when you call submit_case."""


def _parse_simple(tool: str, parts: list[str]) -> dict[str, Any]:
    fields = TOOLS_BY_NAME[tool].args.model_fields
    args: dict[str, Any] = {}
    for part in parts:
        key, _, value = part.partition("=")
        annotation = str(fields[key].annotation) if key in fields else ""
        if "list" in annotation:
            args[key] = [v for v in value.split(",") if v]
        elif "int" in annotation and value.lstrip("-").isdigit():
            args[key] = int(value)
        else:
            args[key] = value
    return args


def cmd_play(args: argparse.Namespace) -> int:
    bundle = load_bundle(args.task, Path(args.root))
    episode = Episode(bundle.public.world, bundle.public.task_id, max_steps=bundle.public.max_steps)
    source: TextIO = open(args.script) if args.script else sys.stdin  # noqa: SIM115
    _print(bundle.public.prompt)
    _print()
    _print(PLAY_HELP)
    try:
        while not episode.done:
            if source is sys.stdin:
                print("> ", end="", flush=True)
            line = source.readline()
            if not line:
                break
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tool, _, rest = line.partition(" ")
            if tool in ("quit", "exit"):
                break
            if tool == "help":
                _print(PLAY_HELP)
                continue
            if tool == "tools":
                for t in TOOLS:
                    fields = ", ".join(t.args.model_fields)
                    _print(f"- {t.name}({fields}): {t.description}")
                continue
            if tool not in TOOLS_BY_NAME:
                _print(f"Unknown command {tool!r}. Type help.")
                continue
            rest = rest.strip()
            try:
                arguments = (
                    json.loads(rest)
                    if rest.startswith("{")
                    else _parse_simple(tool, shlex.split(rest))
                )
            except (ValueError, KeyError) as exc:
                _print(f"Could not parse arguments: {exc}")
                continue
            _print(json.dumps(episode.step(tool, arguments), indent=2, ensure_ascii=False))
    finally:
        if source is not sys.stdin:
            source.close()
    run_id = args.run_id or f"play-{bundle.public.task_id}-{now_iso().replace(':', '')}"
    run_dir = Path(args.runs) / run_id
    record = record_episode(episode, run_id, "human", 0)
    save_episode(run_dir, record)
    _print(
        f"\nSaved run {run_id} ({episode.end_reason or 'not submitted'}). "
        f"Grade it with: invoiceops grade {run_id}"
    )
    return 0


def cmd_grade(args: argparse.Namespace) -> int:
    run_dir = find_run(args.run_id, Path(args.runs))
    status = 0
    for record in load_episodes(run_dir):
        bundle = load_bundle(record.task_id, Path(args.root))
        initial = Episode(bundle.public.world, record.task_id).initial_snapshot
        result = verify(bundle.public.world, bundle.private, initial, record.final_snapshot)
        verdict = "PASS" if result.passed else ("UNSCORABLE" if not result.scorable else "FAIL")
        _print(f"{record.task_id} attempt {record.attempt}: {verdict}")
        for check in result.failed_checks():
            _print(f"  - {check.name}: {check.detail}")
        if result.critical_violations:
            _print(f"  critical: {', '.join(result.critical_violations)}")
        status |= 0 if result.passed else 1
    return status


# -- evaluation and review --------------------------------------------------------------------


def cmd_evaluate(args: argparse.Namespace) -> int:
    from invoiceops.agents.openai_runner import ModelConfig
    from invoiceops.evaluation.run import evaluate

    root = Path(args.root)
    tasks = [t for split in args.split for t in task_ids(split, root)]
    agents = (
        ["oracle", "noop", "always_hold", "always_pay", "random"]
        if args.agent == "all-scripted"
        else [args.agent]
    )
    model = None
    if args.agent == "model":
        if not (args.base_url and args.model):
            _print("--base-url and --model are required for --agent model")
            return 2
        model = ModelConfig(
            base_url=args.base_url,
            model=args.model,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tool_calls=args.max_tool_calls,
        )
    stamp = now_iso().replace(":", "")
    for agent in agents:
        run_id = (
            args.run_id
            if args.run_id and len(agents) == 1
            else f"{agent}-{'-'.join(args.split)}-{stamp}"
        )
        run_dir = Path(args.runs) / run_id
        summary = evaluate(
            agent,
            tasks,
            run_dir,
            attempts=args.attempts,
            model=model,
            prompt_version=args.prompt,
            concurrency=args.concurrency,
            task_root=root,
            extra_config={"splits": args.split},
        )
        success = summary["task_mean_success"]
        _print(
            f"{agent}: task-mean success "
            f"{'n/a' if success is None else f'{100 * success:.1f}%'} over {summary['tasks']} "
            f"tasks; report {run_dir / 'report.md'}"
        )
    return 0


def cmd_verify_mutations(args: argparse.Namespace) -> int:
    from invoiceops.verification.mutations import run_mutations

    root = Path(args.root)
    ids = [t for split in args.split for t in task_ids(split, root)]
    rows = []
    unexpected = 0
    for task_id in ids:
        for r in run_mutations(load_bundle(task_id, root)):
            if not r.applicable:
                continue
            expected = "accepted" if r.kind == "alternative" else "rejected"
            got = "accepted" if r.passed else "rejected"
            unexpected += got != expected
            rows.append(
                f"| {task_id} | {r.kind} | {r.name} | {expected} | **{got}** | "
                f"{r.reason.replace('|', '/')[:160]} |"
            )
    report = "\n".join(
        [
            "# Verifier mutation report",
            "",
            f"{len(rows)} cases on {len(ids)} tasks; {unexpected} unexpected results.",
            "",
            "| Task | Kind | Case | Expected | Result | Verifier reason |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
        ]
    )
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report)
        _print(f"wrote {args.report}: {len(rows)} cases, {unexpected} unexpected")
    else:
        _print(report)
    return 1 if unexpected else 0


def cmd_audit_visibility(args: argparse.Namespace) -> int:
    bundle = load_bundle(args.task, Path(args.root))
    ep = Episode(bundle.public.world, bundle.public.task_id, max_steps=100_000)
    _print("== Prompt ==")
    _print(bundle.public.prompt)
    _print("\n== Tools ==")
    for t in TOOLS:
        _print(f"- {t.name}: {t.description}")
    _print("\n== Everything readable through the tools at the start of the episode ==")
    collections = [
        "invoices",
        "purchase_orders",
        "receipts",
        "vendors",
        "documents",
        "credit_notes",
        "payments",
    ]
    getters = {
        "invoices": ("get_invoice", "invoice_id"),
        "purchase_orders": ("get_purchase_order", "po_id"),
        "vendors": ("get_vendor", "vendor_id"),
        "documents": ("get_document", "document_id"),
    }
    for collection in collections:
        cursor = None
        while True:
            page = ep.step("search_records", {"collection": collection, "cursor": cursor})["result"]
            for row in page["results"]:
                if collection in getters:
                    tool, key = getters[collection]
                    _print(
                        json.dumps(ep.step(tool, {key: row["id"]})["result"], ensure_ascii=False)
                    )
                else:
                    _print(json.dumps(row, ensure_ascii=False))
            cursor = page["next_cursor"]
            if cursor is None:
                break
    _print("\n== Private fields that must not appear above ==")
    _print(
        f"family={bundle.private.family} split={bundle.private.split} "
        f"rationale={bundle.private.rationale!r}"
    )
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    from invoiceops.evaluation.replay import render

    run_dir = find_run(args.run_id, Path(args.runs))
    out = Path(args.out) if args.out else run_dir / "replay"
    out.mkdir(parents=True, exist_ok=True)
    for record in load_episodes(run_dir):
        if args.task and record.task_id != args.task:
            continue
        path = out / f"{record.task_id}__{record.attempt}.html"
        path.write_text(render(record))
        _print(str(path))
    return 0


def cmd_verify_exports(args: argparse.Namespace) -> int:
    from invoiceops.verification.exports import grade_directory

    results = grade_directory(Path(args.exports), Path(args.out), Path(args.root))
    for result in results:
        verdict = "PASS" if result.passed else ("UNSCORABLE" if not result.scorable else "FAIL")
        _print(f"{result.task_id}: {verdict} reward={result.reward}")
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    from invoiceops.tools.spec import openai_tools

    _print(json.dumps(openai_tools(), indent=2))
    return 0


# -- parser ----------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="invoiceops", description="InvoiceOps RL environment")
    parser.add_argument("--version", action="version", version=f"invoiceops {__version__}")
    parser.add_argument("--root", default=str(DEFAULT_TASK_ROOT), help="task directory")
    parser.add_argument("--runs", default=str(RUNS_ROOT), help="run output directory")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("build-tasks", help="regenerate task files from code")
    p.add_argument("--check", action="store_true", help="fail if files on disk are out of date")
    p.set_defaults(func=cmd_build_tasks)

    p = sub.add_parser("show-task", help="print a task in readable form")
    p.add_argument("task_id")
    p.add_argument("--private", action="store_true", help="also show the expected outcome")
    p.set_defaults(func=cmd_show_task)

    p = sub.add_parser("show-family", help="list a family's tasks with expected outcomes")
    p.add_argument("family_id")
    p.set_defaults(func=cmd_show_family)

    p = sub.add_parser("review-sample", help="deterministic review sample, one task per family")
    p.add_argument("--path", choices=["standard", "minimum"], default="standard")
    p.set_defaults(func=cmd_review_sample)

    p = sub.add_parser("play", help="solve a task yourself through the agent tools")
    p.add_argument("--task", required=True)
    p.add_argument("--run-id")
    p.add_argument("--script", help="read commands from a file instead of the keyboard")
    p.set_defaults(func=cmd_play)

    p = sub.add_parser("grade", help="grade a saved run")
    p.add_argument("run_id")
    p.set_defaults(func=cmd_grade)

    p = sub.add_parser("evaluate", help="run an agent on task splits and write a report")
    p.add_argument(
        "--agent",
        required=True,
        choices=["oracle", "noop", "always_hold", "always_pay", "random", "all-scripted", "model"],
    )
    p.add_argument("--split", action="append", choices=["train", "dev", "test"], required=True)
    p.add_argument("--attempts", type=int, default=1)
    p.add_argument("--concurrency", type=int, default=1)
    p.add_argument("--run-id")
    p.add_argument("--base-url")
    p.add_argument("--model")
    p.add_argument("--prompt", choices=["v1", "v2"], default="v1")
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.8)
    p.add_argument("--max-tool-calls", type=int, default=40)
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser(
        "verify-mutations", help="check the verifier against wrong and alternative outcomes"
    )
    p.add_argument("--split", action="append", choices=["train", "dev", "test"], default=None)
    p.add_argument("--report")
    p.set_defaults(func=cmd_verify_mutations)

    p = sub.add_parser("audit-visibility", help="print everything an agent can see for a task")
    p.add_argument("--task", required=True)
    p.set_defaults(func=cmd_audit_visibility)

    p = sub.add_parser("replay", help="write HTML replays for a saved run")
    p.add_argument("run_id")
    p.add_argument("--task")
    p.add_argument("--out")
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser("verify-exports", help="grade episode exports from the OpenEnv server")
    p.add_argument("--exports", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_verify_exports)

    p = sub.add_parser("tools", help="print the tool schemas")
    p.set_defaults(func=cmd_tools)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) == "verify-mutations" and args.split is None:
        args.split = ["train", "dev", "test"]
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
