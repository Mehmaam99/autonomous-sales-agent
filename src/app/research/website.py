import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup


class WebsiteResearchError(Exception):
    """Raised when website content cannot be fetched safely."""


class WebsiteResearcher:
    """Fetch and extract readable text from public company websites."""

    MAX_BYTES = 1_000_000
    MAX_REDIRECTS = 3
    TIMEOUT_SECONDS = 10.0

    def research(self, url: str) -> dict[str, str]:
        """Fetch a public HTML page and extract readable text."""
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
                            current_url = self._validate_url(
                                urljoin(current_url, location)
                            )
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

                for element in soup(
                    ["script", "style", "noscript", "svg", "nav", "footer"]
                ):
                    element.decompose()

                title = soup.title.get_text(" ", strip=True) if soup.title else ""
                text = soup.get_text(" ", strip=True)

                return {
                    "url": current_url,
                    "title": title[:500],
                    "text": text[:20_000],
                }

        raise WebsiteResearchError("Website exceeded redirect limit.")

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
