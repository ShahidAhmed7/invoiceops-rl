"""Versioned system prompts. Never edit a released version; add a new one."""

from __future__ import annotations

from importlib import resources

VERSIONS = ("v1", "v2")


def system_prompt(version: str) -> str:
    if version not in VERSIONS:
        raise ValueError(f"unknown prompt version {version}")
    return resources.files(__name__).joinpath(f"system_{version}.md").read_text()
