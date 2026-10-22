"""Pinned models, benchmark versions, and serving settings: the single source for Modal jobs.

Model revisions are recorded by ``inspect_models`` in Phase 11A and must be filled in here
before any evaluation job, so every result names the exact weights used.
"""

from __future__ import annotations

CANDIDATE_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
CANDIDATE_FALLBACK = "Qwen/Qwen3.5-4B"
REFERENCE_MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"
REFERENCE_FP8 = "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8"
REFERENCE_FALLBACK = "Qwen/Qwen3-8B"

# Filled in from reports/model_verification.json after Phase 11A step 3. ``None`` means
# "not yet verified": evaluation jobs refuse to run with an unpinned revision.
REVISIONS: dict[str, str | None] = {
    CANDIDATE_MODEL: None,
    CANDIDATE_FALLBACK: None,
    REFERENCE_MODEL: None,
    REFERENCE_FP8: None,
    REFERENCE_FALLBACK: None,
}

TAU2_REPO = "https://github.com/sierra-research/tau2-bench"
TAU2_COMMIT = "318fa35b1431a42e3ffdad05197378f506fac9d4"
TAU2_DOMAIN = "retail"
TAU2_SPLIT = "test"
TAU2_TRIALS = 4
TAU2_SEED = 300
BFCL_VERSION = "2026.3.23"
BFCL_CATEGORIES = (
    "simple_python",
    "multiple",
    "parallel",
    "parallel_multiple",
    "irrelevance",
    "live_simple",
    "live_multiple",
    "multi_turn_base",
)

# Decoding for every agent evaluation (BUILD_PLAN.md section 3.3). Not tuned on test data.
AGENT_TEMPERATURE = 0.7
AGENT_TOP_P = 0.8
USER_SIM_TEMPERATURE = 0.0
MAX_MODEL_LEN = 16384
# Qwen3 instruct models emit Hermes-style tool calls; Phase 11A smoke_serve confirms parsing.
TOOL_CALL_PARSER = "hermes"
