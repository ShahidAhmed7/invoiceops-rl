"""FastAPI app for the OpenEnv server: ``uvicorn invoiceops.adapters.openenv_app:app``."""

from __future__ import annotations

import os

from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation

from invoiceops.adapters.openenv_env import (
    InvoiceOpsEnvironment,
    InvoiceOpsResetObservation,
    InvoiceOpsState,
)

app = create_app(
    InvoiceOpsEnvironment,
    CallToolAction,
    CallToolObservation,
    env_name="invoiceops",
    max_concurrent_envs=int(os.environ.get("MAX_CONCURRENT_ENVS", "8")),
    state_cls=InvoiceOpsState,
    reset_observation_cls=InvoiceOpsResetObservation,
)


def main() -> None:
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
