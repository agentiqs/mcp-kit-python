"""Utility functions for MCP client connections."""

from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def http_streamable_session(url: str, headers: dict[str, Any] | None) -> tuple[ClientSession, AsyncExitStack]:
    """Create an HTTP streamable MCP client session.

    Establishes a connection to an MCP server over HTTP and returns both
    the session and the exit stack for proper cleanup.

    :param url: URL of the MCP server
    :param headers: Optional HTTP headers to include in requests
    :return: Tuple of (ClientSession, AsyncExitStack) for the connection
    """
    exit_stack = AsyncExitStack()
    read, write, *_ = await exit_stack.enter_async_context(streamablehttp_client(url=url, headers=headers))
    mcp_session = await exit_stack.enter_async_context(ClientSession(read, write))
    await mcp_session.initialize()

    return mcp_session, exit_stack
