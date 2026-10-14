from unittest.mock import MagicMock

import pytest

from app.models.lead import Lead
from app.qualification.schemas import LeadQualification
from app.qualification.workflow import LeadQualificationWorkflow


def test_workflow_qualifies_and_saves_existing_lead(monkeypatch):
    company = MagicMock()
    company.name = "Example Realty"
    company.website = "https://example.com"
    company.industry = "real_estate"
    company.location = "Karachi"

    lead = MagicMock(spec=Lead)
    lead.full_name = "Test Lead"
    lead.email = "lead@example.com"
    lead.company = company

    session = MagicMock()
    session.get.return_value = lead

    result = LeadQualification(
        score=8,
        reasons=["Matches target profile."],
        evidence=["Company industry was supplied."],
        qualified=True,
    )

    workflow = LeadQualificationWorkflow.__new__(
        LeadQualificationWorkflow
    )
    workflow.session = session
    workflow.qualification_service = MagicMock()
    workflow.qualification_service.qualify.return_value = result
    workflow.repository = MagicMock()

    returned = workflow.run(1)

    workflow.qualification_service.qualify.assert_called_once_with(
        {
            "lead_name": "Test Lead",
            "email": "lead@example.com",
            "company_name": "Example Realty",
            "website": "https://example.com",
            "industry": "real_estate",
            "location": "Karachi",
        }
    )
    workflow.repository.save.assert_called_once_with(1, result)
    assert returned == result


def test_workflow_rejects_missing_lead():
    session = MagicMock()
    session.get.return_value = None

    workflow = LeadQualificationWorkflow.__new__(
        LeadQualificationWorkflow
    )
    workflow.session = session

    with pytest.raises(ValueError, match="Lead with ID 999 was not found"):
        workflow.run(999)
