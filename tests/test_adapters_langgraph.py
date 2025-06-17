"""Tests for LangGraph adapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_kit.adapters.client_session import ClientSessionAdapter
from mcp_kit.adapters.langgraph import LangGraphMultiServerMCPClient
from mcp_kit.targets.interfaces import Target


@pytest.fixture
def mock_target():
    """Create a mock target for testing."""
    target = MagicMock(spec=Target)
    target.name = "test-langgraph-target"
    target.initialize = AsyncMock()
    target.close = AsyncMock()
    target.list_tools = AsyncMock()
    target.call_tool = AsyncMock()
    return target


@pytest.fixture
def mock_load_mcp_tools():
    """Mock the load_mcp_tools function."""
    return MagicMock()


class TestLangGraphMultiServerMCPClient:
    """Test cases for LangGraphMultiServerMCPClient."""

    def test_init_success(self, mock_target, monkeypatch):
        """Test successful initialization with langchain_mcp_adapters available."""
        # Mock the import
        mock_load_mcp_tools = MagicMock()

        def mock_import(module_name):
            if module_name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            raise ImportError(f"No module named '{module_name}'")

        # Patch the import mechanism
        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        client = LangGraphMultiServerMCPClient(mock_target)
        assert client.target == mock_target
        assert client._session is None

    def test_init_missing_dependency(self, mock_target, monkeypatch):
        """Test initialization failure when langchain_mcp_adapters is not available."""
        # Mock the import to raise ImportError
        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                raise ImportError("No module named 'langchain_mcp_adapters'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        with pytest.raises(
            ImportError, match="langchain_mcp_adapters.*package is required"
        ):
            LangGraphMultiServerMCPClient(mock_target)

    @pytest.mark.asyncio
    async def test_session_success(self, mock_target, monkeypatch):
        """Test successful session creation."""
        # Setup mock for langchain_mcp_adapters
        mock_load_mcp_tools = MagicMock()

        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        client = LangGraphMultiServerMCPClient(mock_target)

        async with client.session("test-langgraph-target") as session:
            assert isinstance(session, ClientSessionAdapter)
            assert session.target == mock_target
            mock_target.initialize.assert_called_once()

        # After exiting context, target should be closed and session cleared
        mock_target.close.assert_called_once()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_session_wrong_server_name(self, mock_target, monkeypatch):
        """Test session creation with wrong server name."""
        # Setup mock for langchain_mcp_adapters
        mock_load_mcp_tools = MagicMock()

        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        client = LangGraphMultiServerMCPClient(mock_target)

        with pytest.raises(
            ValueError, match="Couldn't find a server with name 'wrong-name'"
        ):
            async with client.session("wrong-name"):
                pass

    @pytest.mark.asyncio
    async def test_session_no_auto_initialize(self, mock_target, monkeypatch):
        """Test session creation without auto-initialization."""
        # Setup mock for langchain_mcp_adapters
        mock_load_mcp_tools = MagicMock()

        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        client = LangGraphMultiServerMCPClient(mock_target)

        async with client.session(
            "test-langgraph-target", auto_initialize=False
        ) as session:
            assert isinstance(session, ClientSessionAdapter)
            assert session.target == mock_target
            # Should not call initialize when auto_initialize=False
            mock_target.initialize.assert_not_called()

        # Should still call close
        mock_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_exception_during_context(self, mock_target, monkeypatch):
        """Test session cleanup when exception occurs during context execution."""
        # Setup mock for langchain_mcp_adapters
        mock_load_mcp_tools = MagicMock()

        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        client = LangGraphMultiServerMCPClient(mock_target)

        with pytest.raises(RuntimeError, match="Test exception"):
            async with client.session("test-langgraph-target") as session:
                assert isinstance(session, ClientSessionAdapter)
                raise RuntimeError("Test exception")

        # Should still call close even if exception occurred
        mock_target.close.assert_called_once()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_get_tools_method(self, mock_target, monkeypatch):
        """Test get_tools method functionality."""
        # Setup mock for langchain_mcp_adapters
        mock_load_mcp_tools = AsyncMock()
        mock_tools = ["tool1", "tool2"]
        mock_load_mcp_tools.return_value = mock_tools

        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        client = LangGraphMultiServerMCPClient(mock_target)

        result = await client.get_tools(server_name="test-langgraph-target")

        assert result == mock_tools
        mock_load_mcp_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tools_no_server_name(self, mock_target, monkeypatch):
        """Test get_tools method without server name validation."""
        # Setup mock for langchain_mcp_adapters
        mock_load_mcp_tools = AsyncMock()
        mock_tools = ["tool1", "tool2"]
        mock_load_mcp_tools.return_value = mock_tools

        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        client = LangGraphMultiServerMCPClient(mock_target)

        result = await client.get_tools()

        assert result == mock_tools
        mock_target.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tools_wrong_server_name(self, mock_target, monkeypatch):
        """Test get_tools method with wrong server name."""
        # Setup mock for langchain_mcp_adapters
        mock_load_mcp_tools = AsyncMock()

        import builtins

        original_import = builtins.__import__

        def patched_import(name, *args, **kwargs):
            if name == "langchain_mcp_adapters.tools":
                mock_module = MagicMock()
                mock_module.load_mcp_tools = mock_load_mcp_tools
                return mock_module
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched_import)

        client = LangGraphMultiServerMCPClient(mock_target)

        with pytest.raises(
            ValueError, match="Couldn't find a server with name 'wrong-name'"
        ):
            await client.get_tools(server_name="wrong-name")
