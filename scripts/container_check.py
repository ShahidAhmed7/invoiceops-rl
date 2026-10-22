"""Phase 8 isolation check against the real containers.

Run from the repository root after building both images:

    docker build -f containers/env.Dockerfile -t invoiceops-env .
    docker build -f containers/verifier.Dockerfile -t invoiceops-verifier .
    uv run python scripts/container_check.py

The host acts as the trusted controller: it chooses tasks and holds the oracle trajectories.
Checks:
1. The agent-facing image contains no private task specs, verifier, family builders, or oracle,
   and runs as a non-root user.
2. Three concurrent WebSocket sessions (two on the same task) stay isolated: each export
   matches the state the same actions produce in-process.
3. The public ``state`` response exposes only episode_id, step_count, and task_id.
4. The verifier container, with no network and read-only exports, passes the two correct
   episodes and fails the do-nothing one.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

from websockets.sync.client import connect

from invoiceops.state.store import canonical_json
from invoiceops.tasks.store import load_bundle, task_ids
from invoiceops.verification.mutations import oracle_actions, replay

ENV_IMAGE = "invoiceops-env"
VERIFIER_IMAGE = "invoiceops-verifier"
PORT = 18766


def sh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=check)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def check_image_contents() -> None:
    probe = (
        "import importlib.util as u, os, pathlib;"
        "mods=['invoiceops.verification','invoiceops.families','invoiceops.agents',"
        "'invoiceops.evaluation','invoiceops.adapters.trl_env'];"
        "print('present=' + ','.join(m for m in mods if u.find_spec(m)));"
        "print(sum(1 for _ in pathlib.Path('/').rglob('private.json')));"
        "print(os.getuid())"
    )
    out = sh("docker", "run", "--rm", "--network", "none", ENV_IMAGE, "python", "-c", probe).stdout
    present, privates, uid = out.strip().splitlines()
    present = present.removeprefix("present=")
    if present:
        fail(f"agent image contains trusted modules: {present}")
    if privates != "0":
        fail(f"agent image contains {privates} private.json files")
    if uid == "0":
        fail("agent image runs as root")
    print("ok: agent image has no private specs, verifier, builders, or oracle; runs as uid", uid)


def session_run(ws: Any, task_id: str, actions: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    ws.send(json.dumps({"type": "reset", "data": {"task_id": task_id}}))
    json.loads(ws.recv())
    version = 1
    last: dict[str, Any] = {}
    for tool, args in actions:
        if tool == "set_disposition":
            args = {**args, "expected_version": version}
        ws.send(
            json.dumps(
                {
                    "type": "step",
                    "data": {"type": "call_tool", "tool_name": tool, "arguments": args},
                }
            )
        )
        last = json.loads(ws.recv())["data"]
        obs = json.loads(last["observation"]["result"]["content"][0]["text"])
        if tool == "set_disposition" and obs["ok"]:
            version = obs["result"]["version"]
    ws.send(json.dumps({"type": "state"}))
    state = json.loads(ws.recv())["data"]
    if set(state) != {"episode_id", "step_count", "task_id"}:
        fail(f"state exposes more than safe metadata: {sorted(state)}")
    return {"last": last, "state": state}


def main() -> None:
    check_image_contents()
    tasks = task_ids("dev")
    a = load_bundle(tasks[0])
    b = load_bundle(tasks[1])
    a_actions, b_actions = oracle_actions(a), oracle_actions(b)
    inv = a.private.expectation.invoice_id
    noop_actions = [
        (
            "submit_case",
            {
                "invoice_id": inv,
                "status": "ready_for_payment",
                "reason_code": "matched",
                "amount_proposed_minor": 0,
                "evidence_ids": [inv],
                "summary": "nothing done",
            },
        )
    ]

    work = Path(tempfile.mkdtemp(prefix="invoiceops-containers-"))
    exports, results = work / "exports", work / "results"
    exports.mkdir()
    results.mkdir()
    exports.chmod(0o777)
    results.chmod(0o777)
    name = f"invoiceops-env-check-{int(time.time())}"
    sh(
        "docker",
        "run",
        "-d",
        "--name",
        name,
        "-p",
        f"127.0.0.1:{PORT}:8000",
        "-v",
        f"{exports}:/exports",
        ENV_IMAGE,
    )
    try:
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2):
                    break
            except OSError:
                time.sleep(1)
        else:
            fail(
                "server did not become healthy:\n" + sh("docker", "logs", name, check=False).stderr
            )
        url = f"ws://127.0.0.1:{PORT}/ws"
        with connect(url) as ws_a, connect(url) as ws_b, connect(url) as ws_c:
            # Interleave: C starts on the same task as A before A finishes.
            ws_c.send(json.dumps({"type": "reset", "data": {"task_id": a.public.task_id}}))
            ws_c.recv()
            run_a = session_run(ws_a, a.public.task_id, a_actions)
            run_b = session_run(ws_b, b.public.task_id, b_actions)
            run_c = session_run(ws_c, a.public.task_id, noop_actions)
        for label, run in (("A", run_a), ("B", run_b), ("C", run_c)):
            if not run["last"].get("done"):
                fail(f"session {label} did not end")
        if run_a["state"]["episode_id"] == run_c["state"]["episode_id"]:
            fail("two sessions shared an episode")
        print("ok: three concurrent sessions ran; state exposes only safe metadata")
    finally:
        sh("docker", "rm", "-f", name, check=False)

    exported = {
        json.loads(p.read_text())["episode_id"]: json.loads(p.read_text())
        for p in exports.glob("*.json")
    }
    if len(exported) != 3:
        fail(f"expected 3 exports, found {len(exported)}")
    for label, bundle, actions, run in (("A", a, a_actions, run_a), ("B", b, b_actions, run_b)):
        export = exported[run["state"]["episode_id"]]
        expected = replay(bundle, actions).snapshot()
        mine = {k: v for k, v in export["final_snapshot"].items()}
        if canonical_json(mine) != canonical_json(expected):
            fail(f"session {label} final state differs from the in-process replay")
    print("ok: exported states match in-process replays (no cross-session interference)")

    proc = sh(
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "-v",
        f"{exports}:/exports:ro",
        "-v",
        f"{results}:/results",
        VERIFIER_IMAGE,
        check=False,
    )
    if proc.returncode != 0:
        fail("verifier container failed:\n" + proc.stderr)
    verdicts = {
        r["task_id"] + ":" + str(r["passed"]): r
        for r in (json.loads(p.read_text()) for p in results.glob("*.json"))
    }
    passed = sorted(k for k in verdicts if k.endswith(":True"))
    failed = sorted(k for k in verdicts if k.endswith(":False"))
    want_pass = sorted({f"{a.public.task_id}:True", f"{b.public.task_id}:True"})
    if passed != want_pass or failed != [f"{a.public.task_id}:False"]:
        fail(f"unexpected verdicts: passed={passed} failed={failed}")
    print("ok: offline verifier container passed the correct episodes and failed the no-op")
    shutil.rmtree(work, ignore_errors=True)
    print("ALL CONTAINER CHECKS PASSED")


if __name__ == "__main__":
    main()
