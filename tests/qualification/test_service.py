import json

import pytest

from app.core.config import load_application_config
from app.qualification.schemas import LeadQualification
from app.qualification.service import LeadQualificationService


def test_qualification_returns_validated_result(monkeypatch):
    config = load_application_config("real_estate")
    minimum_score = config.niche.qualification.minimum_score

    fake_response = json.dumps(
        {
            "score": minimum_score,
            "reasons": ["Business matches the target customer profile."],
            "evidence": ["The supplied data identifies a real-estate agency."],
            "qualified": True,
        }
    )

    class FakeGateway:
        def __init__(self, niche):
            self.niche = niche

        def generate(self, prompt, system_prompt=None):
            assert "LEAD INFORMATION" in prompt
            assert system_prompt
            return fake_response

    monkeypatch.setattr(
        "app.qualification.service.LLMGateway",
        FakeGateway,
    )

    service = LeadQualificationService("real_estate")
    result = service.qualify(
        {
            "business_name": "Example Realty",
            "business_type": "Real-estate agency",
        }
    )

    assert isinstance(result, LeadQualification)
    assert result.score == minimum_score
    assert result.qualified is True
    assert result.evidence


def test_qualification_rejects_empty_lead_data(monkeypatch):
    class FakeGateway:
        def __init__(self, niche):
            pass

    monkeypatch.setattr(
        "app.qualification.service.LLMGateway",
        FakeGateway,
    )

    service = LeadQualificationService("real_estate")

    with pytest.raises(ValueError, match="Lead data must not be empty"):
        service.qualify({})


def test_schema_rejects_score_outside_range():
    with pytest.raises(ValueError):
        LeadQualification(
            score=11,
            reasons=["Good fit"],
            evidence=["Relevant business information"],
            qualified=True,
        )


def test_schema_rejects_empty_evidence():
    with pytest.raises(ValueError, match="At least one non-empty item"):
        LeadQualification(
            score=8,
            reasons=["Good fit"],
            evidence=[" ", ""],
            qualified=True,
        )


def test_service_rejects_decision_below_configured_threshold(monkeypatch):
    fake_response = json.dumps(
        {
            "score": 4,
            "reasons": ["Insufficient fit evidence."],
            "evidence": ["Business type was supplied."],
            "qualified": True,
        }
    )

    class FakeGateway:
        def __init__(self, niche):
            pass

        def generate(self, prompt, system_prompt=None):
            return fake_response

    monkeypatch.setattr(
        "app.qualification.service.LLMGateway",
        FakeGateway,
    )

    service = LeadQualificationService("real_estate")

    with pytest.raises(ValueError, match="configured minimum score"):
        service.qualify({"business_type": "Real-estate agency"})
