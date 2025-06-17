"""Tests for MCP target implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import Tool
from mcp.types import TextContent
from omegaconf import OmegaConf

from mcp_kit.targets.mcp import McpTarget


class TestMcpTarget:
    """Test cases for McpTarget class."""

    def test_init_with_url(self):
        """Test McpTarget initialization with URL."""
        target = McpTarget(
            name="test-mcp",
            url="http://example.com/mcp",
            headers={"Authorization": "Bearer token"},
        )
        assert target.name == "test-mcp"
        assert target.url == "http://example.com/mcp"
        assert target.headers == {"Authorization": "Bearer token"}
        assert target.tools is None
        assert target.target_mcp is None
        assert target.target_mcp_exit_stack is None

    def test_init_with_tools(self):
        """Test McpTarget initialization with predefined tools."""
        tools = [Tool(name="test_tool", description="A test tool", inputSchema={})]
        target = McpTarget(name="test-mcp", tools=tools)
        assert target.name == "test-mcp"
        assert target.url is None
        assert target.headers is None
        assert target.tools == tools

    def test_init_minimal(self):
        """Test McpTarget initialization with minimal parameters."""
        target = McpTarget(name="minimal-mcp")
        assert target.name == "minimal-mcp"
        assert target.url is None
        assert target.headers is None
        assert target.tools is None

    def test_from_config_with_url(self):
        """Test McpTarget.from_config with URL configuration."""
        config = OmegaConf.create(
            {
                "type": "mcp",
                "name": "config-mcp",
                "url": "http://example.com/mcp",
                "headers": {"Authorization": "Bearer config-token"},
            }
        )

        target = McpTarget.from_config(config)
        assert target.name == "config-mcp"
        assert target.url == "http://example.com/mcp"
        assert target.headers == {"Authorization": "Bearer config-token"}

    def test_from_config_with_tools(self):
        """Test McpTarget.from_config with tools configuration."""
        config = OmegaConf.create(
            {
                "type": "mcp",
                "name": "config-mcp",
                "tools": [{"name": "config_tool", "description": "A tool from config"}],
            }
        )

        with patch("mcp_kit.targets.mcp.create_tools_from_config") as mock_create_tools:
            mock_tools = [
                Tool(
                    name="config_tool", description="A tool from config", inputSchema={}
                )
            ]
            mock_create_tools.return_value = mock_tools

            target = McpTarget.from_config(config)
            assert target.name == "config-mcp"
            assert target.tools == mock_tools
            mock_create_tools.assert_called_once_with(config)

    def test_from_config_minimal(self):
        """Test McpTarget.from_config with minimal configuration."""
        config = OmegaConf.create({"type": "mcp", "name": "minimal-config-mcp"})

        target = McpTarget.from_config(config)
        assert target.name == "minimal-config-mcp"
        assert target.url is None
        assert target.headers is None
        assert target.tools is None

    @pytest.mark.asyncio
    async def test_initialize_with_predefined_tools(self):
        """Test initialize when tools are predefined."""
        tools = [
            Tool(name="predefined_tool", description="Predefined tool", inputSchema={})
        ]
        target = McpTarget(name="test-mcp", tools=tools)

        await target.initialize()
        # Should not set up any MCP connection when tools are predefined
        assert target.target_mcp is None
        assert target.target_mcp_exit_stack is None

    @pytest.mark.asyncio
    async def test_initialize_with_url(self):
        """Test initialize with URL (sets up MCP connection)."""
        target = McpTarget(
            name="test-mcp",
            url="http://example.com/mcp",
            headers={"Authorization": "Bearer token"},
        )

        mock_session = MagicMock()
        mock_exit_stack = MagicMock()

        with patch("mcp_kit.targets.mcp.http_streamable_session") as mock_http_session:
            mock_http_session.return_value = (mock_session, mock_exit_stack)

            await target.initialize()

            assert target.target_mcp == mock_session
            assert target.target_mcp_exit_stack == mock_exit_stack
            mock_http_session.assert_called_once_with(
                "http://example.com/mcp", {"Authorization": "Bearer token"}
            )

    @pytest.mark.asyncio
    async def test_initialize_without_url_or_tools(self):
        """Test initialize without URL or tools."""
        target = McpTarget(name="test-mcp")

        await target.initialize()
        # Should not set up any MCP connection
        assert target.target_mcp is None
        assert target.target_mcp_exit_stack is None

    @pytest.mark.asyncio
    async def test_list_tools_with_predefined_tools(self):
        """Test list_tools with predefined tools."""
        tools = [
            Tool(name="tool1", description="First tool", inputSchema={}),
            Tool(name="tool2", description="Second tool", inputSchema={}),
        ]
        target = McpTarget(name="test-mcp", tools=tools)

        result = await target.list_tools()
        assert result == tools

    @pytest.mark.asyncio
    async def test_list_tools_from_mcp_server(self):
        """Test list_tools from MCP server."""
        target = McpTarget(name="test-mcp", url="http://example.com/mcp")

        mock_session = AsyncMock()
        mock_tools = [
            Tool(name="server_tool", description="Tool from server", inputSchema={})
        ]
        mock_session.list_tools.return_value.tools = mock_tools
        target.target_mcp = mock_session

        result = await target.list_tools()
        assert result == mock_tools
        mock_session.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_no_mcp_session(self):
        """Test list_tools when no MCP session is available."""
        target = McpTarget(name="test-mcp")

        with pytest.raises(ValueError, match="No tools available"):
            await target.list_tools()

    @pytest.mark.asyncio
    async def test_call_tool_with_predefined_tools(self):
        """Test call_tool with predefined tools (should raise error)."""
        tools = [
            Tool(name="predefined_tool", description="Predefined tool", inputSchema={})
        ]
        target = McpTarget(name="test-mcp", tools=tools)

        with pytest.raises(ValueError, match="MCP client is not initialized"):
            await target.call_tool("predefined_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_from_mcp_server(self):
        """Test call_tool from MCP server."""
        target = McpTarget(name="test-mcp", url="http://example.com/mcp")

        mock_session = AsyncMock()
        mock_content = [TextContent(type="text", text="Tool response")]
        mock_session.call_tool.return_value.content = mock_content
        target.target_mcp = mock_session

        result = await target.call_tool("server_tool", {"param": "value"})
        assert result == mock_content
        mock_session.call_tool.assert_called_once_with(
            name="server_tool", arguments={"param": "value"}
        )

    @pytest.mark.asyncio
    async def test_call_tool_no_mcp_session(self):
        """Test call_tool when no MCP session is available."""
        target = McpTarget(name="test-mcp")

        with pytest.raises(ValueError, match="MCP client is not initialized"):
            await target.call_tool("some_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_close_with_exit_stack(self):
        """Test close when exit stack is available."""
        target = McpTarget(name="test-mcp")

        mock_exit_stack = AsyncMock()
        target.target_mcp_exit_stack = mock_exit_stack

        await target.close()
        mock_exit_stack.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_exit_stack(self):
        """Test close when no exit stack is available."""
        target = McpTarget(name="test-mcp")

        # Should not raise any errors
        await target.close()
        assert target.target_mcp is None
        assert target.target_mcp_exit_stack is None

    @pytest.mark.asyncio
    async def test_full_lifecycle_with_url(self):
        """Test full lifecycle: initialize, list_tools, call_tool, close."""
        target = McpTarget(
            name="lifecycle-mcp",
            url="http://example.com/mcp",
            headers={"Auth": "token"},
        )

        mock_session = AsyncMock()
        mock_exit_stack = AsyncMock()
        mock_tools = [
            Tool(name="lifecycle_tool", description="Lifecycle tool", inputSchema={})
        ]
        mock_content = [TextContent(type="text", text="Lifecycle response")]

        mock_session.list_tools.return_value.tools = mock_tools
        mock_session.call_tool.return_value.content = mock_content

        with patch("mcp_kit.targets.mcp.http_streamable_session") as mock_http_session:
            mock_http_session.return_value = (mock_session, mock_exit_stack)

            # Initialize
            await target.initialize()
            assert target.target_mcp == mock_session

            # List tools
            tools = await target.list_tools()
            assert tools == mock_tools

            # Call tool
            result = await target.call_tool("lifecycle_tool", {"test": "param"})
            assert result == mock_content

            # Close
            await target.close()
            mock_exit_stack.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_connection_error(self):
        """Test initialize handles connection errors properly."""
        target = McpTarget(name="test-mcp", url="http://example.com/mcp")

        with patch("mcp_kit.targets.mcp.http_streamable_session") as mock_http_session:
            mock_http_session.side_effect = ConnectionError("Failed to connect")

            with pytest.raises(ConnectionError, match="Failed to connect"):
                await target.initialize()

    @pytest.mark.asyncio
    async def test_name_property(self):
        """Test name property."""
        target = McpTarget(name="property-test")
        assert target.name == "property-test"

    def test_repr_and_str(self):
        """Test string representation of McpTarget."""
        target = McpTarget(name="repr-test", url="http://example.com")
        # Should not raise any errors
        str_repr = str(target)
        assert "repr-test" in str_repr or "McpTarget" in str_repr
