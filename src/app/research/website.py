import ipaddress
import socket
from typing import ClassVar
from urllib.parse import urldefrag, urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup


class WebsiteResearchError(Exception):
    """Raised when website content cannot be fetched safely."""


class WebsiteResearcher:
    """Fetch and extract readable text from public company websites."""

    MAX_BYTES = 1_000_000
    MAX_REDIRECTS = 3
    TIMEOUT_SECONDS = 10.0
    MAX_PAGES = 5
    MAX_LINKS_TO_CHECK = 100
    MAX_TEXT_LENGTH = 20_000

    RELEVANT_PATHS: ClassVar[set[str]] = {
        "about",
        "about-us",
        "aboutus",
        "services",
        "service",
        "products",
        "product",
        "solutions",
        "contact",
        "contact-us",
        "company",
        "what-we-do",
    }

    def research(self, url: str) -> dict[str, str]:
        """Fetch one public HTML page and extract readable text."""
        result = self._research_page(url)
        return {
            "url": result["url"],
            "title": result["title"],
            "text": result["text"],
        }

    def research_site(self, url: str) -> dict[str, object]:
        """Research the homepage and a limited set of relevant same-host pages."""
        homepage = self._research_page(url)
        pages = [homepage]
        visited = {homepage["url"]}

        homepage_host = urlsplit(homepage["url"]).hostname
        candidates = self._relevant_links(
            homepage["url"],
            homepage["links"],
            homepage_host,
        )

        for candidate in candidates:
            if len(pages) >= self.MAX_PAGES:
                break

            normalized = self._normalize_url(candidate)
            if normalized is None or normalized in visited:
                continue

            visited.add(normalized)

            try:
                page = self._research_page(normalized, expected_host=homepage_host)
            except WebsiteResearchError:
                continue

            final_host = urlsplit(page["url"]).hostname
            if final_host != homepage_host:
                continue

            pages.append(page)

        combined_text = "\n\n".join(
            f"Page: {page['title']}\nURL: {page['url']}\n{page['text']}"
            for page in pages
        )

        return {
            "url": homepage["url"],
            "title": homepage["title"],
            "text": combined_text[: self.MAX_TEXT_LENGTH],
            "pages": pages,
        }

    def _research_page(
        self, url: str, expected_host: str | None = None
    ) -> dict[str, object]:
        """Fetch one page, enforce URL and response limits, and extract links."""
        current_url = self._validate_url(url)

        with httpx.Client(
            timeout=self.TIMEOUT_SECONDS,
            follow_redirects=False,
            headers={"User-Agent": "AutonomousSalesAgent/0.1"},
            trust_env=False,
        ) as client:
            for _ in range(self.MAX_REDIRECTS + 1):
                self._validate_public_host(current_url)

                try:
                    with client.stream("GET", current_url) as response:
                        if response.status_code in (301, 302, 303, 307, 308):
                            location = response.headers.get("location")
                            if not location:
                                raise WebsiteResearchError(
                                    "Redirect has no destination."
                                )

                            redirect_url = self._validate_url(
                                urljoin(current_url, location)
                            )
                            if (
                                expected_host is not None
                                and urlsplit(redirect_url).hostname != expected_host
                            ):
                                raise WebsiteResearchError(
                                    "Cross-host redirects are not allowed "
                                    "during multi-page research."
                                )
                            current_url = redirect_url
                            continue

                        response.raise_for_status()

                        content_type = response.headers.get(
                            "content-type", ""
                        ).lower()
                        if "text/html" not in content_type:
                            raise WebsiteResearchError(
                                "Website did not return HTML."
                            )

                        declared_size = response.headers.get("content-length")
                        if declared_size:
                            try:
                                if int(declared_size) > self.MAX_BYTES:
                                    raise WebsiteResearchError(
                                        "Website response exceeds size limit."
                                    )
                            except ValueError as exc:
                                raise WebsiteResearchError(
                                    "Invalid content length."
                                ) from exc

                        chunks: list[bytes] = []
                        total_bytes = 0

                        for chunk in response.iter_bytes():
                            total_bytes += len(chunk)
                            if total_bytes > self.MAX_BYTES:
                                raise WebsiteResearchError(
                                    "Website response exceeds size limit."
                                )
                            chunks.append(chunk)

                        html = b"".join(chunks)

                except WebsiteResearchError:
                    raise
                except httpx.HTTPError as exc:
                    raise WebsiteResearchError(
                        f"Website request failed: {exc}"
                    ) from exc

                soup = BeautifulSoup(html, "html.parser")

                links = [
                    urljoin(current_url, anchor["href"])
                    for anchor in soup.find_all("a", href=True)[
                        : self.MAX_LINKS_TO_CHECK
                    ]
                ]

                for element in soup(
                    ["script", "style", "noscript", "svg", "nav", "footer"]
                ):
                    element.decompose()

                title = soup.title.get_text(" ", strip=True) if soup.title else ""
                text = soup.get_text(" ", strip=True)

                return {
                    "url": current_url,
                    "title": title[:500],
                    "text": text[: self.MAX_TEXT_LENGTH],
                    "links": links,
                }

        raise WebsiteResearchError("Website exceeded redirect limit.")

    def _relevant_links(
        self,
        base_url: str,
        links: list[str],
        expected_host: str | None,
    ) -> list[str]:
        """Select relevant links that remain on the exact same hostname."""
        relevant: list[str] = []

        for link in links:
            normalized = self._normalize_url(urljoin(base_url, link))
            if normalized is None:
                continue

            parsed = urlsplit(normalized)
            if parsed.hostname != expected_host:
                continue

            path_parts = [
                part.lower()
                for part in parsed.path.strip("/").split("/")
                if part
            ]

            if any(part in self.RELEVANT_PATHS for part in path_parts):
                relevant.append(normalized)

        return list(dict.fromkeys(relevant))

    @staticmethod
    def _normalize_url(url: str) -> str | None:
        """Normalize a candidate URL, rejecting invalid or credentialed URLs."""
        try:
            value = urldefrag(url.strip()).url
            parsed = urlsplit(value)

            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.port == 0
            ):
                return None

            return value
        except ValueError:
            return None

    @staticmethod
    def _validate_url(url: str) -> str:
        """Allow absolute HTTP(S) URLs without embedded credentials."""
        try:
            value = url.strip()
            parsed = urlsplit(value)

            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.port == 0
            ):
                raise WebsiteResearchError(
                    "Provide a valid HTTP or HTTPS website URL."
                )

            return value
        except ValueError as exc:
            raise WebsiteResearchError("Invalid website URL.") from exc

    @staticmethod
    def _validate_public_host(url: str) -> None:
        """Reject hosts resolving to non-public IP addresses."""
        parsed = urlsplit(url)
        hostname = parsed.hostname

        if not hostname:
            raise WebsiteResearchError("Website hostname is missing.")

        try:
            addresses = socket.getaddrinfo(
                hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise WebsiteResearchError(
                "Website hostname could not be resolved."
            ) from exc

        if not addresses:
            raise WebsiteResearchError("No IP addresses found for website.")

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise WebsiteResearchError(
                    "Private or non-public website addresses are not allowed."
                )

