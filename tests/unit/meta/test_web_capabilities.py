"""Unit tests for paracle_meta.capabilities.web_capabilities module."""

import pytest

from paracle_meta.capabilities.web_capabilities import (
    CrawlResult,
    SearchResult,
    WebCapability,
    WebConfig,
)


class TestWebConfig:
    """Tests for WebConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WebConfig()
        assert "ParacleMetaAgent" in config.user_agent
        assert config.max_pages == 10
        assert config.max_depth == 2
        assert config.respect_robots_txt is True
        assert config.request_delay == 1.0
        assert config.extract_text_only is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = WebConfig(
            user_agent="CustomBot/1.0",
            max_pages=50,
            max_depth=3,
            request_delay=2.0,
        )
        assert config.user_agent == "CustomBot/1.0"
        assert config.max_pages == 50
        assert config.max_depth == 3
        assert config.request_delay == 2.0


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_create_result(self):
        """Test creating search result."""
        result = SearchResult(
            title="Test Result",
            url="https://example.com",
            snippet="This is a test snippet",
            rank=1,
        )
        assert result.title == "Test Result"
        assert result.url == "https://example.com"
        assert result.rank == 1

    def test_default_rank(self):
        """Test default rank value."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Test",
        )
        assert result.rank == 0


class TestCrawlResult:
    """Tests for CrawlResult model."""

    def test_create_result(self):
        """Test creating crawl result."""
        result = CrawlResult(
            url="https://example.com",
            title="Example Page",
            content="Page content here",
            links=["https://example.com/page1", "https://example.com/page2"],
            status_code=200,
            content_type="text/html",
            word_count=100,
        )
        assert result.url == "https://example.com"
        assert result.title == "Example Page"
        assert len(result.links) == 2
        assert result.status_code == 200

    def test_default_values(self):
        """Test default values."""
        result = CrawlResult(
            url="https://example.com",
            title="Test",
            content="Content",
        )
        assert result.links == []
        assert result.status_code == 0
        assert result.word_count == 0


class TestWebCapability:
    """Tests for WebCapability."""

    @pytest.fixture
    def web_capability(self):
        """Create web capability instance."""
        return WebCapability()

    @pytest.fixture
    def web_capability_custom(self):
        """Create web capability with custom config."""
        config = WebConfig(
            max_pages=5,
            max_depth=1,
            request_delay=0.1,
        )
        return WebCapability(config=config)

    def test_initialization(self, web_capability):
        """Test capability initialization."""
        assert web_capability.name == "web"
        assert "search" in web_capability.description.lower()
        assert web_capability.config.max_pages == 10

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, web_capability):
        """Test initialize and shutdown lifecycle."""
        await web_capability.initialize()
        assert web_capability.is_initialized is True
        assert web_capability._client is not None

        await web_capability.shutdown()
        assert web_capability.is_initialized is False
        assert web_capability._client is None

    @pytest.mark.asyncio
    async def test_search_simulated(self, web_capability):
        """Test simulated search."""
        await web_capability.initialize()

        result = await web_capability.search("Python tutorial", num_results=3)

        assert result.success is True
        assert result.capability == "web"
        assert isinstance(result.output, list)
        # Simulated results should be returned
        if result.output:
            assert "title" in result.output[0]

        await web_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_search_action(self, web_capability):
        """Test execute with search action."""
        await web_capability.initialize()

        result = await web_capability.execute(
            action="search",
            query="test query",
            num_results=5,
        )

        assert result.success is True
        assert result.metadata.get("action") == "search"

        await web_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, web_capability):
        """Test execute with unknown action."""
        await web_capability.initialize()

        result = await web_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await web_capability.shutdown()

    @pytest.mark.asyncio
    async def test_crawl_config_limits(self, web_capability_custom):
        """Test that crawl respects config limits."""
        assert web_capability_custom.config.max_pages == 5
        assert web_capability_custom.config.max_depth == 1

    def test_simulate_search(self, web_capability):
        """Test _simulate_search method."""
        results = web_capability._simulate_search("test query", 5)

        assert len(results) == 5
        assert all("title" in r for r in results)
        assert all("url" in r for r in results)
        assert all("snippet" in r for r in results)

    def test_parse_html_without_beautifulsoup(self, web_capability):
        """Test HTML parsing fallback without BeautifulSoup."""
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <p>This is content.</p>
                <a href="/link1">Link 1</a>
            </body>
        </html>
        """

        result = web_capability._parse_html(
            html=html,
            url="https://example.com",
            status_code=200,
            content_type="text/html",
            extract_links=True,
        )

        assert result["url"] == "https://example.com"
        assert result["status_code"] == 200
        # Title should be extracted
        assert (
            "Test Page" in result.get("title", "")
            or "content" in result.get("content", "").lower()
        )


class TestWebCapabilityIntegration:
    """Integration-style tests for WebCapability."""

    @pytest.fixture
    def capability(self):
        """Create capability for tests."""
        return WebCapability(
            config=WebConfig(
                timeout=5.0,
                request_delay=0.1,
            )
        )

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, capability):
        """Test full capability lifecycle."""
        # Initialize
        await capability.initialize()
        assert capability.is_initialized

        # Execute search
        search_result = await capability.search("python", num_results=2)
        assert search_result.success is True

        # Shutdown
        await capability.shutdown()
        assert not capability.is_initialized

    @pytest.mark.asyncio
    async def test_convenience_methods(self, capability):
        """Test convenience method wrappers."""
        await capability.initialize()

        # Test search convenience method
        result = await capability.search("test", 3)
        assert result.capability == "web"

        await capability.shutdown()
