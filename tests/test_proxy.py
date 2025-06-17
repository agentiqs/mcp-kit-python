"""Tests for ProxyMCP class."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from mcp import Tool
from mcp.server import Server
from mcp.types import TextContent

from mcp_kit.adapters import (
    ClientSessionAdapter,
    LangGraphMultiServerMCPClient,
    OpenAIMCPServerAdapter,
)
from mcp_kit import ProxyMCP
from mcp_kit.targets.interfaces import Target


@pytest.fixture
def mock_target():
    """Create a mock target for testing."""
    target = MagicMock(spec=Target)
    target.name = "test-proxy-target"
    target.initialize = AsyncMock()
    target.close = AsyncMock()
    target.list_tools = AsyncMock()
    target.call_tool = AsyncMock()
    return target


@pytest.fixture
def proxy_mcp(mock_target):
    """Create a ProxyMCP instance for testing."""
    return ProxyMCP(mock_target)


class TestProxyMCP:
    """Test cases for ProxyMCP class."""

    def test_init(self, mock_target):
        """Test ProxyMCP initialization."""
        proxy = ProxyMCP(mock_target)
        assert proxy.target == mock_target

    def test_from_config_yaml(self):
        """Test ProxyMCP.from_config with YAML file."""
        config_data = {
            "target": {
                "type": "mcp",
                "name": "test-mcp",
                "url": "http://example.com/mcp",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            assert proxy.target.name == "test-mcp"
        finally:
            Path(config_file).unlink()

    def test_from_config_json(self):
        """Test ProxyMCP.from_config with JSON file."""
        config_data = {
            "target": {
                "type": "mcp",
                "name": "test-mcp-json",
                "url": "http://example.com/mcp",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            assert proxy.target.name == "test-mcp-json"
        finally:
            Path(config_file).unlink()

    def test_from_config_pathlib_path(self):
        """Test ProxyMCP.from_config with pathlib.Path."""
        config_data = {
            "target": {
                "type": "mcp",
                "name": "test-mcp-path",
                "url": "http://example.com/mcp",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = Path(f.name)

        try:
            proxy = ProxyMCP.from_config(config_file)
            assert proxy.target.name == "test-mcp-path"
        finally:
            config_file.unlink()

    @pytest.mark.asyncio
    async def test_client_session_adapter_context_manager(self, proxy_mcp, mock_target):
        """Test client_session_adapter context manager."""
        async with proxy_mcp.client_session_adapter() as adapter:
            assert isinstance(adapter, ClientSessionAdapter)
            assert adapter.target == mock_target
            mock_target.initialize.assert_called_once()

        # After exiting context, target should be closed
        mock_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_session_adapter_exception_handling(
        self, proxy_mcp, mock_target
    ):
        """Test client_session_adapter exception handling."""
        with pytest.raises(RuntimeError, match="Test exception"):
            async with proxy_mcp.client_session_adapter() as adapter:
                assert isinstance(adapter, ClientSessionAdapter)
                raise RuntimeError("Test exception")

        # Should still call close even if exception occurred
        mock_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_agents_mcp_server_context_manager(
        self, proxy_mcp, mock_target
    ):
        """Test openai_agents_mcp_server context manager."""
        async with proxy_mcp.openai_agents_mcp_server() as adapter:
            assert isinstance(adapter, OpenAIMCPServerAdapter)
            assert adapter.target == mock_target
            mock_target.initialize.assert_called_once()

        # After exiting context, target should be closed
        mock_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_agents_mcp_server_exception_handling(
        self, proxy_mcp, mock_target
    ):
        """Test openai_agents_mcp_server exception handling."""
        with pytest.raises(RuntimeError, match="Test exception"):
            async with proxy_mcp.openai_agents_mcp_server() as adapter:
                assert isinstance(adapter, OpenAIMCPServerAdapter)
                raise RuntimeError("Test exception")

        # Should still call close even if exception occurred
        mock_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_official_mcp_server_context_manager(self, proxy_mcp, mock_target):
        """Test official_mcp_server context manager."""
        # Setup mock tools and responses
        mock_tools = [Tool(name="test_tool", description="Test tool", inputSchema={})]
        mock_content = [TextContent(type="text", text="Tool response")]
        mock_target.list_tools.return_value = mock_tools
        mock_target.call_tool.return_value = mock_content

        async with proxy_mcp.official_mcp_server() as server:
            assert isinstance(server, Server)
            assert server.name == "test-proxy-target"
            mock_target.initialize.assert_called_once()

        # After exiting context, target should be closed
        mock_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_official_mcp_server_exception_handling(self, proxy_mcp, mock_target):
        """Test official_mcp_server exception handling."""
        with pytest.raises(RuntimeError, match="Test exception"):
            async with proxy_mcp.official_mcp_server() as server:
                assert isinstance(server, Server)
                raise RuntimeError("Test exception")

        # Should still call close even if exception occurred
        mock_target.close.assert_called_once()

    def test_langgraph_multi_server_mcp_client(self, proxy_mcp, mock_target):
        """Test langgraph_multi_server_mcp_client method."""
        client = proxy_mcp.langgraph_multi_server_mcp_client()
        assert isinstance(client, LangGraphMultiServerMCPClient)
        assert client.target == mock_target

    @pytest.mark.asyncio
    async def test_integration_flow(self, proxy_mcp, mock_target):
        """Test a complete integration flow using multiple adapters."""
        # Setup mock responses
        mock_tools = [
            Tool(
                name="integration_tool",
                description="Integration test tool",
                inputSchema={},
            )
        ]
        mock_content = [TextContent(type="text", text="Integration response")]
        mock_target.list_tools.return_value = mock_tools
        mock_target.call_tool.return_value = mock_content

        # Test client session adapter
        async with proxy_mcp.client_session_adapter() as client_adapter:
            tools_result = await client_adapter.list_tools()
            assert tools_result.tools == mock_tools

            call_result = await client_adapter.call_tool(
                "integration_tool", {"param": "value"}
            )
            assert call_result.content == mock_content
            assert call_result.isError is False

        # Test OpenAI agents adapter
        async with proxy_mcp.openai_agents_mcp_server() as openai_adapter:
            tools = await openai_adapter.list_tools()
            assert tools == mock_tools

            result = await openai_adapter.call_tool(
                "integration_tool", {"param": "value"}
            )
            assert result.content == mock_content
            assert result.isError is False

        # Test LangGraph client (doesn't require context manager)
        langgraph_client = proxy_mcp.langgraph_multi_server_mcp_client()
        assert langgraph_client.target == mock_target

        # Verify target was properly cleaned up after each adapter usage
        assert mock_target.close.call_count == 2  # Called twice (client + openai)

    def test_proxy_mcp_with_different_target_types(self):
        """Test ProxyMCP works with different target types via configuration."""
        # Test with OAS target
        oas_config_data = {
            "target": {
                "type": "oas",
                "name": "test-oas",
                "spec_url": "http://example.com/openapi.json",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(oas_config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            assert proxy.target.name == "test-oas"
        finally:
            Path(config_file).unlink()

        # Test with mocked target
        mocked_config_data = {
            "target": {
                "type": "mocked",
                "base_target": {
                    "type": "mcp",
                    "name": "base-mcp",
                    "url": "http://example.com/mcp",
                },
                "response_generator": {"type": "random"},
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(mocked_config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            # Should be a MockedTarget containing an McpTarget
            assert hasattr(
                proxy.target, "target"
            )  # MockedTarget has a target attribute
        finally:
            Path(config_file).unlink()
