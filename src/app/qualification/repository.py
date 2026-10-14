from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.qualification.schemas import LeadQualification


class LeadQualificationRepository:
    """Persist qualification results for existing leads."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        lead_id: int,
        result: LeadQualification,
    ) -> Lead:
        """Save a validated qualification result to an existing lead."""
        lead = self.session.get(Lead, lead_id)

        if lead is None:
            raise ValueError(f"Lead with ID {lead_id} was not found.")

        lead.qualification_score = result.score
        lead.qualification_reasons = result.reasons
        lead.qualification_evidence = result.evidence
        lead.is_qualified = result.qualified
        lead.qualified_at = datetime.now(UTC)

        try:
            self.session.commit()
            self.session.refresh(lead)
        except Exception:
            self.session.rollback()
            raise

        return lead
