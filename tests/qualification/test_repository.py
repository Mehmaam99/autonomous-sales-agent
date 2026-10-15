from unittest.mock import MagicMock

import pytest

from app.models.lead import Lead
from app.qualification.repository import LeadQualificationRepository
from app.qualification.schemas import LeadQualification


@pytest.fixture
def qualification_result():
    return LeadQualification(
        score=8,
        reasons=["Matches the target customer profile."],
        evidence=["Business type matches the supplied criteria."],
        qualified=True,
    )


def test_save_updates_existing_lead(qualification_result):
    session = MagicMock()
    lead = Lead(id=1, company_id=1, full_name="Test Lead")
    session.get.return_value = lead

    repository = LeadQualificationRepository(session)
    saved = repository.save(1, qualification_result)

    assert saved.qualification_score == 8
    assert saved.qualification_reasons == [
        "Matches the target customer profile."
    ]
    assert saved.qualification_evidence == [
        "Business type matches the supplied criteria."
    ]
    assert saved.is_qualified is True
    assert saved.qualified_at is not None
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(lead)


def test_save_raises_when_lead_does_not_exist(qualification_result):
    session = MagicMock()
    session.get.return_value = None

    repository = LeadQualificationRepository(session)

    with pytest.raises(ValueError, match="Lead with ID 999 was not found"):
        repository.save(999, qualification_result)

    session.commit.assert_not_called()


def test_save_rolls_back_on_commit_failure(qualification_result):
    session = MagicMock()
    lead = Lead(id=1, company_id=1, full_name="Test Lead")
    session.get.return_value = lead
    session.commit.side_effect = RuntimeError("Database failure")

    repository = LeadQualificationRepository(session)

    with pytest.raises(RuntimeError, match="Database failure"):
        repository.save(1, qualification_result)

    session.rollback.assert_called_once()

def test_save_rolls_back_when_refresh_fails(qualification_result):
    session = MagicMock()
    lead = Lead(id=1, company_id=1, full_name="Test Lead")
    session.get.return_value = lead
    session.refresh.side_effect = RuntimeError("Refresh failure")

    repository = LeadQualificationRepository(session)

    with pytest.raises(RuntimeError, match="Refresh failure"):
        repository.save(1, qualification_result)

    session.commit.assert_called_once()
    session.rollback.assert_called_once()


def test_save_preserves_commit_error_when_rollback_fails(
    qualification_result,
):
    session = MagicMock()
    lead = Lead(id=1, company_id=1, full_name="Test Lead")
    session.get.return_value = lead
    session.commit.side_effect = RuntimeError("Database failure")
    session.rollback.side_effect = RuntimeError("Rollback failure")

    repository = LeadQualificationRepository(session)

    with pytest.raises(RuntimeError, match="Database failure"):
        repository.save(1, qualification_result)

    session.rollback.assert_called_once()
