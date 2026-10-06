import pytest
from pydantic import ValidationError

from app.core.config import load_application_config, load_yaml
from app.core.config_models import NicheConfig, PoliciesConfig


def test_real_estate_config_loads():
    config = load_application_config("real_estate")

    assert config.niche.niche.name == "real_estate"
    assert config.niche.niche.display_name == "Real Estate"


def test_real_estate_weights_sum_to_one():
    config = load_application_config("real_estate")

    weights = config.niche.qualification.weights

    assert sum(weights.values()) == pytest.approx(1.0)


def test_policies_config_loads():
    raw_config = load_yaml("policies.yaml")
    config = PoliciesConfig.model_validate(raw_config)

    assert config.agent.dry_run is True
    assert config.agent.require_human_approval is True
    assert config.outreach.max_followups == 2


def test_invalid_followup_count_is_rejected():
    raw_config = load_yaml("policies.yaml")
    raw_config["outreach"]["max_followups"] = -1

    with pytest.raises(ValidationError):
        PoliciesConfig.model_validate(raw_config)


def test_invalid_niche_weights_are_rejected():
    raw_config = load_yaml("niches/real_estate.yaml")
    raw_config["qualification"]["weights"]["business_fit"] = 0.50

    with pytest.raises(ValidationError):
        NicheConfig.model_validate(raw_config)

@pytest.mark.parametrize(
    "niche",
    ["real_estate", "gym", "restaurant"],
)
def test_all_niches_load(niche):
    config = load_application_config(niche)

    assert config.niche.niche.name == niche
    assert config.niche.qualification.minimum_score == 7
    assert sum(config.niche.qualification.weights.values()) == pytest.approx(1.0)
