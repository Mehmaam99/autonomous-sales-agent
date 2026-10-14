from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.qualification.repository import LeadQualificationRepository
from app.qualification.schemas import LeadQualification
from app.qualification.service import LeadQualificationService


class LeadQualificationWorkflow:
    """Qualify an existing lead and persist the result."""

    def __init__(self, session: Session, niche: str) -> None:
        self.session = session
        self.qualification_service = LeadQualificationService(niche)
        self.repository = LeadQualificationRepository(session)

    def run(self, lead_id: int) -> LeadQualification:
        """Load a lead, qualify its available information, and save the result."""
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
        }

        result = self.qualification_service.qualify(lead_data)
        self.repository.save(lead_id, result)

        return result
