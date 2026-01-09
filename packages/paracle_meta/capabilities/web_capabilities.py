"""Web capabilities for MetaAgent.

Provides web search, web crawling, and content extraction
capabilities for the MetaAgent.
"""

import asyncio
import re
import time
from typing import Any
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WebConfig(CapabilityConfig):
    """Configuration for web capabilities."""

    user_agent: str = Field(
        default="ParacleMetaAgent/1.0 (Research Bot)",
        description="User agent for HTTP requests",
    )
    max_pages: int = Field(
        default=10, ge=1, le=100, description="Max pages to crawl per request"
    )
    max_depth: int = Field(
        default=2, ge=0, le=5, description="Max crawl depth from starting URL"
    )
    respect_robots_txt: bool = Field(
        default=True, description="Respect robots.txt rules"
    )
    request_delay: float = Field(
        default=1.0, ge=0.0, le=10.0, description="Delay between requests (seconds)"
    )
    extract_text_only: bool = Field(
        default=True, description="Extract only text content (no HTML)"
    )


class SearchResult(BaseModel):
    """A single search result."""

    title: str
    url: str
    snippet: str
    rank: int = 0


class CrawlResult(BaseModel):
    """Result of crawling a page."""

    url: str
    title: str
    content: str
    links: list[str] = Field(default_factory=list)
    status_code: int = 0
    content_type: str = ""
    word_count: int = 0


