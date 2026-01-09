"""HTTP tools for making web requests."""

from __future__ import annotations

from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from paracle_tools.builtin.base import BaseTool, ToolError


class HTTPGetTool(BaseTool):
    """Tool for making HTTP GET requests."""

    def __init__(self, timeout: float = 30.0):
        """Initialize http_get tool.

        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(
            name="http_get",
            description="Make an HTTP GET request",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to request",
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers to send",
                        "default": {},
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters",
                        "default": {},
                    },
                },
                "required": ["url"],
            },
            permissions=["http:request"],
        )
        self.timeout = timeout

    async def _execute(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Make HTTP GET request.

        Args:
            url: URL to request
            headers: HTTP headers
            params: Query parameters

        Returns:
            Dictionary with response data

        Raises:
            ToolError: If httpx is not installed or request fails
        """
        if not HTTPX_AVAILABLE:
            raise ToolError(
                self.name,
                "httpx library is not installed. Install it with: pip install httpx",
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=headers or {},
                    params=params or {},
                )

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                    "json": response.json() if self._is_json(response) else None,
                    "url": str(response.url),
                }
        except httpx.TimeoutException:
            raise ToolError(
                self.name,
                f"Request timed out after {self.timeout}s",
                {"url": url},
            )
        except httpx.HTTPError as e:
            raise ToolError(
                self.name,
                f"HTTP request failed: {e}",
                {"url": url},
            )
        except Exception as e:
            raise ToolError(
                self.name,
                f"Unexpected error: {e}",
                {"url": url},
            )

    def _is_json(self, response: Any) -> bool:
        """Check if response is JSON."""
        content_type = response.headers.get("content-type", "")
        return "application/json" in content_type


class HTTPPostTool(BaseTool):
    """Tool for making HTTP POST requests."""

    def __init__(self, timeout: float = 30.0):
        """Initialize http_post tool.

        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(
            name="http_post",
            description="Make an HTTP POST request",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to request",
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers to send",
                        "default": {},
                    },
                    "json_data": {
                        "type": "object",
                        "description": "JSON data to send in request body",
                        "default": None,
                    },
                    "form_data": {
                        "type": "object",
                        "description": "Form data to send",
                        "default": None,
                    },
                },
                "required": ["url"],
            },
            permissions=["http:request"],
        )
        self.timeout = timeout

    async def _execute(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
        form_data: dict[str, str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Make HTTP POST request.

        Args:
            url: URL to request
            headers: HTTP headers
            json_data: JSON data for request body
            form_data: Form data

        Returns:
            Dictionary with response data

        Raises:
            ToolError: If httpx is not installed or request fails
        """
        if not HTTPX_AVAILABLE:
            raise ToolError(
                self.name,
                "httpx library is not installed. Install it with: pip install httpx",
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=headers or {},
                    json=json_data,
                    data=form_data,
                )

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                    "json": response.json() if self._is_json(response) else None,
                    "url": str(response.url),
                }
        except httpx.TimeoutException:
            raise ToolError(
                self.name,
                f"Request timed out after {self.timeout}s",
                {"url": url},
            )
        except httpx.HTTPError as e:
            raise ToolError(
                self.name,
                f"HTTP request failed: {e}",
                {"url": url},
            )
        except Exception as e:
            raise ToolError(
                self.name,
                f"Unexpected error: {e}",
                {"url": url},
            )

    def _is_json(self, response: Any) -> bool:
        """Check if response is JSON."""
        content_type = response.headers.get("content-type", "")
        return "application/json" in content_type


class HTTPPutTool(BaseTool):
    """Tool for making HTTP PUT requests."""

    def __init__(self, timeout: float = 30.0):
        """Initialize http_put tool.

        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(
            name="http_put",
            description="Make an HTTP PUT request",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to request",
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers to send",
                        "default": {},
                    },
                    "json_data": {
                        "type": "object",
                        "description": "JSON data to send in request body",
                        "default": None,
                    },
                },
                "required": ["url"],
            },
            permissions=["http:request"],
        )
        self.timeout = timeout

    async def _execute(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Make HTTP PUT request.

        Args:
            url: URL to request
            headers: HTTP headers
            json_data: JSON data for request body

        Returns:
            Dictionary with response data

        Raises:
            ToolError: If httpx is not installed or request fails
        """
        if not HTTPX_AVAILABLE:
            raise ToolError(
                self.name,
                "httpx library is not installed. Install it with: pip install httpx",
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    url,
                    headers=headers or {},
                    json=json_data,
                )

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                    "json": response.json() if self._is_json(response) else None,
                    "url": str(response.url),
                }
        except httpx.TimeoutException:
            raise ToolError(
                self.name,
                f"Request timed out after {self.timeout}s",
                {"url": url},
            )
        except httpx.HTTPError as e:
            raise ToolError(
                self.name,
                f"HTTP request failed: {e}",
                {"url": url},
            )
        except Exception as e:
            raise ToolError(
                self.name,
                f"Unexpected error: {e}",
                {"url": url},
            )

    def _is_json(self, response: Any) -> bool:
        """Check if response is JSON."""
        content_type = response.headers.get("content-type", "")
        return "application/json" in content_type


class HTTPDeleteTool(BaseTool):
    """Tool for making HTTP DELETE requests."""

    def __init__(self, timeout: float = 30.0):
        """Initialize http_delete tool.

        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(
            name="http_delete",
            description="Make an HTTP DELETE request",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to request",
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers to send",
                        "default": {},
                    },
                },
                "required": ["url"],
            },
            permissions=["http:request"],
        )
        self.timeout = timeout

    async def _execute(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Make HTTP DELETE request.

        Args:
            url: URL to request
            headers: HTTP headers

        Returns:
            Dictionary with response data

        Raises:
            ToolError: If httpx is not installed or request fails
        """
        if not HTTPX_AVAILABLE:
            raise ToolError(
                self.name,
                "httpx library is not installed. Install it with: pip install httpx",
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    url,
                    headers=headers or {},
                )

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                    "json": response.json() if self._is_json(response) else None,
                    "url": str(response.url),
                }
        except httpx.TimeoutException:
            raise ToolError(
                self.name,
                f"Request timed out after {self.timeout}s",
                {"url": url},
            )
        except httpx.HTTPError as e:
            raise ToolError(
                self.name,
                f"HTTP request failed: {e}",
                {"url": url},
            )
        except Exception as e:
            raise ToolError(
                self.name,
                f"Unexpected error: {e}",
                {"url": url},
            )

    def _is_json(self, response: Any) -> bool:
        """Check if response is JSON."""
        content_type = response.headers.get("content-type", "")
        return "application/json" in content_type


# Create default instances
http_get = HTTPGetTool()
http_post = HTTPPostTool()
http_put = HTTPPutTool()
http_delete = HTTPDeleteTool()
