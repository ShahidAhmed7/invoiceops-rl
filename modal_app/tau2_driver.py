"""Run tau2-bench (retail, test split) against local vLLM servers, graded on database state only.

Executed with the tau2 virtual environment's Python inside the Modal container:

    /opt/tau2/bin/python tau2_driver.py --agent-model candidate --agent-port 8001 \
        --user-model user-sim --user-port 8002 --trials 4 --out /runs/tau2/before

Uses tau2's ``run_tasks`` with ``EvaluationType.ENV`` (database checks and environment
assertions, no LLM judge). Both the agent and the simulated customer are local open models,
so no external API is called. Results are not comparable with the public leaderboard.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from pathlib import Path


def validate_summary(summary: dict) -> None:
    """Reject missing rewards or partial trial coverage instead of reporting a biased score."""
    expected = summary["tasks"] * summary["trials"]
    if (
        not expected
        or summary["simulations"] != expected
        or summary["simulations_without_reward"]
        or summary["complete_tasks"] != summary["tasks"]
        or summary["unexpected_task_ids"]
        or len(summary["per_task_mean_reward"]) != summary["tasks"]
        or any(
            not math.isfinite(x) or not 0 <= x <= 1
            for x in summary["per_task_mean_reward"].values()
        )
    ):
        raise ValueError("tau2 evaluation requires every scheduled task and trial to be scored")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-model", required=True)
    parser.add_argument("--agent-port", type=int, required=True)
    parser.add_argument("--user-model", required=True)
    parser.add_argument("--user-port", type=int, required=True)
    parser.add_argument("--trials", type=int, default=4)
    parser.add_argument("--num-tasks", type=int, default=0, help="0 = whole split")
    parser.add_argument("--seed", type=int, default=300)
    parser.add_argument("--split", default="test")
    parser.add_argument("--domain", default="retail")
    parser.add_argument("--agent-temperature", type=float, default=0.7)
    parser.add_argument("--agent-top-p", type=float, default=0.8)
    parser.add_argument("--user-temperature", type=float, default=0.0)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # LiteLLM requires a key variable for the openai/ provider even for a local server.
    os.environ.setdefault("OPENAI_API_KEY", "EMPTY")

    from tau2.domains.retail.environment import get_tasks
    from tau2.evaluator.evaluator import EvaluationType
    from tau2.run import run_tasks

    if args.domain != "retail":
        raise SystemExit("only the retail domain is configured")
    tasks = get_tasks(args.split)
    if args.num_tasks:
        tasks = tasks[: args.num_tasks]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = run_tasks(
        domain=args.domain,
        tasks=tasks,
        agent="llm_agent",
        user="user_simulator",
        llm_agent=f"openai/{args.agent_model}",
        llm_args_agent={
            "api_base": f"http://127.0.0.1:{args.agent_port}/v1",
            "api_key": "EMPTY",
            "temperature": args.agent_temperature,
            "top_p": args.agent_top_p,
        },
        llm_user=f"openai/{args.user_model}",
        llm_args_user={
            "api_base": f"http://127.0.0.1:{args.user_port}/v1",
            "api_key": "EMPTY",
            "temperature": args.user_temperature,
        },
        num_trials=args.trials,
        evaluation_type=EvaluationType.ENV,
        max_concurrency=args.concurrency,
        seed=args.seed,
        save_to=str(out / "results.json"),
        console_display=False,
        auto_review=False,
    )

    per_task: dict[str, list[float]] = defaultdict(list)
    errors = 0
    for sim in results.simulations:
        if sim.reward_info is None:
            errors += 1
            continue
        per_task[str(sim.task_id)].append(float(sim.reward_info.reward))
    k = args.trials
    complete = {t: r for t, r in per_task.items() if len(r) == k}
    summary = {
        "domain": args.domain,
        "split": args.split,
        "tasks": len(tasks),
        "trials": k,
        "evaluation_type": "ENV (database state and environment assertions only)",
        "agent_model": args.agent_model,
        "user_model": args.user_model,
        "agent_temperature": args.agent_temperature,
        "user_temperature": args.user_temperature,
        "seed": args.seed,
        "simulations": len(results.simulations),
        "simulations_without_reward": errors,
        "complete_tasks": len(complete),
        "unexpected_task_ids": sorted(set(per_task) - {str(t.id) for t in tasks}),
        "pass_1": sum(sum(r) / len(r) for r in per_task.values()) / len(per_task)
        if per_task
        else None,
        f"pass^{k}": (sum(all(x >= 1.0 for x in r) for r in complete.values()) / len(complete))
        if complete
        else None,
        "per_task_mean_reward": {t: sum(r) / len(r) for t, r in sorted(per_task.items())},
        "comparable_with_public_leaderboard": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    validate_summary(summary)
    print(
        json.dumps({k_: v for k_, v in summary.items() if k_ != "per_task_mean_reward"}, indent=2)
    )


if __name__ == "__main__":
    main()
