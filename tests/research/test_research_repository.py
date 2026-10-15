from unittest.mock import MagicMock

import pytest

from app.research.repository import WebsiteResearchRepository


def test_save_successful_research():
    session = MagicMock()
    repository = WebsiteResearchRepository(session)

    saved = repository.save(
        company_id=10,
        source_url="https://example.com",
        status="success",
        page_title="Example Domain",
        extracted_text="Useful company information.",
    )

    assert saved.company_id == 10
    assert saved.source_url == "https://example.com"
    assert saved.status == "success"
    assert saved.page_title == "Example Domain"
    assert saved.extracted_text == "Useful company information."
    assert saved.error_message is None
    session.add.assert_called_once_with(saved)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(saved)


def test_save_failed_research():
    session = MagicMock()
    repository = WebsiteResearchRepository(session)

    saved = repository.save(
        company_id=10,
        source_url="https://example.com",
        status="failed",
        error_message="Website request failed.",
    )

    assert saved.status == "failed"
    assert saved.error_message == "Website request failed."
    assert saved.page_title is None
    assert saved.extracted_text is None
    session.commit.assert_called_once()


def test_save_rejects_invalid_status():
    session = MagicMock()
    repository = WebsiteResearchRepository(session)

    with pytest.raises(ValueError, match="Status must be"):
        repository.save(
            company_id=10,
            source_url="https://example.com",
            status="pending",
        )

    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_save_rolls_back_on_commit_failure():
    session = MagicMock()
    session.commit.side_effect = RuntimeError("Database failure")
    repository = WebsiteResearchRepository(session)

    with pytest.raises(RuntimeError, match="Database failure"):
        repository.save(
            company_id=10,
            source_url="https://example.com",
            status="success",
            extracted_text="Research content.",
        )

    session.rollback.assert_called_once()


def test_save_rolls_back_when_refresh_fails():
    session = MagicMock()
    session.refresh.side_effect = RuntimeError("Refresh failure")
    repository = WebsiteResearchRepository(session)

    with pytest.raises(RuntimeError, match="Refresh failure"):
        repository.save(
            company_id=10,
            source_url="https://example.com",
            status="success",
            extracted_text="Research content.",
        )

    session.commit.assert_called_once()
    session.rollback.assert_called_once()


def test_save_preserves_commit_error_when_rollback_fails():
    session = MagicMock()
    session.commit.side_effect = RuntimeError("Database failure")
    session.rollback.side_effect = RuntimeError("Rollback failure")
    repository = WebsiteResearchRepository(session)

    with pytest.raises(RuntimeError, match="Database failure"):
        repository.save(
            company_id=10,
            source_url="https://example.com",
            status="success",
            extracted_text="Research content.",
        )

    session.rollback.assert_called_once()