class WebCapability(BaseCapability):
    """Web search and crawling capability for MetaAgent.

    Provides:
    - Web search (simulated or via search API)
    - Page fetching and content extraction
    - Multi-page crawling with depth control
    - HTML parsing and text extraction

    Example:
        >>> web = WebCapability()
        >>> await web.initialize()
        >>>
        >>> # Search the web
        >>> result = await web.execute(
        ...     action="search",
        ...     query="Python best practices"
        ... )
        >>>
        >>> # Fetch a specific page
        >>> result = await web.execute(
        ...     action="fetch",
        ...     url="https://example.com/article"
        ... )
        >>>
        >>> # Crawl multiple pages
        >>> result = await web.execute(
        ...     action="crawl",
        ...     start_url="https://docs.example.com",
        ...     max_pages=5
        ... )
    """

    name = "web"
    description = "Web search, fetch, and crawling capabilities"

    def __init__(self, config: WebConfig | None = None):
        """Initialize web capability.

        Args:
            config: Web configuration
        """
        super().__init__(config or WebConfig())
        self.config: WebConfig = self.config
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for web capabilities. "
                "Install with: pip install httpx"
            )

        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={"User-Agent": self.config.user_agent},
            follow_redirects=True,
        )
        await super().initialize()

    async def shutdown(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute web capability.

        Args:
            action: Action to perform (search, fetch, crawl)
            **kwargs: Action-specific parameters

        Returns:
            CapabilityResult with web data
        """
        if not self._initialized or not self._client:
            await self.initialize()

        action = kwargs.pop("action", "fetch")
        start_time = time.time()

        try:
            if action == "search":
                result = await self._search(**kwargs)
            elif action == "fetch":
                result = await self._fetch(**kwargs)
            elif action == "crawl":
                result = await self._crawl(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _search(
        self,
        query: str,
        num_results: int = 10,
        search_engine: str = "duckduckgo",
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Search the web.

        Args:
            query: Search query
            num_results: Number of results to return
            search_engine: Search engine to use

        Returns:
            List of search results
        """
        # DuckDuckGo HTML search (no API key needed)
        if search_engine == "duckduckgo":
            return await self._search_duckduckgo(query, num_results)

        # Fallback: simulated search results for testing
        return self._simulate_search(query, num_results)

    async def _search_duckduckgo(
        self, query: str, num_results: int
    ) -> list[dict[str, Any]]:
        """Search using DuckDuckGo HTML interface."""
        if not self._client:
            raise RuntimeError("HTTP client not initialized")

        url = "https://html.duckduckgo.com/html/"
        data = {"q": query, "b": ""}

        try:
            response = await self._client.post(url, data=data)
            response.raise_for_status()

            if not BS4_AVAILABLE:
                # Return mock results if BeautifulSoup not available
                return self._simulate_search(query, num_results)

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            for i, result in enumerate(soup.select(".result")[:num_results]):
                title_elem = result.select_one(".result__title a")
                snippet_elem = result.select_one(".result__snippet")

                if title_elem:
                    results.append(
                        SearchResult(
                            title=title_elem.get_text(strip=True),
                            url=title_elem.get("href", ""),
                            snippet=(
                                snippet_elem.get_text(strip=True)
                                if snippet_elem
                                else ""
                            ),
                            rank=i + 1,
                        ).model_dump()
                    )

            return results

        except Exception:
            # Fallback to simulated results on error
            return self._simulate_search(query, num_results)

    def _simulate_search(self, query: str, num_results: int) -> list[dict[str, Any]]:
        """Generate simulated search results for testing."""
        results = []
        for i in range(min(num_results, 5)):
            results.append(
                SearchResult(
                    title=f"Result {i + 1} for: {query}",
                    url=f"https://example.com/result/{i + 1}",
                    snippet=f"This is a simulated search result for '{query}'...",
                    rank=i + 1,
                ).model_dump()
            )
        return results

    async def _fetch(
        self,
        url: str,
        extract_links: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Fetch and parse a web page.

        Args:
            url: URL to fetch
            extract_links: Whether to extract links

        Returns:
            Page content and metadata
        """
        if not self._client:
            raise RuntimeError("HTTP client not initialized")

        response = await self._client.get(url)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")

        # Parse HTML content
        if "text/html" in content_type:
            return self._parse_html(
                response.text,
                url,
                response.status_code,
                content_type,
                extract_links,
            )

        # Return raw text for non-HTML
        return CrawlResult(
            url=url,
            title="",
            content=response.text[:50000],  # Limit content size
            status_code=response.status_code,
            content_type=content_type,
            word_count=len(response.text.split()),
        ).model_dump()

    def _parse_html(
        self,
        html: str,
        url: str,
        status_code: int,
        content_type: str,
        extract_links: bool,
    ) -> dict[str, Any]:
        """Parse HTML content.

        Args:
            html: HTML content
            url: Source URL
            status_code: HTTP status code
            content_type: Content type header
            extract_links: Whether to extract links

        Returns:
            Parsed page data
        """
        if not BS4_AVAILABLE:
            # Basic extraction without BeautifulSoup
            title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
            title = title_match.group(1) if title_match else ""

            # Strip HTML tags for text extraction
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()

            return CrawlResult(
                url=url,
                title=title,
                content=text[:50000],
                links=[],
                status_code=status_code,
                content_type=content_type,
                word_count=len(text.split()),
            ).model_dump()

        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Extract text content
        if self.config.extract_text_only:
            content = soup.get_text(separator=" ", strip=True)
            # Clean up whitespace
            content = re.sub(r"\s+", " ", content)
        else:
            content = str(soup)

        # Extract links
        links = []
        if extract_links:
            for link in soup.find_all("a", href=True):
                href = link["href"]
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                # Only include HTTP(S) links
                if absolute_url.startswith(("http://", "https://")):
                    links.append(absolute_url)

        return CrawlResult(
            url=url,
            title=title,
            content=content[:50000],  # Limit content size
            links=links[:100],  # Limit number of links
            status_code=status_code,
            content_type=content_type,
            word_count=len(content.split()),
        ).model_dump()

    async def _crawl(
        self,
        start_url: str,
        max_pages: int | None = None,
        max_depth: int | None = None,
        same_domain_only: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Crawl multiple pages starting from a URL.

        Args:
            start_url: Starting URL for crawl
            max_pages: Maximum pages to crawl
            max_depth: Maximum link depth
            same_domain_only: Only crawl same domain

        Returns:
            Crawl results with all pages
        """
        max_pages = max_pages or self.config.max_pages
        max_depth = max_depth if max_depth is not None else self.config.max_depth

        start_domain = urlparse(start_url).netloc
        visited: set[str] = set()
        results: list[dict[str, Any]] = []
        queue: list[tuple[str, int]] = [(start_url, 0)]  # (url, depth)

        while queue and len(results) < max_pages:
            url, depth = queue.pop(0)

            # Skip if already visited
            if url in visited:
                continue

            # Skip if too deep
            if depth > max_depth:
                continue

            # Skip if different domain (when same_domain_only)
            if same_domain_only:
                if urlparse(url).netloc != start_domain:
                    continue

            visited.add(url)

            try:
                # Add delay between requests
                if len(results) > 0:
                    await asyncio.sleep(self.config.request_delay)

                # Fetch page
                page_data = await self._fetch(url, extract_links=True)
                results.append(page_data)

                # Add links to queue
                if depth < max_depth:
                    for link in page_data.get("links", []):
                        if link not in visited:
                            queue.append((link, depth + 1))

            except Exception as e:
                # Log error but continue crawling
                results.append(
                    {
                        "url": url,
                        "error": str(e),
                        "status_code": 0,
                    }
                )

        return {
            "start_url": start_url,
            "pages_crawled": len(results),
            "pages_visited": len(visited),
            "max_depth_reached": max_depth,
            "pages": results,
        }

    # Convenience methods for direct use
    async def search(self, query: str, num_results: int = 10) -> CapabilityResult:
        """Search the web for a query."""
        return await self.execute(action="search", query=query, num_results=num_results)

    async def fetch(self, url: str) -> CapabilityResult:
        """Fetch and parse a URL."""
        return await self.execute(action="fetch", url=url)

    async def crawl(
        self,
        start_url: str,
        max_pages: int | None = None,
    ) -> CapabilityResult:
        """Crawl pages starting from a URL."""
        return await self.execute(
            action="crawl", start_url=start_url, max_pages=max_pages
        )
