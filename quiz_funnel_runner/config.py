from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RunnerConfig(BaseModel):
    urls: list[str] = Field(default_factory=list, min_length=1, max_length=5)
    max_steps: int = Field(default=20, ge=1, le=100)
    headless: bool = False
    concurrency: int = Field(default=3, ge=1, le=5)
    output_dir: Path = Path("results")
    llm_enabled: bool = False
    device: Literal["iPhone 13", "iPhone 12", "iPhone SE"] = "iPhone 13"

    @field_validator("urls")
    @classmethod
    def ensure_unique_urls(cls, urls: list[str]) -> list[str]:
        dedup = list(dict.fromkeys(urls))
        if len(dedup) != len(urls):
            return dedup
        return urls


def load_config(config_path: str | None, urls: list[str] | None = None, **overrides) -> RunnerConfig:
    raw: dict = {}
    if config_path:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    if urls:
        raw["urls"] = urls
    raw.update({k: v for k, v in overrides.items() if v is not None})
    return RunnerConfig(**raw)
