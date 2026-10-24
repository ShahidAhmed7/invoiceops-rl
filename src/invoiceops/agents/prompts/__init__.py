"""Versioned system prompts. Never edit a released version; add a new one."""

from __future__ import annotations

from importlib import resources

# v3a and v3b are candidates written from train/dev transcripts only (reports/prompt_trials.md).
VERSIONS = ("v1", "v2", "v3a", "v3b")


def system_prompt(version: str) -> str:
    if version not in VERSIONS:
        raise ValueError(f"unknown prompt version {version}")
    return resources.files(__name__).joinpath(f"system_{version}.md").read_text()
