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

    def fake_research_page(url, **kwargs):
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


def test_research_site_does_not_fetch_duplicate_urls():
    researcher = WebsiteResearcher()

    homepage = {
        "url": "https://example.com/",
        "title": "Example",
        "text": "Homepage content.",
        "links": [
            "https://example.com/about",
            "https://example.com/about",
            "https://example.com/about#team",
        ],
    }

    about_page = {
        "url": "https://example.com/about",
        "title": "About",
        "text": "About content.",
        "links": [],
    }

    def fake_research_page(url, **kwargs):
        if url == "https://example.com/":
            return homepage
        return about_page

    with patch.object(
        researcher,
        "_research_page",
        side_effect=fake_research_page,
    ) as mock_research:
        result = researcher.research_site("https://example.com/")

    assert len(result["pages"]) == 2
    assert mock_research.call_count == 2


def test_research_site_continues_when_subpage_fails():
    researcher = WebsiteResearcher()

    homepage = {
        "url": "https://example.com/",
        "title": "Example",
        "text": "Homepage content.",
        "links": [
            "https://example.com/about",
            "https://example.com/services",
        ],
    }

    services_page = {
        "url": "https://example.com/services",
        "title": "Services",
        "text": "Property management services.",
        "links": [],
    }

    def fake_research_page(url, **kwargs):
        if url == "https://example.com/":
            return homepage
        if url == "https://example.com/about":
            raise WebsiteResearchError("Page unavailable.")
        return services_page

    with patch.object(
        researcher,
        "_research_page",
        side_effect=fake_research_page,
    ):
        result = researcher.research_site("https://example.com/")

    assert len(result["pages"]) == 2
    assert "Homepage content." in result["text"]
    assert "Property management services." in result["text"]
    assert all("about" not in page["url"] for page in result["pages"])


def test_research_site_never_fetches_more_than_max_pages():
    researcher = WebsiteResearcher()

    homepage = {
        "url": "https://example.com/",
        "title": "Example",
        "text": "Homepage content.",
        "links": [
            f"https://example.com/services/{index}"
            for index in range(1, 21)
        ],
    }

    def fake_research_page(url, **kwargs):
        if url == "https://example.com/":
            return homepage
        return {
            "url": url,
            "title": "Service",
            "text": f"Service page: {url}",
            "links": [],
        }

    with patch.object(
        researcher,
        "_research_page",
        side_effect=fake_research_page,
    ) as mock_research:
        result = researcher.research_site("https://example.com/")

    assert len(result["pages"]) == researcher.MAX_PAGES
    assert mock_research.call_count == researcher.MAX_PAGES


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "https://user:password@example.com",
        "https://example.com:0",
        "not-a-url",
    ],
)
def test_normalize_url_rejects_unsafe_or_invalid_urls(url):
    assert WebsiteResearcher._normalize_url(url) is None


def test_research_page_rejects_cross_host_redirect():
    researcher = WebsiteResearcher()

    response = MagicMock()
    response.status_code = 302
    response.headers = {"location": "https://other.com/about"}

    client = MagicMock()
    client.stream.return_value.__enter__.return_value = response

    with (
        patch("app.research.website.httpx.Client") as client_class,
        patch.object(WebsiteResearcher, "_validate_public_host"),
    ):
        client_class.return_value.__enter__.return_value = client

        with pytest.raises(
            WebsiteResearchError,
            match="Cross-host redirects are not allowed",
        ):
            researcher._research_page(
                "https://example.com/about",
                expected_host="example.com",
            )

    client.stream.assert_called_once_with(
        "GET",
        "https://example.com/about",
    )



@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "HTTPS://EXAMPLE.COM/about/",
            "https://example.com/about",
        ),
        (
            "http://example.com:80/services",
            "http://example.com/services",
        ),
        (
            "https://example.com:443/contact",
            "https://example.com/contact",
        ),
        (
            "https://example.com:8443/about/",
            "https://example.com:8443/about",
        ),
        (
            "https://example.com/",
            "https://example.com/",
        ),
        (
            "https://example.com/about#team",
            "https://example.com/about",
        ),
    ],
)
def test_normalize_url_canonicalizes_valid_urls(url, expected):
    assert WebsiteResearcher._normalize_url(url) == expected


def test_research_removes_empty_page_boilerplate():
    html = """
    <html>
        <head><title>   </title></head>
        <body>
            <nav>Navigation links</nav>
            <script>var x = 1;</script>
            <style>.banner { display: none; }</style>
            <footer>Footer links</footer>
            <p>     </p>
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

    assert result["text"] == ""
    assert result["title"] == ""


def test_research_normalizes_extracted_whitespace():
    html = """
    <html>
        <head><title>Example   Realty</title></head>
        <body>
            <h1>Real Estate</h1>
            <p>We     help
               businesses
               grow.</p>
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
    assert result["text"] == "Real Estate We help businesses grow."
