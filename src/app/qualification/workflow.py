from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.qualification.repository import LeadQualificationRepository
from app.qualification.schemas import LeadQualification
from app.qualification.service import LeadQualificationService
from app.research.website import WebsiteResearcher, WebsiteResearchError


class LeadQualificationWorkflow:
    """Research, qualify, and persist an existing lead."""

    def __init__(self, session: Session, niche: str) -> None:
        self.session = session
        self.qualification_service = LeadQualificationService(niche)
        self.repository = LeadQualificationRepository(session)
        self.website_researcher = WebsiteResearcher()

    def run(self, lead_id: int) -> LeadQualification:
        """Qualify a lead using available company and website information."""
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
                research = self.website_researcher.research(company.website)
                lead_data["website_title"] = research["title"]
                lead_data["website_text"] = research["text"]
            except WebsiteResearchError:
                lead_data["website_text"] = (
                    "Website research was unavailable. "
                    "Do not infer company facts from the URL alone."
                )

        result = self.qualification_service.qualify(lead_data)
        self.repository.save(lead_id, result)

        return result
