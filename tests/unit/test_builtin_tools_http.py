"""Tests for built-in HTTP tools."""

import pytest
from unittest.mock import AsyncMock, patch

from paracle_tools.builtin.http import (
    HTTPGetTool,
    HTTPPostTool,
    HTTPPutTool,
    HTTPDeleteTool,
)


# Skip tests if httpx is not installed
pytest.importorskip("httpx")


class TestHTTPGetTool:
    """Test http_get tool."""

    @pytest.mark.asyncio
    async def test_get_success(self):
        # Arrange
        from unittest.mock import Mock
        tool = HTTPGetTool()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"message": "success"}'
        mock_response.json.return_value = {"message": "success"}
        mock_response.url = "https://api.example.com/test"

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            result = await tool.execute(url="https://api.example.com/test")

        # Assert
        assert result.success is True
        assert result.output["status_code"] == 200
        assert result.output["json"]["message"] == "success"

    @pytest.mark.asyncio
    async def test_get_with_headers_and_params(self):
        # Arrange
        tool = HTTPGetTool()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "response text"
        mock_response.url = "https://api.example.com/test"

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.get.return_value = mock_response

            result = await tool.execute(
                url="https://api.example.com/test",
                headers={"Authorization": "Bearer token"},
                params={"key": "value"}
            )

            # Verify headers and params were passed
            mock_client_instance.get.assert_called_once()
            call_args = mock_client_instance.get.call_args

        # Assert
        assert result.success is True
        assert result.output["status_code"] == 200

    @pytest.mark.asyncio
    async def test_get_timeout(self):
        # Arrange
        tool = HTTPGetTool(timeout=1.0)

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            import httpx
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")

            result = await tool.execute(url="https://slow.example.com")

        # Assert
        assert result.success is False
        assert "timed out" in result.error.lower()


class TestHTTPPostTool:
    """Test http_post tool."""

    @pytest.mark.asyncio
    async def test_post_with_json(self):
        # Arrange
        from unittest.mock import Mock
        tool = HTTPPostTool()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"id": 123}'
        mock_response.json.return_value = {"id": 123}
        mock_response.url = "https://api.example.com/items"

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await tool.execute(
                url="https://api.example.com/items",
                json_data={"name": "test item"}
            )

        # Assert
        assert result.success is True
        assert result.output["status_code"] == 201
        assert result.output["json"]["id"] == 123

    @pytest.mark.asyncio
    async def test_post_with_form_data(self):
        # Arrange
        tool = HTTPPostTool()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "<html>success</html>"
        mock_response.url = "https://example.com/submit"

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await tool.execute(
                url="https://example.com/submit",
                form_data={"field1": "value1", "field2": "value2"}
            )

        # Assert
        assert result.success is True
        assert result.output["status_code"] == 200


class TestHTTPPutTool:
    """Test http_put tool."""

    @pytest.mark.asyncio
    async def test_put_success(self):
        # Arrange
        from unittest.mock import Mock
        tool = HTTPPutTool()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"updated": true}'
        mock_response.json.return_value = {"updated": True}
        mock_response.url = "https://api.example.com/items/123"

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.put.return_value = mock_response

            result = await tool.execute(
                url="https://api.example.com/items/123",
                json_data={"name": "updated item"}
            )

        # Assert
        assert result.success is True
        assert result.output["status_code"] == 200


class TestHTTPDeleteTool:
    """Test http_delete tool."""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        # Arrange
        tool = HTTPDeleteTool()
        mock_response = AsyncMock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_response.text = ""
        mock_response.url = "https://api.example.com/items/123"

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.delete.return_value = mock_response

            result = await tool.execute(url="https://api.example.com/items/123")

        # Assert
        assert result.success is True
        assert result.output["status_code"] == 204
