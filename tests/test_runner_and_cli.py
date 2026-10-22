from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest

from invoiceops.agents.openai_runner import InfrastructureError, ModelConfig, chat
from invoiceops.cli import main, review_sample
from invoiceops.evaluation.run import evaluate
from invoiceops.runs import load_episodes
from invoiceops.verification.mutations import oracle_actions

from .conftest import by_family


class FakeModel:
    """An OpenAI-compatible endpoint that replays a fixed list of tool calls."""

    def __init__(self, actions: list[tuple[str, dict[str, Any]]], bad_first: bool = False) -> None:
        self.actions = list(actions)
        self.requests: list[dict[str, Any]] = []
        self.bad_first = bad_first

    def respond(self, body: dict[str, Any]) -> dict[str, Any]:
        self.requests.append(body)
        n = len(self.requests) - 1
        if self.bad_first and n == 0:
            call = {
                "id": "c0",
                "type": "function",
                "function": {"name": "get_invoice", "arguments": "{not json"},
            }
            return {"choices": [{"message": {"content": "", "tool_calls": [call]}}]}
        index = n - 1 if self.bad_first else n
        if index >= len(self.actions):
            return {"choices": [{"message": {"content": "done"}}]}
        tool, args = self.actions[index]
        if tool == "set_disposition":
            # read the latest case version from the transcript, as a real agent would
            versions = [
                json.loads(m["content"]).get("result", {})
                for m in body["messages"]
                if m["role"] == "tool"
            ]
            args = {
                **args,
                "expected_version": next(
                    (
                        v["version"]
                        for v in reversed(versions)
                        if isinstance(v, dict) and "version" in v and "status" in v
                    ),
                    1,
                ),
            }
        call = {
            "id": f"c{n}",
            "type": "function",
            "function": {"name": tool, "arguments": json.dumps(args)},
        }
        return {
            "choices": [{"message": {"content": "", "tool_calls": [call]}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


@pytest.fixture
def fake_server() -> Iterator[tuple[str, dict[str, FakeModel]]]:
    holder: dict[str, FakeModel] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if "model" not in holder:
                self.send_response(500)
                self.end_headers()
                return
            payload = json.dumps(holder["model"].respond(body)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args: Any) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/v1", holder
    server.shutdown()
    server.server_close()


def test_model_runner_end_to_end(
    fake_server: tuple[str, dict[str, FakeModel]], tmp_path: Path
) -> None:
    url, holder = fake_server
    bundle = by_family("F06", 0)
    holder["model"] = FakeModel(oracle_actions(bundle), bad_first=True)
    cfg = ModelConfig(base_url=url, model="fake", http_retries=0)
    summary = evaluate("model", [bundle.public.task_id], tmp_path / "run", model=cfg)
    assert summary["task_mean_success"] == 1.0
    record = load_episodes(tmp_path / "run")[0]
    assert record.usage["requests"] >= len(holder["model"].actions)
    tool_msgs = [m for m in record.messages if m["role"] == "tool"]
    assert json.loads(tool_msgs[0]["content"])["error"]["code"] == "invalid_arguments"
    sent_tools = holder["model"].requests[0]["tools"]
    assert {t["function"]["name"] for t in sent_tools} >= {"submit_case", "propose_payment"}


def test_endpoint_failure_is_unscorable(
    fake_server: tuple[str, dict[str, FakeModel]], tmp_path: Path
) -> None:
    url, _ = fake_server  # no model registered: the server answers 500
    cfg = ModelConfig(base_url=url, model="fake", http_retries=0)
    with pytest.raises(InfrastructureError):
        chat(cfg, [], [])
    bundle = by_family("F01", 0)
    summary = evaluate("model", [bundle.public.task_id], tmp_path / "run", model=cfg)
    assert summary["unscorable_attempts"] == 1 and summary["scored_attempts"] == 0


def test_play_script_then_grade(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bundle = by_family("F02", 1)
    lines = []
    for tool, args in oracle_actions(bundle):
        if tool == "set_disposition":
            args = {**args, "expected_version": 1}
        lines.append(f"{tool} {json.dumps(args)}")
    script = tmp_path / "moves.txt"
    script.write_text("help\nget_receipts po_id=NOPE\n" + "\n".join(lines) + "\n")
    runs = tmp_path / "runs"
    assert (
        main(
            [
                "--runs",
                str(runs),
                "play",
                "--task",
                bundle.public.task_id,
                "--script",
                str(script),
                "--run-id",
                "p1",
            ]
        )
        == 0
    )
    assert main(["--runs", str(runs), "grade", "p1"]) == 0
    out = capsys.readouterr().out
    assert "PASS" in out and "not_found" in out


def test_review_sample_is_one_per_family() -> None:
    standard = review_sample("standard")
    assert len(standard) == 12 and len(set(standard)) == 12
    assert len(review_sample("minimum")) == 6
    assert review_sample("standard") == standard


def test_build_tasks_check_passes() -> None:
    assert main(["build-tasks", "--check"]) == 0
