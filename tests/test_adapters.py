from __future__ import annotations

import inspect
import json
import warnings
from typing import Any

import pytest

from invoiceops.adapters.tool_methods import TOOL_METHOD_NAMES, ToolMethods
from invoiceops.adapters.trl_env import InvoiceOpsToolEnv
from invoiceops.tools.spec import TOOLS, TOOLS_BY_NAME
from invoiceops.verification.mutations import oracle_actions, replay
from invoiceops.verification.verifier import verify_episode

from .conftest import by_family

CASES = [("F06", 1), ("F08", 1), ("F11", 0), ("F04", 0)]


def test_tool_methods_cover_every_tool() -> None:
    assert sorted(TOOL_METHOD_NAMES) == sorted(t.name for t in TOOLS)


def test_trl_sees_exactly_the_tools() -> None:
    # Mirrors TRL 1.16's discovery: public functions on the class, minus reset/get_reward.
    names = [
        n
        for n, _ in inspect.getmembers(InvoiceOpsToolEnv, predicate=inspect.isfunction)
        if not n.startswith("_") and n not in ("reset", "get_reward")
    ]
    assert sorted(names) == sorted(TOOLS_BY_NAME)


def test_docstring_schemas_match_tool_specs() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from transformers.utils.chat_template_utils import get_json_schema
    env = InvoiceOpsToolEnv()
    for name in TOOL_METHOD_NAMES:
        generated = get_json_schema(getattr(env, name))["function"]["parameters"]
        spec_model = TOOLS_BY_NAME[name].args
        assert set(generated.get("properties", {})) == set(spec_model.model_fields), name
        required = {k for k, f in spec_model.model_fields.items() if f.is_required()}
        assert set(generated.get("required", [])) == required, name


@pytest.mark.parametrize(("family", "variant"), CASES)
def test_trl_adapter_matches_direct_episode(family: str, variant: int) -> None:
    bundle = by_family(family, variant)
    actions = oracle_actions(bundle)
    direct = replay(bundle, actions)
    env = InvoiceOpsToolEnv()
    env.reset(task_id=bundle.public.task_id, prompt=[{"role": "user", "content": "x"}])
    for tool, args in actions:
        if tool == "set_disposition":
            case = env._episode.store.work_rows("cases")[0]  # type: ignore[union-attr]
            args = {**args, "expected_version": case["version"]}
        json.loads(getattr(env, tool)(**args))
    assert env._episode is not None
    assert env._episode.store.state_hash() == direct.store.state_hash()
    assert env.get_reward() == verify_episode(direct, bundle.private).reward == 1.0


@pytest.mark.parametrize(("family", "variant"), CASES)
def test_openenv_adapter_matches_direct_episode(
    family: str, variant: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("openenv")
    from fastapi.testclient import TestClient

    monkeypatch.setenv("INVOICEOPS_PRIVATE_ROOT", "tasks")
    from invoiceops.adapters.openenv_app import app

    bundle = by_family(family, variant)
    actions = oracle_actions(bundle)
    final: dict[str, Any] = {}
    with TestClient(app).websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "reset", "data": {"task_id": bundle.public.task_id}}))
        reset = json.loads(ws.receive_text())["data"]
        assert reset["observation"]["prompt"] == bundle.public.prompt
        version = 1
        for tool, args in actions:
            if tool == "set_disposition":
                args = {**args, "expected_version": version}
            ws.send_text(
                json.dumps(
                    {
                        "type": "step",
                        "data": {"type": "call_tool", "tool_name": tool, "arguments": args},
                    }
                )
            )
            final = json.loads(ws.receive_text())["data"]
            text = final["observation"]["result"]["content"][0]["text"]
            obs = json.loads(text)
            if tool == "set_disposition":
                version = obs["result"]["version"]
        ws.send_text(json.dumps({"type": "state"}))
        state = json.loads(ws.receive_text())["data"]
    assert final["done"] is True
    assert final["reward"] == 1.0
    assert set(state) == {"episode_id", "step_count", "task_id"}


def test_mixin_has_no_state() -> None:
    assert not [
        k for k, v in vars(ToolMethods).items() if not callable(v) and not k.startswith("__")
    ]
