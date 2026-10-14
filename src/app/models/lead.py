from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.company import Company


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        index=True,
    )

    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="new",
        index=True,
    )

    qualification_score: Mapped[int | None] = mapped_column(nullable=True)
    qualification_reasons: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    qualification_evidence: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    is_qualified: Mapped[bool | None] = mapped_column(nullable=True)
    qualified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    company: Mapped["Company"] = relationship(back_populates="leads")
