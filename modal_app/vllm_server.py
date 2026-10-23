"""Start a vLLM OpenAI-compatible server as a subprocess and wait until it is healthy."""

from __future__ import annotations

import subprocess
import time
import urllib.request
from collections.abc import Sequence

from modal_app import settings


def start(
    model: str,
    port: int,
    served_name: str,
    gpu_memory_utilization: float,
    revision: str | None = None,
    lora_path: str | None = None,
    extra: Sequence[str] = (),
    startup_timeout_s: int = 900,
    max_model_len: int = settings.MAX_MODEL_LEN,
) -> subprocess.Popen[bytes]:
    cmd = [
        "vllm",
        "serve",
        model,
        "--port",
        str(port),
        "--served-model-name",
        served_name,
        "--max-model-len",
        str(max_model_len),
        "--gpu-memory-utilization",
        str(gpu_memory_utilization),
        "--enable-auto-tool-choice",
        "--tool-call-parser",
        settings.TOOL_CALL_PARSER,
        "--download-dir",
        "/hf-cache",
    ]
    if revision:
        cmd += ["--revision", revision]
    if lora_path:
        cmd += [
            "--enable-lora",
            "--max-lora-rank",
            "64",
            "--lora-modules",
            f"{served_name}-lora={lora_path}",
        ]
    cmd += list(extra)
    print("starting:", " ".join(cmd), flush=True)
    process = subprocess.Popen(cmd)
    deadline = time.monotonic() + startup_timeout_s
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"vLLM exited with code {process.returncode} while starting {model}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
                if response.status == 200:
                    return process
        except OSError:
            pass
        time.sleep(5)
    process.kill()
    raise RuntimeError(f"vLLM did not become healthy within {startup_timeout_s}s for {model}")


def stop(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
