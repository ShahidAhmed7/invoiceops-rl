"""Incrementally mirror a run directory on the ``invoiceops-runs`` volume to local disk.

    uv run --frozen --group modal --env-file .env python -m modal_app.sync_run <run_name>
        [--local-root runs/modal/training] [--interval 45] [--once] [--verify-only]

Each pass lists the remote prefix recursively, downloads new or changed files to a
``.part`` staging file, verifies sha256, and renames atomically. ``.tmp`` files
(unfinalized shards) are never mirrored. ``--until-done`` keeps syncing until the
remote manifest reports a terminal status and every manifest file verifies locally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from modal_app.budget import ROOT

VOLUME_NAME = "invoiceops-runs"
LOCAL_TRAINING = ROOT / "runs" / "modal" / "training"
TERMINAL_STATUSES = {"completed", "failed", "stopped_wallclock"}
STATE_FILE = ".sync_state.json"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_file(entry: Any) -> bool:
    ftype = getattr(entry, "type", None)
    return ftype is None or int(ftype) == 1  # FileEntryType.FILE


def _remote_listing(vol: Any, remote_root: str) -> dict[str, Any]:
    root = remote_root.strip("/")
    entries: dict[str, Any] = {}
    for entry in vol.listdir(root, recursive=True):
        if not _is_file(entry):
            continue
        rel = entry.path.lstrip("/")
        if rel.startswith(root + "/"):
            rel = rel[len(root) + 1 :]
        entries[rel] = entry
    return entries


def _download(vol: Any, remote_path: str, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with open(tmp, "wb") as fh:
        vol.read_file_into_fileobj(remote_path, fh)
        fh.flush()
        os.fsync(fh.fileno())
    digest = _sha256_file(tmp)
    os.replace(tmp, dest)
    return digest


def _load_state(local_dir: Path) -> dict[str, Any]:
    path = local_dir / STATE_FILE
    if path.exists():
        return json.loads(path.read_text())
    return {"files": {}, "passes": 0, "synced_utc": None}


def _save_state(local_dir: Path, state: dict[str, Any]) -> None:
    tmp = local_dir / (STATE_FILE + ".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True))
    os.replace(tmp, local_dir / STATE_FILE)


def sync_once(vol: Any, remote_root: str, local_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    """One pass over the remote prefix; returns per-pass stats."""
    remote_root = remote_root.strip("/")
    local_dir.mkdir(parents=True, exist_ok=True)
    listing = _remote_listing(vol, remote_root)
    stats = {"downloaded": [], "skipped": 0, "failed": [], "checked_utc": time.time()}
    for rel, entry in sorted(listing.items()):
        if rel.endswith(".tmp") or rel.endswith(".part"):
            continue
        prev = state["files"].get(rel)
        if prev and prev["size"] == entry.size and prev["mtime"] == entry.mtime:
            stats["skipped"] += 1
            continue
        dest = local_dir / rel
        try:
            digest = _download(vol, entry.path, dest)
        except Exception as exc:  # keep mirroring other files; record the failure
            stats["failed"].append({"file": rel, "error": repr(exc)})
            continue
        state["files"][rel] = {
            "size": entry.size,
            "mtime": entry.mtime,
            "sha256": digest,
        }
        stats["downloaded"].append(rel)
    state["passes"] = state.get("passes", 0) + 1
    state["synced_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save_state(local_dir, state)
    return stats


def verify_manifest(local_dir: Path) -> dict[str, Any]:
    """Compare local files against the run manifest's recorded sha256s."""
    manifest_path = local_dir / "manifest.json"
    result: dict[str, Any] = {"checked": 0, "ok": 0, "missing": [], "mismatched": []}
    if not manifest_path.exists():
        result["error"] = "no manifest.json mirrored yet"
        return result
    manifest = json.loads(manifest_path.read_text())
    result["manifest_status"] = manifest.get("status")
    for rel, info in sorted((manifest.get("files") or {}).items()):
        result["checked"] += 1
        path = local_dir / rel
        if not path.exists():
            result["missing"].append(rel)
            continue
        if _sha256_file(path) != info.get("sha256"):
            result["mismatched"].append(rel)
            continue
        result["ok"] += 1
    return result


def remote_status(local_dir: Path) -> str | None:
    manifest = local_dir / "manifest.json"
    if not manifest.exists():
        return None
    try:
        return json.loads(manifest.read_text()).get("status")
    except json.JSONDecodeError:
        return None


def mirror(
    vol: Any,
    run_name: str,
    local_dir: Path,
    *,
    interval: float = 45.0,
    once: bool = False,
    remote_root: str | None = None,
) -> int:
    """Sync until the run reaches a terminal status and the mirror verifies."""
    root = remote_root or f"train/{run_name}"
    local_dir.mkdir(parents=True, exist_ok=True)
    state = _load_state(local_dir)
    while True:
        try:
            stats = sync_once(vol, root, local_dir, state)
        except Exception as exc:
            # The remote run dir may not exist yet, or a transient API error; keep trying.
            print(f"[sync] pass failed: {exc!r}", flush=True)
            if once:
                return 1
            time.sleep(interval)
            continue
        print(
            f"[sync] +{len(stats['downloaded'])} files "
            f"({stats['skipped']} unchanged, {len(stats['failed'])} failed)",
            flush=True,
        )
        for failure in stats["failed"]:
            print(f"[sync] FAILED {failure['file']}: {failure['error']}", flush=True)
        status = remote_status(local_dir)
        if once:
            return 1 if stats["failed"] else 0
        if status in TERMINAL_STATUSES and not stats["downloaded"] and not stats["failed"]:
            verify = verify_manifest(local_dir)
            print(f"[sync] terminal status {status!r}; verify: {json.dumps(verify)}", flush=True)
            (local_dir / "sync_verify.json").write_text(json.dumps(verify, indent=1))
            return 0 if not verify["missing"] and not verify["mismatched"] else 1
        time.sleep(interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_name")
    parser.add_argument("--local-root", type=Path, default=LOCAL_TRAINING)
    parser.add_argument("--remote-root", help="volume-relative prefix; default train/<run_name>")
    parser.add_argument("--interval", type=float, default=45.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)

    local_dir = args.local_root / args.run_name
    if args.verify_only:
        print(json.dumps(verify_manifest(local_dir), indent=1))
        return 0

    import modal

    vol = modal.Volume.from_name(VOLUME_NAME)
    return mirror(
        vol,
        args.run_name,
        local_dir,
        interval=args.interval,
        once=args.once,
        remote_root=args.remote_root,
    )


if __name__ == "__main__":
    sys.exit(main())
