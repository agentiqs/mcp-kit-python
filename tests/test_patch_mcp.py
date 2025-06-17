"""Tests for patch_mcp module."""

from contextlib import AsyncExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import ClientSession

from mcp_kit.patch_mcp import http_streamable_session


class TestHttpStreamableSession:
    """Test cases for http_streamable_session function."""

    @pytest.mark.asyncio
    async def test_http_streamable_session_success(self):
        """Test successful creation of HTTP streamable session."""
        # Mock the dependencies
        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_session = MagicMock(spec=ClientSession)
        mock_session.initialize = AsyncMock()

        with (
            patch("mcp_kit.patch_mcp.streamablehttp_client") as mock_streamable_client,
            patch("mcp_kit.patch_mcp.ClientSession") as mock_client_session_class,
        ):
            # Setup the mock context manager for streamablehttp_client
            mock_streamable_client.return_value.__aenter__ = AsyncMock(
                return_value=(mock_read, mock_write, "extra1", "extra2")
            )
            mock_streamable_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Setup the mock context manager for ClientSession
            mock_client_session_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session_class.return_value.__aexit__ = AsyncMock(
                return_value=None
            )

            # Call the function
            session, exit_stack = await http_streamable_session(
                url="http://test.com", headers={"Authorization": "Bearer token"}
            )

            # Verify the results
            assert session == mock_session
            assert isinstance(exit_stack, AsyncExitStack)

            # Verify the function calls
            mock_streamable_client.assert_called_once_with(
                url="http://test.com", headers={"Authorization": "Bearer token"}
            )
            mock_client_session_class.assert_called_once_with(mock_read, mock_write)
            mock_session.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_streamable_session_without_headers(self):
        """Test HTTP streamable session creation without headers."""
        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_session = MagicMock(spec=ClientSession)
        mock_session.initialize = AsyncMock()

        with (
            patch("mcp_kit.patch_mcp.streamablehttp_client") as mock_streamable_client,
            patch("mcp_kit.patch_mcp.ClientSession") as mock_client_session_class,
        ):
            # Setup the mock context manager for streamablehttp_client
            mock_streamable_client.return_value.__aenter__ = AsyncMock(
                return_value=(mock_read, mock_write)
            )
            mock_streamable_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Setup the mock context manager for ClientSession
            mock_client_session_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session_class.return_value.__aexit__ = AsyncMock(
                return_value=None
            )

            # Call the function with None headers
            session, exit_stack = await http_streamable_session(
                url="http://test.com", headers=None
            )

            # Verify the results
            assert session == mock_session
            assert isinstance(exit_stack, AsyncExitStack)

            # Verify headers were passed as None
            mock_streamable_client.assert_called_once_with(
                url="http://test.com", headers=None
            )

    @pytest.mark.asyncio
    async def test_http_streamable_session_streamable_client_error(self):
        """Test HTTP streamable session when streamablehttp_client fails."""
        with patch("mcp_kit.patch_mcp.streamablehttp_client") as mock_streamable_client:
            # Make streamablehttp_client raise an exception
            mock_streamable_client.side_effect = ConnectionError("Connection failed")

            with pytest.raises(ConnectionError, match="Connection failed"):
                await http_streamable_session(
                    url="http://test.com", headers={"Authorization": "Bearer token"}
                )

    @pytest.mark.asyncio
    async def test_http_streamable_session_client_session_error(self):
        """Test HTTP streamable session when ClientSession fails."""
        mock_read = MagicMock()
        mock_write = MagicMock()

        with (
            patch("mcp_kit.patch_mcp.streamablehttp_client") as mock_streamable_client,
            patch("mcp_kit.patch_mcp.ClientSession") as mock_client_session_class,
        ):
            # Setup successful streamablehttp_client
            mock_streamable_client.return_value.__aenter__ = AsyncMock(
                return_value=(mock_read, mock_write)
            )
            mock_streamable_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Make ClientSession raise an exception
            mock_client_session_class.side_effect = RuntimeError("ClientSession failed")

            with pytest.raises(RuntimeError, match="ClientSession failed"):
                await http_streamable_session(url="http://test.com", headers=None)

    @pytest.mark.asyncio
    async def test_http_streamable_session_initialize_error(self):
        """Test HTTP streamable session when session.initialize fails."""
        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_session = MagicMock(spec=ClientSession)
        mock_session.initialize = AsyncMock(
            side_effect=RuntimeError("Initialize failed")
        )

        with (
            patch("mcp_kit.patch_mcp.streamablehttp_client") as mock_streamable_client,
            patch("mcp_kit.patch_mcp.ClientSession") as mock_client_session_class,
        ):
            # Setup the mock context manager for streamablehttp_client
            mock_streamable_client.return_value.__aenter__ = AsyncMock(
                return_value=(mock_read, mock_write)
            )
            mock_streamable_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Setup the mock context manager for ClientSession
            mock_client_session_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session_class.return_value.__aexit__ = AsyncMock(
                return_value=None
            )

            with pytest.raises(RuntimeError, match="Initialize failed"):
                await http_streamable_session(url="http://test.com", headers=None)
