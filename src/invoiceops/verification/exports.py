"""Grade episode exports written by the OpenEnv server (``INVOICEOPS_EXPORT_DIR``).

This runs in the verifier container, which has the private task specs; the agent-facing
container that produced the exports does not.
"""

from __future__ import annotations

import json
from pathlib import Path

from invoiceops.episode import Episode
from invoiceops.tasks.store import DEFAULT_TASK_ROOT, load_bundle
from invoiceops.verification.verifier import VerifierResult, verify


def grade_export(path: Path, task_root: Path = DEFAULT_TASK_ROOT) -> VerifierResult:
    export = json.loads(path.read_text())
    bundle = load_bundle(export["task_id"], task_root)
    initial = Episode(bundle.public.world, bundle.public.task_id).initial_snapshot
    return verify(bundle.public.world, bundle.private, initial, export["final_snapshot"])


def grade_directory(
    exports: Path, out: Path, task_root: Path = DEFAULT_TASK_ROOT
) -> list[VerifierResult]:
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(exports.glob("*.json")):
        result = grade_export(path, task_root)
        (out / path.name).write_text(result.model_dump_json(indent=1))
        results.append(result)
    return results
