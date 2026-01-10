"""
Browser Capability - Web browser automation with Playwright.

Provides capabilities for:
- Web page navigation and interaction
- Screenshot capture
- PDF generation from web pages
- Form filling and submission
- Web scraping
- JavaScript execution
"""

import asyncio
import base64
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import BaseCapability, CapabilityResult


class BrowserType(str, Enum):
    """Supported browser types."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class WaitStrategy(str, Enum):
    """Page load wait strategies."""

    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"
    COMMIT = "commit"


@dataclass
class BrowserConfig:
    """Configuration for browser capability."""

    # Browser settings
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    slow_mo: int = 0  # Slow down operations by milliseconds

    # Viewport settings
    viewport_width: int = 1280
    viewport_height: int = 720

    # Timeout settings
    default_timeout: int = 30000  # milliseconds
    navigation_timeout: int = 60000

    # User agent
    user_agent: str | None = None

    # Proxy settings
    proxy_server: str | None = None
    proxy_username: str | None = None
    proxy_password: str | None = None

    # Storage
    storage_state: str | None = None  # Path to storage state file
    downloads_path: str | None = None

    # Options
    ignore_https_errors: bool = False
    java_script_enabled: bool = True
    locale: str = "en-US"
    timezone_id: str | None = None

    # Extra launch args
    extra_args: list[str] = field(default_factory=list)


@dataclass
class ElementInfo:
    """Information about a DOM element."""

    tag: str
    text: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)
    visible: bool = True
    enabled: bool = True
    bounding_box: dict[str, float] | None = None


class BrowserCapability(BaseCapability):
    """
    Browser automation capability using Playwright.

    Provides operations for:
    - Web page navigation
    - Element interaction (click, type, select)
    - Screenshots and PDF generation
    - Web scraping
    - JavaScript execution

    Example:
        capability = BrowserCapability(config=BrowserConfig(
            headless=True,
            browser_type=BrowserType.CHROMIUM
        ))

        # Navigate and screenshot
        result = await capability.navigate("https://example.com")
        result = await capability.screenshot("page.png")

        # Interact with elements
        result = await capability.click("button#submit")
        result = await capability.fill("input[name='email']", "test@example.com")

        # Extract content
        result = await capability.get_text("h1")
        result = await capability.evaluate("document.title")
    """

    name = "browser"
    description = "Web browser automation with Playwright"

    def __init__(self, config: BrowserConfig | None = None):
        """Initialize browser capability."""
        self.config = config or BrowserConfig()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Playwright is available."""
        self._playwright_available = False
        try:
            from playwright.async_api import async_playwright  # noqa: F401

            self._playwright_available = True
        except ImportError:
            pass

    @property
    def is_available(self) -> bool:
        """Check if Playwright is available."""
        return self._playwright_available

    async def _ensure_browser(self) -> None:
        """Ensure browser is launched."""
        if not self._playwright_available:
            raise RuntimeError(
                "playwright not installed. "
                "Install with: pip install playwright && playwright install"
            )

        if self._page is not None:
            return

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        # Select browser type
        if self.config.browser_type == BrowserType.FIREFOX:
            browser_launcher = self._playwright.firefox
        elif self.config.browser_type == BrowserType.WEBKIT:
            browser_launcher = self._playwright.webkit
        else:
            browser_launcher = self._playwright.chromium

        # Launch options
        launch_options = {
            "headless": self.config.headless,
            "slow_mo": self.config.slow_mo,
        }

        if self.config.extra_args:
            launch_options["args"] = self.config.extra_args

        if self.config.proxy_server:
            launch_options["proxy"] = {
                "server": self.config.proxy_server,
            }
            if self.config.proxy_username:
                launch_options["proxy"]["username"] = self.config.proxy_username
                launch_options["proxy"]["password"] = self.config.proxy_password

        if self.config.downloads_path:
            launch_options["downloads_path"] = self.config.downloads_path

        self._browser = await browser_launcher.launch(**launch_options)

        # Context options
        context_options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "ignore_https_errors": self.config.ignore_https_errors,
            "java_script_enabled": self.config.java_script_enabled,
            "locale": self.config.locale,
        }

        if self.config.user_agent:
            context_options["user_agent"] = self.config.user_agent

        if self.config.timezone_id:
            context_options["timezone_id"] = self.config.timezone_id

        if self.config.storage_state and os.path.exists(self.config.storage_state):
            context_options["storage_state"] = self.config.storage_state

        self._context = await self._browser.new_context(**context_options)
        self._context.set_default_timeout(self.config.default_timeout)
        self._context.set_default_navigation_timeout(self.config.navigation_timeout)

        self._page = await self._context.new_page()

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self._page:
            await self._page.close()
            self._page = None

        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> CapabilityResult:
        """
        Execute a browser operation.

        Args:
            operation: Operation to perform
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation output
        """
        operations = {
            # Navigation
            "navigate": self._navigate,
            "go_back": self._go_back,
            "go_forward": self._go_forward,
            "reload": self._reload,
            # Interaction
            "click": self._click,
            "fill": self._fill,
            "type": self._type,
            "select": self._select,
            "check": self._check,
            "uncheck": self._uncheck,
            "hover": self._hover,
            "focus": self._focus,
            "press": self._press,
            # Content
            "get_text": self._get_text,
            "get_html": self._get_html,
            "get_attribute": self._get_attribute,
            "get_elements": self._get_elements,
            # Screenshots/PDF
            "screenshot": self._screenshot,
            "pdf": self._pdf,
            # JavaScript
            "evaluate": self._evaluate,
            # Waiting
            "wait_for_selector": self._wait_for_selector,
            "wait_for_navigation": self._wait_for_navigation,
            "wait_for_timeout": self._wait_for_timeout,
            # State
            "get_url": self._get_url,
            "get_title": self._get_title,
            "get_cookies": self._get_cookies,
            "set_cookies": self._set_cookies,
            # Storage
            "save_storage": self._save_storage,
            "load_storage": self._load_storage,
            # Close
            "close": self._close_operation,
        }

        if operation not in operations:
            return CapabilityResult(
                success=False,
                output={"error": f"Unknown operation: {operation}"},
                error=f"Supported operations: {list(operations.keys())}",
            )

        try:
            await self._ensure_browser()
            result = await operations[operation](**kwargs)
            return CapabilityResult(success=True, output=result)
        except Exception as e:
            return CapabilityResult(
                success=False, output={"error": str(e)}, error=str(e)
            )

    # =========================================================================
    # Navigation
    # =========================================================================

    async def _navigate(
        self,
        url: str,
        wait_until: str = "load",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Navigate to a URL."""
        response = await self._page.goto(url, wait_until=wait_until)
        return {
            "url": self._page.url,
            "status": response.status if response else None,
            "ok": response.ok if response else None,
        }

    async def _go_back(self, **kwargs: Any) -> dict[str, Any]:
        """Navigate back in history."""
        response = await self._page.go_back()
        return {"url": self._page.url, "success": response is not None}

    async def _go_forward(self, **kwargs: Any) -> dict[str, Any]:
        """Navigate forward in history."""
        response = await self._page.go_forward()
        return {"url": self._page.url, "success": response is not None}

    async def _reload(self, **kwargs: Any) -> dict[str, Any]:
        """Reload the page."""
        response = await self._page.reload()
        return {
            "url": self._page.url,
            "status": response.status if response else None,
        }

    # =========================================================================
    # Interaction
    # =========================================================================

    async def _click(
        self,
        selector: str,
        button: str = "left",
        click_count: int = 1,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Click an element."""
        await self._page.click(selector, button=button, click_count=click_count)
        return {"success": True, "selector": selector}

    async def _fill(
        self, selector: str, value: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Fill an input field."""
        await self._page.fill(selector, value)
        return {"success": True, "selector": selector}

    async def _type(
        self, selector: str, text: str, delay: int = 0, **kwargs: Any
    ) -> dict[str, Any]:
        """Type text into an element."""
        await self._page.type(selector, text, delay=delay)
        return {"success": True, "selector": selector}

    async def _select(
        self, selector: str, value: str | list[str], **kwargs: Any
    ) -> dict[str, Any]:
        """Select option(s) from a dropdown."""
        if isinstance(value, str):
            value = [value]
        selected = await self._page.select_option(selector, value)
        return {"success": True, "selector": selector, "selected": selected}

    async def _check(self, selector: str, **kwargs: Any) -> dict[str, Any]:
        """Check a checkbox."""
        await self._page.check(selector)
        return {"success": True, "selector": selector}

    async def _uncheck(self, selector: str, **kwargs: Any) -> dict[str, Any]:
        """Uncheck a checkbox."""
        await self._page.uncheck(selector)
        return {"success": True, "selector": selector}

    async def _hover(self, selector: str, **kwargs: Any) -> dict[str, Any]:
        """Hover over an element."""
        await self._page.hover(selector)
        return {"success": True, "selector": selector}

    async def _focus(self, selector: str, **kwargs: Any) -> dict[str, Any]:
        """Focus an element."""
        await self._page.focus(selector)
        return {"success": True, "selector": selector}

    async def _press(self, selector: str, key: str, **kwargs: Any) -> dict[str, Any]:
        """Press a key on an element."""
        await self._page.press(selector, key)
        return {"success": True, "selector": selector, "key": key}

    # =========================================================================
    # Content Extraction
    # =========================================================================

    async def _get_text(self, selector: str, **kwargs: Any) -> dict[str, Any]:
        """Get text content of an element."""
        text = await self._page.text_content(selector)
        return {"text": text, "selector": selector}

    async def _get_html(
        self, selector: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Get HTML content."""
        if selector:
            element = await self._page.query_selector(selector)
            if element:
                html = await element.inner_html()
            else:
                html = None
        else:
            html = await self._page.content()
        return {"html": html, "selector": selector}

    async def _get_attribute(
        self, selector: str, attribute: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Get attribute value of an element."""
        value = await self._page.get_attribute(selector, attribute)
        return {"value": value, "selector": selector, "attribute": attribute}

    async def _get_elements(
        self, selector: str, **kwargs: Any
    ) -> dict[str, list[dict[str, Any]]]:
        """Get information about multiple elements."""
        elements = await self._page.query_selector_all(selector)
        result = []

        for element in elements:
            info = {
                "tag": await element.evaluate("el => el.tagName.toLowerCase()"),
                "text": await element.text_content(),
                "visible": await element.is_visible(),
                "enabled": await element.is_enabled(),
            }

            # Get common attributes
            for attr in ["id", "class", "href", "src", "name", "value", "type"]:
                value = await element.get_attribute(attr)
                if value:
                    info[attr] = value

            result.append(info)

        return {"elements": result, "count": len(result)}

    # =========================================================================
    # Screenshots and PDF
    # =========================================================================

    async def _screenshot(
        self,
        path: str | None = None,
        full_page: bool = False,
        selector: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Take a screenshot."""
        options = {"full_page": full_page}

        if path:
            options["path"] = path

        if selector:
            element = await self._page.query_selector(selector)
            if element:
                screenshot = await element.screenshot(**options)
            else:
                raise ValueError(f"Element not found: {selector}")
        else:
            screenshot = await self._page.screenshot(**options)

        result = {"success": True}
        if path:
            result["path"] = path
        else:
            result["data"] = base64.b64encode(screenshot).decode("utf-8")

        return result

    async def _pdf(
        self,
        path: str,
        format: str = "A4",
        landscape: bool = False,
        print_background: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate PDF from page."""
        await self._page.pdf(
            path=path,
            format=format,
            landscape=landscape,
            print_background=print_background,
        )
        return {"success": True, "path": path}

    # =========================================================================
    # JavaScript Execution
    # =========================================================================

    async def _evaluate(
        self, expression: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute JavaScript in the page context."""
        result = await self._page.evaluate(expression)
        return {"result": result}

    # =========================================================================
    # Waiting
    # =========================================================================

    async def _wait_for_selector(
        self,
        selector: str,
        state: str = "visible",
        timeout: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Wait for an element to match a state."""
        await self._page.wait_for_selector(selector, state=state, timeout=timeout)
        return {"success": True, "selector": selector, "state": state}

    async def _wait_for_navigation(
        self,
        url: str | None = None,
        wait_until: str = "load",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Wait for navigation to complete."""
        await self._page.wait_for_load_state(wait_until)
        return {"success": True, "url": self._page.url}

    async def _wait_for_timeout(self, timeout: int, **kwargs: Any) -> dict[str, Any]:
        """Wait for specified milliseconds."""
        await self._page.wait_for_timeout(timeout)
        return {"success": True, "waited_ms": timeout}

    # =========================================================================
    # State
    # =========================================================================

    async def _get_url(self, **kwargs: Any) -> dict[str, Any]:
        """Get current URL."""
        return {"url": self._page.url}

    async def _get_title(self, **kwargs: Any) -> dict[str, Any]:
        """Get page title."""
        return {"title": await self._page.title()}

    async def _get_cookies(self, **kwargs: Any) -> dict[str, list[dict[str, Any]]]:
        """Get all cookies."""
        cookies = await self._context.cookies()
        return {"cookies": cookies}

    async def _set_cookies(
        self, cookies: list[dict[str, Any]], **kwargs: Any
    ) -> dict[str, Any]:
        """Set cookies."""
        await self._context.add_cookies(cookies)
        return {"success": True, "count": len(cookies)}

    async def _save_storage(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Save storage state (cookies, localStorage)."""
        await self._context.storage_state(path=path)
        return {"success": True, "path": path}

    async def _load_storage(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Load storage state."""
        # Need to recreate context with storage state
        if os.path.exists(path):
            self.config.storage_state = path
            # Close and reopen with new storage
            await self._page.close()
            await self._context.close()

            context_options = {
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
                "storage_state": path,
            }
            self._context = await self._browser.new_context(**context_options)
            self._page = await self._context.new_page()

            return {"success": True, "path": path}
        else:
            raise FileNotFoundError(f"Storage state file not found: {path}")

    async def _close_operation(self, **kwargs: Any) -> dict[str, Any]:
        """Close the browser."""
        await self.close()
        return {"success": True}

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def navigate(
        self, url: str, wait_until: str = "load"
    ) -> CapabilityResult:
        """Navigate to a URL."""
        return await self.execute("navigate", url=url, wait_until=wait_until)

    async def click(
        self, selector: str, button: str = "left", click_count: int = 1
    ) -> CapabilityResult:
        """Click an element."""
        return await self.execute(
            "click", selector=selector, button=button, click_count=click_count
        )

    async def fill(self, selector: str, value: str) -> CapabilityResult:
        """Fill an input field."""
        return await self.execute("fill", selector=selector, value=value)

    async def type_text(
        self, selector: str, text: str, delay: int = 0
    ) -> CapabilityResult:
        """Type text into an element."""
        return await self.execute("type", selector=selector, text=text, delay=delay)

    async def select(
        self, selector: str, value: str | list[str]
    ) -> CapabilityResult:
        """Select option(s) from a dropdown."""
        return await self.execute("select", selector=selector, value=value)

    async def get_text(self, selector: str) -> CapabilityResult:
        """Get text content of an element."""
        return await self.execute("get_text", selector=selector)

    async def get_html(self, selector: str | None = None) -> CapabilityResult:
        """Get HTML content."""
        return await self.execute("get_html", selector=selector)

    async def screenshot(
        self,
        path: str | None = None,
        full_page: bool = False,
        selector: str | None = None,
    ) -> CapabilityResult:
        """Take a screenshot."""
        return await self.execute(
            "screenshot", path=path, full_page=full_page, selector=selector
        )

    async def pdf(
        self,
        path: str,
        format: str = "A4",
        landscape: bool = False,
        print_background: bool = True,
    ) -> CapabilityResult:
        """Generate PDF from page."""
        return await self.execute(
            "pdf",
            path=path,
            format=format,
            landscape=landscape,
            print_background=print_background,
        )

    async def evaluate(self, expression: str) -> CapabilityResult:
        """Execute JavaScript in the page context."""
        return await self.execute("evaluate", expression=expression)

    async def wait_for_selector(
        self, selector: str, state: str = "visible", timeout: int | None = None
    ) -> CapabilityResult:
        """Wait for an element to match a state."""
        return await self.execute(
            "wait_for_selector", selector=selector, state=state, timeout=timeout
        )

    async def get_url(self) -> CapabilityResult:
        """Get current URL."""
        return await self.execute("get_url")

    async def get_title(self) -> CapabilityResult:
        """Get page title."""
        return await self.execute("get_title")

    async def run(self, operation: str, **kwargs: Any) -> CapabilityResult:
        """Run a browser operation (alias for execute)."""
        return await self.execute(operation, **kwargs)

    async def __aenter__(self) -> "BrowserCapability":
        """Async context manager entry."""
        await self._ensure_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
