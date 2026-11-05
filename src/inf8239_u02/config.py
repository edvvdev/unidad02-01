from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    data_source: str = os.getenv("DATA_SOURCE", "local")
    dataset_path: Path = ROOT / os.getenv("DATASET_PATH", "data/sample/demo_text.csv")
    dataset_url: str = os.getenv("DATASET_URL", "")
    text_column: str = os.getenv("TEXT_COLUMN", "text")
    target_column: str = os.getenv("TARGET_COLUMN", "label")
    random_state: int = int(os.getenv("RANDOM_STATE", "42"))


settings = Settings()
