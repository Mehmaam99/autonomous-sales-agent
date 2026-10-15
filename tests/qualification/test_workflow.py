from unittest.mock import MagicMock

import pytest

from app.models.lead import Lead
from app.qualification.schemas import LeadQualification
from app.qualification.workflow import LeadQualificationWorkflow
from app.research.website import WebsiteResearchError


def build_workflow(lead, result=None):
    session = MagicMock()
    session.get.return_value = lead

    workflow = LeadQualificationWorkflow.__new__(
        LeadQualificationWorkflow
    )
    workflow.session = session
    workflow.qualification_service = MagicMock()
    workflow.qualification_service.qualify.return_value = result
    workflow.repository = MagicMock()
    workflow.website_researcher = MagicMock()
    workflow.research_repository = MagicMock()

    return workflow, session


def build_lead(*, website="https://example.com", email="lead@example.com",
               industry="real_estate", location="Karachi"):
    company = MagicMock()
    company.id = 10
    company.name = "Example Realty"
    company.website = website
    company.industry = industry
    company.location = location

    lead = MagicMock(spec=Lead)
    lead.full_name = "Test Lead"
    lead.email = email
    lead.company = company

    return lead


def test_workflow_qualifies_and_saves_existing_lead():
    result = LeadQualification(
        score=8,
        reasons=["Matches target profile."],
        evidence=["Company industry was supplied."],
        qualified=True,
    )
    lead = build_lead()
    workflow, _ = build_workflow(lead, result)
    workflow.website_researcher.research_site.return_value = {
        "url": "https://example.com",
        "title": "Example Domain",
        "text": "Example website content.",
    }

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
    workflow, _ = build_workflow(None)

    with pytest.raises(ValueError, match="Lead with ID 999 was not found"):
        workflow.run(999)


def test_workflow_records_failed_website_research():
    result = LeadQualification(
        score=2,
        reasons=["Insufficient evidence."],
        evidence=["Website research failed."],
        qualified=False,
    )
    workflow, _ = build_workflow(build_lead(), result)
    workflow.website_researcher.research_site.side_effect = (
        WebsiteResearchError("Website request failed.")
    )

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


def test_workflow_records_empty_website_research_as_failed():
    result = LeadQualification(
        score=2,
        reasons=["Insufficient evidence."],
        evidence=["No useful website content was available."],
        qualified=False,
    )
    workflow, _ = build_workflow(build_lead(), result)
    workflow.website_researcher.research_site.return_value = {
        "url": "https://example.com",
        "title": "Example Domain",
        "text": "   \n  ",
    }

    returned = workflow.run(1)

    assert returned == result
    workflow.research_repository.save.assert_called_once_with(
        company_id=10,
        source_url="https://example.com",
        status="failed",
        error_message="Website research returned no useful text.",
    )
    qualification_data = (
        workflow.qualification_service.qualify.call_args.args[0]
    )
    assert qualification_data["website_title"] == ""
    assert "Website research failed" in qualification_data["website_text"]


def test_workflow_stops_when_research_persistence_fails():
    workflow, _ = build_workflow(build_lead())
    workflow.website_researcher.research_site.return_value = {
        "url": "https://example.com",
        "title": "Example Domain",
        "text": "Useful company information.",
    }
    workflow.research_repository.save.side_effect = RuntimeError(
        "Database failure"
    )

    with pytest.raises(RuntimeError, match="Database failure"):
        workflow.run(1)

    workflow.qualification_service.qualify.assert_not_called()
    workflow.repository.save.assert_not_called()


def test_workflow_skips_research_when_company_has_no_website():
    result = LeadQualification(
        score=2,
        reasons=["Insufficient evidence."],
        evidence=["No website was available."],
        qualified=False,
    )
    workflow, _ = build_workflow(build_lead(website=None), result)

    returned = workflow.run(1)

    assert returned == result
    workflow.website_researcher.research_site.assert_not_called()
    workflow.research_repository.save.assert_not_called()
    qualification_data = (
        workflow.qualification_service.qualify.call_args.args[0]
    )
    assert qualification_data["website"] == ""
    assert qualification_data["website_title"] == ""
    assert qualification_data["website_text"] == ""
    workflow.repository.save.assert_called_once_with(1, result)


def test_workflow_handles_missing_optional_lead_and_company_fields():
    result = LeadQualification(
        score=2,
        reasons=["Insufficient evidence."],
        evidence=["Optional fields were unavailable."],
        qualified=False,
    )
    lead = build_lead(
        website=None,
        email=None,
        industry=None,
        location=None,
    )
    workflow, _ = build_workflow(lead, result)

    returned = workflow.run(1)

    assert returned == result
    workflow.website_researcher.research_site.assert_not_called()
    qualification_data = (
        workflow.qualification_service.qualify.call_args.args[0]
    )
    assert qualification_data["email"] == ""
    assert qualification_data["website"] == ""
    assert qualification_data["industry"] == ""
    assert qualification_data["location"] == ""
    assert qualification_data["website_title"] == ""
    assert qualification_data["website_text"] == ""
    workflow.repository.save.assert_called_once_with(1, result)
