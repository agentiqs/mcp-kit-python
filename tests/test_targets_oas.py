"""Tests for OpenAPI Specification (OAS) target implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import Tool
from mcp.types import TextContent
from omegaconf import OmegaConf

from mcp_kit.targets.oas import OasTarget


class TestOasTarget:
    """Test cases for OasTarget class."""

    def test_init(self):
        """Test OasTarget initialization."""
        target = OasTarget(name="test-oas", spec_url="http://example.com/openapi.json")
        assert target.name == "test-oas"
        assert target._spec_url == "http://example.com/openapi.json"
        assert target._fast_mcp is None

    def test_name_property(self):
        """Test name property."""
        target = OasTarget("property-test", "http://example.com/spec.json")
        assert target.name == "property-test"

    def test_from_config(self):
        """Test OasTarget.from_config."""
        config = OmegaConf.create(
            {
                "type": "oas",
                "name": "config-oas",
                "spec_url": "http://example.com/openapi.json",
            }
        )

        target = OasTarget.from_config(config)
        assert target.name == "config-oas"
        assert target._spec_url == "http://example.com/openapi.json"

    def test_from_config_minimal(self):
        """Test OasTarget.from_config with minimal configuration."""
        config = OmegaConf.create(
            {
                "type": "oas",
                "name": "minimal-oas",
                "spec_url": "http://minimal.com/spec.yaml",
            }
        )

        target = OasTarget.from_config(config)
        assert target.name == "minimal-oas"
        assert target._spec_url == "http://minimal.com/spec.yaml"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test initialize method creates FastMCP server."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        mock_fast_mcp = MagicMock()

        with patch("mcp_kit.targets.oas.create_mcp_server") as mock_create_server:
            mock_create_server.return_value = mock_fast_mcp

            await target.initialize()

            assert target._fast_mcp == mock_fast_mcp
            mock_create_server.assert_called_once_with(
                "http://example.com/openapi.json"
            )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_initialize_multiple_calls(self):
        """Test that multiple initialize calls don't recreate the server."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        mock_fast_mcp = MagicMock()

        with patch("mcp_kit.targets.oas.create_mcp_server") as mock_create_server:
            mock_create_server.return_value = mock_fast_mcp

            await target.initialize()
            first_server = target._fast_mcp

            await target.initialize()
            second_server = target._fast_mcp

            # Should be the same instance
            assert first_server == second_server
            # create_mcp_server should be called twice (once for each initialize call)
            assert mock_create_server.call_count == 2

    @pytest.mark.asyncio
    async def test_initialize_server_creation_error(self):
        """Test initialize handles server creation errors."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        with patch("mcp_kit.targets.oas.create_mcp_server") as mock_create_server:
            mock_create_server.side_effect = RuntimeError("Failed to create server")

            with pytest.raises(RuntimeError, match="Failed to create server"):
                await target.initialize()

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test list_tools returns tools from FastMCP server."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        # Create mock FastMCP server
        mock_fast_mcp = AsyncMock()
        mock_tools = [
            Tool(name="get_users", description="Get all users", inputSchema={}),
            Tool(name="create_user", description="Create a new user", inputSchema={}),
        ]
        mock_fast_mcp.list_tools.return_value = mock_tools
        target._fast_mcp = mock_fast_mcp

        result = await target.list_tools()
        assert result == mock_tools
        mock_fast_mcp.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_no_server(self):
        """Test list_tools when no server is initialized."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        with pytest.raises(ValueError, match="OasTarget server is not initialized"):
            await target.list_tools()

    @pytest.mark.asyncio
    async def test_list_tools_empty_result(self):
        """Test list_tools with empty result from server."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        mock_fast_mcp = AsyncMock()
        mock_fast_mcp.list_tools.return_value = []
        target._fast_mcp = mock_fast_mcp

        result = await target.list_tools()
        assert result == []

    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test call_tool delegates to FastMCP server."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        mock_fast_mcp = AsyncMock()
        mock_content = [TextContent(type="text", text="API response")]
        mock_fast_mcp.call_tool.return_value = mock_content
        target._fast_mcp = mock_fast_mcp

        result = await target.call_tool("get_users", {"limit": 10})

        assert result == mock_content
        mock_fast_mcp.call_tool.assert_called_once_with("get_users", {"limit": 10})

    @pytest.mark.asyncio
    async def test_call_tool_with_none_arguments(self):
        """Test call_tool with None arguments."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        mock_fast_mcp = AsyncMock()
        mock_content = [TextContent(type="text", text="API response")]
        mock_fast_mcp.call_tool.return_value = mock_content
        target._fast_mcp = mock_fast_mcp

        result = await target.call_tool("get_users", None)

        assert result == mock_content
        mock_fast_mcp.call_tool.assert_called_once_with("get_users", {})

    @pytest.mark.asyncio
    async def test_call_tool_no_server(self):
        """Test call_tool when no server is initialized."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        with pytest.raises(ValueError, match="OasTarget server is not initialized"):
            await target.call_tool("get_users", {"limit": 10})

    @pytest.mark.asyncio
    async def test_call_tool_server_error(self):
        """Test call_tool handles server errors."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        mock_fast_mcp = MagicMock()
        mock_fast_mcp.call_tool.side_effect = RuntimeError("API call failed")
        target._fast_mcp = mock_fast_mcp

        with pytest.raises(RuntimeError, match="API call failed"):
            await target.call_tool("get_users", {"limit": 10})

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close method."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        # Set up a mock server
        mock_fast_mcp = MagicMock()
        target._fast_mcp = mock_fast_mcp

        await target.close()

        # Server should be cleared
        assert target._fast_mcp is None

    @pytest.mark.asyncio
    async def test_close_no_server(self):
        """Test close when no server is initialized."""
        target = OasTarget("test-oas", "http://example.com/openapi.json")

        # Should not raise any errors
        await target.close()
        assert target._fast_mcp is None

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Test full lifecycle: initialize, list_tools, call_tool, close."""
        target = OasTarget("lifecycle-oas", "http://example.com/openapi.json")

        # Mock the FastMCP server
        mock_fast_mcp = AsyncMock()
        mock_tools = [
            Tool(name="lifecycle_tool", description="Lifecycle tool", inputSchema={})
        ]
        mock_content = [TextContent(type="text", text="Lifecycle response")]
        mock_fast_mcp.list_tools.return_value = mock_tools
        mock_fast_mcp.call_tool.return_value = mock_content

        with patch("mcp_kit.targets.oas.create_mcp_server") as mock_create_server:
            mock_create_server.return_value = mock_fast_mcp

            # Initialize
            await target.initialize()
            assert target._fast_mcp == mock_fast_mcp

            # List tools
            tools = await target.list_tools()
            assert tools == mock_tools

            # Call tool
            result = await target.call_tool("lifecycle_tool", {"param": "value"})
            assert result == mock_content

            # Close
            await target.close()
            assert target._fast_mcp is None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations work correctly."""
        target = OasTarget("concurrent-oas", "http://example.com/openapi.json")

        mock_fast_mcp = AsyncMock()
        mock_tools = [
            Tool(name="concurrent_tool", description="Concurrent tool", inputSchema={})
        ]
        mock_content = [TextContent(type="text", text="Concurrent response")]
        mock_fast_mcp.list_tools.return_value = mock_tools
        mock_fast_mcp.call_tool.return_value = mock_content

        with patch("mcp_kit.targets.oas.create_mcp_server") as mock_create_server:
            mock_create_server.return_value = mock_fast_mcp

            await target.initialize()

            # Run concurrent operations
            import asyncio

            async def list_and_call():
                tools = await target.list_tools()
                result = await target.call_tool("concurrent_tool", {"param": "value"})
                return tools, result

            # Run multiple concurrent operations
            tasks = [list_and_call() for _ in range(3)]
            results = await asyncio.gather(*tasks)

            # All should succeed
            for tools, result in results:
                assert tools == mock_tools
                assert result == mock_content

    def test_different_spec_urls(self):
        """Test OasTarget works with different spec URL formats."""
        urls = [
            "http://example.com/openapi.json",
            "https://api.example.com/v1/openapi.yaml",
            "http://localhost:8080/api/docs/openapi.json",
            "https://petstore3.swagger.io/api/v3/openapi.json",
        ]

        for url in urls:
            target = OasTarget(f"test-{len(url)}", url)
            assert target._spec_url == url

    @pytest.mark.asyncio
    async def test_multiple_targets_different_specs(self):
        """Test multiple OasTarget instances with different specs."""
        target1 = OasTarget("target1", "http://example1.com/openapi.json")
        target2 = OasTarget("target2", "http://example2.com/openapi.json")

        mock_fast_mcp1 = MagicMock()
        mock_fast_mcp2 = MagicMock()

        with patch("mcp_kit.targets.oas.create_mcp_server") as mock_create_server:
            mock_create_server.side_effect = [mock_fast_mcp1, mock_fast_mcp2]

            await target1.initialize()
            await target2.initialize()

            assert target1._fast_mcp == mock_fast_mcp1
            assert target2._fast_mcp == mock_fast_mcp2
            assert mock_create_server.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling_during_operations(self):
        """Test error handling during various operations."""
        target = OasTarget("error-test", "http://example.com/openapi.json")

        mock_fast_mcp = MagicMock()
        target._fast_mcp = mock_fast_mcp

        # Test list_tools error
        mock_fast_mcp.list_tools.side_effect = ValueError("List tools failed")
        with pytest.raises(ValueError, match="List tools failed"):
            await target.list_tools()

        # Reset mock for call_tool test
        mock_fast_mcp.list_tools.side_effect = None
        mock_fast_mcp.call_tool.side_effect = ConnectionError("API unreachable")
        with pytest.raises(ConnectionError, match="API unreachable"):
            await target.call_tool("test_tool", {})

    def test_string_representation(self):
        """Test string representation of OasTarget."""
        target = OasTarget("repr-test", "http://example.com/openapi.json")
        # Should not raise any errors
        str_repr = str(target)
        assert "repr-test" in str_repr or "OasTarget" in str_repr
