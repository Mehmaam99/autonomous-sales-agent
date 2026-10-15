from unittest.mock import MagicMock

import pytest

from app.models.lead import Lead
from app.qualification.schemas import LeadQualification
from app.qualification.workflow import LeadQualificationWorkflow


def test_workflow_qualifies_and_saves_existing_lead():
    company = MagicMock()
    company.id = 10
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
    workflow.website_researcher = MagicMock()
    workflow.website_researcher.research_site.return_value = {
        "url": "https://example.com",
        "title": "Example Domain",
        "text": "Example website content.",
    }
    workflow.research_repository = MagicMock()

    returned = workflow.run(1)

    assert returned == result

    qualification_data = (
        workflow.qualification_service.qualify.call_args.args[0]
    )
    assert qualification_data["website_title"] == "Example Domain"
    assert qualification_data["website_text"] == "Example website content."

    workflow.research_repository.save.assert_called_once_with(
        company_id=10,
        source_url="https://example.com",
        status="success",
        page_title="Example Domain",
        extracted_text="Example website content.",
    )
    workflow.repository.save.assert_called_once_with(1, result)


def test_workflow_raises_for_missing_lead():
    session = MagicMock()
    session.get.return_value = None

    workflow = LeadQualificationWorkflow.__new__(
        LeadQualificationWorkflow
    )
    workflow.session = session

    with pytest.raises(ValueError, match="Lead with ID 999 was not found"):
        workflow.run(999)

def test_workflow_records_failed_website_research():
    company = MagicMock()
    company.id = 10
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
        score=2,
        reasons=["Insufficient evidence."],
        evidence=["Website research failed."],
        qualified=False,
    )

    workflow = LeadQualificationWorkflow.__new__(
        LeadQualificationWorkflow
    )
    workflow.session = session
    workflow.qualification_service = MagicMock()
    workflow.qualification_service.qualify.return_value = result
    workflow.repository = MagicMock()

    from app.research.website import WebsiteResearchError

    workflow.website_researcher = MagicMock()
    workflow.website_researcher.research_site.side_effect = (
        WebsiteResearchError("Website request failed.")
    )
    workflow.research_repository = MagicMock()

    returned = workflow.run(1)

    assert returned == result

    workflow.research_repository.save.assert_called_once_with(
        company_id=10,
        source_url="https://example.com",
        status="failed",
        error_message="Website request failed.",
    )

    qualification_data = (
        workflow.qualification_service.qualify.call_args.args[0]
    )
    assert "Website research failed" in qualification_data["website_text"]

