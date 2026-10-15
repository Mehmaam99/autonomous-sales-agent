from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.qualification.repository import LeadQualificationRepository
from app.qualification.schemas import LeadQualification
from app.qualification.service import LeadQualificationService
from app.research.repository import WebsiteResearchRepository
from app.research.website import WebsiteResearcher, WebsiteResearchError


class LeadQualificationWorkflow:
    """Research, qualify, and persist an existing lead."""

    def __init__(self, session: Session, niche: str) -> None:
        self.session = session
        self.qualification_service = LeadQualificationService(niche)
        self.repository = LeadQualificationRepository(session)
        self.website_researcher = WebsiteResearcher()
        self.research_repository = WebsiteResearchRepository(session)

    def run(self, lead_id: int) -> LeadQualification:
        """Research a lead's company, qualify it, and save the result."""
        lead = self.session.get(Lead, lead_id)

        if lead is None:
            raise ValueError(f"Lead with ID {lead_id} was not found.")

        company = lead.company

        lead_data = {
            "lead_name": lead.full_name,
            "email": lead.email or "",
            "company_name": company.name,
            "website": company.website or "",
            "industry": company.industry or "",
            "location": company.location or "",
            "website_title": "",
            "website_text": "",
        }

        if company.website:
            try:
                research = self.website_researcher.research_site(
                    company.website
                )
            except WebsiteResearchError as exc:
                self.research_repository.save(
                    company_id=company.id,
                    source_url=company.website,
                    status="failed",
                    error_message=str(exc)[:2000],
                )
                lead_data["website_text"] = (
                    "Website research failed. Do not infer company facts "
                    "from the URL alone."
                )
            else:
                research_text = research["text"]

                if not research_text.strip():
                    self.research_repository.save(
                        company_id=company.id,
                        source_url=research["url"],
                        status="failed",
                        error_message=(
                            "Website research returned no useful text."
                        ),
                    )
                    lead_data["website_text"] = (
                        "Website research failed. Do not infer company facts "
                        "from the URL alone."
                    )
                else:
                    self.research_repository.save(
                        company_id=company.id,
                        source_url=research["url"],
                        status="success",
                        page_title=research["title"],
                        extracted_text=research_text,
                    )
                    lead_data["website"] = research["url"]
                    lead_data["website_title"] = research["title"]
                    lead_data["website_text"] = research_text

        result = self.qualification_service.qualify(lead_data)
        self.repository.save(lead_id, result)

        return result
