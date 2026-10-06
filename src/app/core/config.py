from pathlib import Path

import yaml

from app.core.config_models import (
    ApplicationConfig,
    AppSettings,
    LLMConfig,
    NicheConfig,
    OutreachConfig,
    PoliciesConfig,
    RetrievalConfig,
)

BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_DIR = BASE_DIR / "config"


def load_yaml(filename: str) -> dict:
    config_path = CONFIG_DIR / filename

    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_application_config(niche: str) -> ApplicationConfig:
    app_config = load_yaml("app.yaml")
    llm_config = load_yaml("llm.yaml")
    policies_config = load_yaml("policies.yaml")
    retrieval_config = load_yaml("retrieval.yaml")
    outreach_config = load_yaml("outreach.yaml")
    niche_config = load_yaml(f"niches/{niche}.yaml")

    return ApplicationConfig(
        app=AppSettings.model_validate(app_config["app"]),
        llm=LLMConfig.model_validate(llm_config),
        policies=PoliciesConfig.model_validate(policies_config),
        retrieval=RetrievalConfig.model_validate(retrieval_config),
        outreach=OutreachConfig.model_validate(outreach_config),
        niche=NicheConfig.model_validate(niche_config),
    )
