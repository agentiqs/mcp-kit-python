"""Tests for ClientSessionAdapter class."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp import Tool
from mcp.types import CallToolResult, ListToolsResult, TextContent

from mcp_kit.adapters.client_session import ClientSessionAdapter
from mcp_kit.targets.interfaces import Target


@pytest.fixture
def mock_target():
    """Create a mock target for testing."""
    target = MagicMock(spec=Target)
    target.name = "test-target"
    target.initialize = AsyncMock()
    target.close = AsyncMock()
    target.list_tools = AsyncMock()
    target.call_tool = AsyncMock()
    return target


@pytest.fixture
def client_session_adapter(mock_target):
    """Create a ClientSessionAdapter instance for testing."""
    return ClientSessionAdapter(mock_target)


class TestClientSessionAdapter:
    """Test cases for ClientSessionAdapter."""

    def test_init(self, mock_target):
        """Test adapter initialization."""
        adapter = ClientSessionAdapter(mock_target)
        assert adapter.target == mock_target

    @pytest.mark.asyncio
    async def test_list_tools_success(self, client_session_adapter, mock_target):
        """Test successful list_tools call."""
        expected_tools = [
            Tool(name="test_tool", description="A test tool", inputSchema={}),
            Tool(name="another_tool", description="Another test tool", inputSchema={}),
        ]
        mock_target.list_tools.return_value = expected_tools

        result = await client_session_adapter.list_tools()

        assert isinstance(result, ListToolsResult)
        assert result.tools == expected_tools
        mock_target.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_empty(self, client_session_adapter, mock_target):
        """Test list_tools with empty tool list."""
        mock_target.list_tools.return_value = []

        result = await client_session_adapter.list_tools()

        assert isinstance(result, ListToolsResult)
        assert result.tools == []

    @pytest.mark.asyncio
    async def test_call_tool_success(self, client_session_adapter, mock_target):
        """Test successful tool call."""
        expected_content = [TextContent(type="text", text="Success response")]
        mock_target.call_tool.return_value = expected_content

        result = await client_session_adapter.call_tool("test_tool", {"arg1": "value1"})

        assert isinstance(result, CallToolResult)
        assert result.content == expected_content
        assert result.isError is False
        mock_target.call_tool.assert_called_once_with(
            name="test_tool", arguments={"arg1": "value1"}
        )

    @pytest.mark.asyncio
    async def test_call_tool_with_none_arguments(
        self, client_session_adapter, mock_target
    ):
        """Test tool call with None arguments."""
        expected_content = [TextContent(type="text", text="Success response")]
        mock_target.call_tool.return_value = expected_content

        result = await client_session_adapter.call_tool("test_tool", None)

        assert isinstance(result, CallToolResult)
        assert result.content == expected_content
        assert result.isError is False
        mock_target.call_tool.assert_called_once_with(name="test_tool", arguments=None)

    @pytest.mark.asyncio
    async def test_call_tool_exception_handling(
        self, client_session_adapter, mock_target
    ):
        """Test tool call with exception handling."""
        error_message = "Tool execution failed"
        mock_target.call_tool.side_effect = Exception(error_message)

        result = await client_session_adapter.call_tool("test_tool", {"arg1": "value1"})

        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        assert error_message in result.content[0].text
        assert "test_tool" in result.content[0].text

    @pytest.mark.asyncio
    async def test_call_tool_runtime_error(self, client_session_adapter, mock_target):
        """Test tool call with specific RuntimeError."""
        error_message = "Runtime error occurred"
        mock_target.call_tool.side_effect = RuntimeError(error_message)

        result = await client_session_adapter.call_tool("failing_tool", {})

        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        assert error_message in result.content[0].text
        assert "failing_tool" in result.content[0].text

    @pytest.mark.asyncio
    async def test_call_tool_value_error(self, client_session_adapter, mock_target):
        """Test tool call with ValueError."""
        error_message = "Invalid value provided"
        mock_target.call_tool.side_effect = ValueError(error_message)

        result = await client_session_adapter.call_tool(
            "bad_tool", {"invalid": "param"}
        )

        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        assert error_message in result.content[0].text
        assert "bad_tool" in result.content[0].text
        assert "invalid" in result.content[0].text
