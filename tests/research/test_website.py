from unittest.mock import MagicMock, patch

import pytest

from app.research.website import WebsiteResearcher, WebsiteResearchError


def test_research_extracts_title_and_readable_text():
    html = """
    <html>
        <head><title>Example Realty</title></head>
        <body>
            <nav>Navigation</nav>
            <h1>Real Estate Services</h1>
            <p>We help people buy and sell properties.</p>
            <script>alert("ignore me")</script>
            <footer>Footer content</footer>
        </body>
    </html>
    """
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "text/html"}
    response.iter_bytes.return_value = [html.encode()]
    response.raise_for_status.return_value = None

    client = MagicMock()
    client.stream.return_value.__enter__.return_value = response

    with (
        patch("app.research.website.httpx.Client") as client_class,
        patch.object(WebsiteResearcher, "_validate_public_host"),
    ):
        client_class.return_value.__enter__.return_value = client

        result = WebsiteResearcher().research("https://example.com")

    assert result["title"] == "Example Realty"
    assert "Real Estate Services" in result["text"]
    assert "buy and sell properties" in result["text"]
    assert "Navigation" not in result["text"]
    assert "Footer content" not in result["text"]
    assert "alert" not in result["text"]


def test_research_rejects_non_http_url():
    with pytest.raises(WebsiteResearchError):
        WebsiteResearcher().research("file:///etc/passwd")


def test_research_rejects_non_html_response():
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "application/pdf"}
    response.raise_for_status.return_value = None

    client = MagicMock()
    client.stream.return_value.__enter__.return_value = response

    with (
        patch("app.research.website.httpx.Client") as client_class,
        patch.object(WebsiteResearcher, "_validate_public_host"),
    ):
        client_class.return_value.__enter__.return_value = client

        with pytest.raises(WebsiteResearchError, match="did not return HTML"):
            WebsiteResearcher().research("https://example.com")


def test_research_site_collects_relevant_same_host_pages():
    researcher = WebsiteResearcher()

    homepage = {
        "url": "https://example.com/",
        "title": "Example Realty",
        "text": "We help people find properties.",
        "links": [
            "https://example.com/about",
            "https://example.com/services",
            "https://example.com/contact",
            "https://example.com/products",
            "https://example.com/careers",
            "https://other.com/services",
        ],
    }

    page_results = {
        "https://example.com/about": {
            "url": "https://example.com/about",
            "title": "About Us",
            "text": "We are a real estate company.",
            "links": [],
        },
        "https://example.com/services": {
            "url": "https://example.com/services",
            "title": "Our Services",
            "text": "We provide property management.",
            "links": [],
        },
        "https://example.com/contact": {
            "url": "https://example.com/contact",
            "title": "Contact",
            "text": "Contact our team.",
            "links": [],
        },
        "https://example.com/products": {
            "url": "https://example.com/products",
            "title": "Our Products",
            "text": "Property listings.",
            "links": [],
        },
    }

    def fake_research_page(url):
        if url == "https://example.com/":
            return homepage
        return page_results[url]

    from unittest.mock import patch

    with patch.object(
        researcher,
        "_research_page",
        side_effect=fake_research_page,
    ):
        result = researcher.research_site("https://example.com/")

    assert len(result["pages"]) == 5
    assert "Example Realty" in result["text"]
    assert "We are a real estate company." in result["text"]
    assert "We provide property management." in result["text"]
    assert all(
        page["url"].startswith("https://example.com/")
        for page in result["pages"]
    )
