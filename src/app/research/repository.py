import logging

from sqlalchemy.orm import Session

from app.models.website_research import WebsiteResearch

logger = logging.getLogger(__name__)


class WebsiteResearchRepository:
    """Persist website research attempts."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        *,
        company_id: int,
        source_url: str,
        status: str,
        page_title: str | None = None,
        extracted_text: str | None = None,
        error_message: str | None = None,
    ) -> WebsiteResearch:
        """Save a successful or failed website research attempt."""
        if status not in {"success", "failed"}:
            raise ValueError("Status must be 'success' or 'failed'.")

        record = WebsiteResearch(
            company_id=company_id,
            source_url=source_url,
            status=status,
            page_title=page_title,
            extracted_text=extracted_text,
            error_message=error_message,
        )

        self.session.add(record)

        try:
            self.session.commit()
            self.session.refresh(record)
        except Exception:
            try:
                self.session.rollback()
            except Exception:
                logger.exception("Rollback failed while saving website research.")
            raise

        return record
