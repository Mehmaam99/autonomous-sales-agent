from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_DIR = BASE_DIR / "config"


def load_yaml(filename: str) -> dict:
    config_path = CONFIG_DIR / filename

    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}