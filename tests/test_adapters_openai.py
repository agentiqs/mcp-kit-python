"""Tests for OpenAI Agents SDK adapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp import Tool
from mcp.types import CallToolResult, TextContent

from mcp_kit.adapters.openai import OpenAIMCPServerAdapter
from mcp_kit.targets.interfaces import Target


@pytest.fixture
def mock_target():
    """Create a mock target for testing."""
    target = MagicMock(spec=Target)
    target.name = "test-openai-target"
    target.initialize = AsyncMock()
    target.close = AsyncMock()
    target.list_tools = AsyncMock()
    target.call_tool = AsyncMock()
    return target


@pytest.fixture
def openai_adapter(mock_target):
    """Create an OpenAIMCPServerAdapter instance for testing."""
    return OpenAIMCPServerAdapter(mock_target)


class TestOpenAIMCPServerAdapter:
    """Test cases for OpenAIMCPServerAdapter."""

    def test_init(self, mock_target):
        """Test adapter initialization."""
        adapter = OpenAIMCPServerAdapter(mock_target)
        assert adapter.target == mock_target

    @pytest.mark.asyncio
    async def test_connect(self, openai_adapter, mock_target):
        """Test connect method."""
        await openai_adapter.connect()
        mock_target.initialize.assert_called_once()

    def test_name_property(self, openai_adapter, mock_target):
        """Test name property."""
        assert openai_adapter.name == "test-openai-target"

    @pytest.mark.asyncio
    async def test_cleanup(self, openai_adapter, mock_target):
        """Test cleanup method."""
        await openai_adapter.cleanup()
        mock_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools(self, openai_adapter, mock_target):
        """Test list_tools method."""
        expected_tools = [
            Tool(name="test_tool", description="A test tool", inputSchema={}),
            Tool(name="another_tool", description="Another test tool", inputSchema={}),
        ]
        mock_target.list_tools.return_value = expected_tools

        result = await openai_adapter.list_tools()

        assert result == expected_tools
        mock_target.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_empty(self, openai_adapter, mock_target):
        """Test list_tools with empty result."""
        mock_target.list_tools.return_value = []

        result = await openai_adapter.list_tools()

        assert result == []
        mock_target.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_success(self, openai_adapter, mock_target):
        """Test successful call_tool."""
        expected_content = [TextContent(type="text", text="Tool response")]
        mock_target.call_tool.return_value = expected_content

        result = await openai_adapter.call_tool("test_tool", {"arg": "value"})

        assert isinstance(result, CallToolResult)
        assert result.content == expected_content
        assert result.isError is False
        mock_target.call_tool.assert_called_once_with(
            name="test_tool", arguments={"arg": "value"}
        )

    @pytest.mark.asyncio
    async def test_call_tool_with_none_arguments(self, openai_adapter, mock_target):
        """Test call_tool with None arguments."""
        expected_content = [TextContent(type="text", text="Tool response")]
        mock_target.call_tool.return_value = expected_content

        result = await openai_adapter.call_tool("test_tool", None)

        assert isinstance(result, CallToolResult)
        assert result.content == expected_content
        assert result.isError is False
        mock_target.call_tool.assert_called_once_with(name="test_tool", arguments=None)

    @pytest.mark.asyncio
    async def test_call_tool_exception_handling(self, openai_adapter, mock_target):
        """Test call_tool with exception handling."""
        error_message = "Tool execution failed"
        mock_target.call_tool.side_effect = Exception(error_message)

        result = await openai_adapter.call_tool("failing_tool", {"param": "value"})

        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        assert error_message in result.content[0].text

    @pytest.mark.asyncio
    async def test_call_tool_runtime_error(self, openai_adapter, mock_target):
        """Test call_tool with RuntimeError."""
        error_message = "Runtime error occurred"
        mock_target.call_tool.side_effect = RuntimeError(error_message)

        result = await openai_adapter.call_tool("error_tool", {})

        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        assert error_message in result.content[0].text

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, openai_adapter, mock_target):
        """Test full adapter lifecycle: connect, list_tools, call_tool, cleanup."""
        # Setup
        tools = [Tool(name="lifecycle_tool", description="Test tool", inputSchema={})]
        mock_target.list_tools.return_value = tools
        mock_target.call_tool.return_value = [TextContent(type="text", text="Success")]

        # Connect
        await openai_adapter.connect()
        mock_target.initialize.assert_called_once()

        # List tools
        result_tools = await openai_adapter.list_tools()
        assert result_tools == tools

        # Call tool
        result = await openai_adapter.call_tool("lifecycle_tool", {"test": "param"})
        assert result.isError is False

        # Cleanup
        await openai_adapter.cleanup()
        mock_target.close.assert_called_once()
