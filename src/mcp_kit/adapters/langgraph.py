"""LangGraph adapter for MCP targets."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_mcp_adapters.tools import BaseTool  # type: ignore[import-untyped]

from mcp_kit.adapters.client_session import ClientSessionAdapter
from mcp_kit.targets.interfaces import Target


class LangGraphMultiServerMCPClient:
    """Adapter class for LangGraph compatibility with MCP targets.

    This adapter provides an interface similar to MultiServerMCPClient from
    langchain-mcp-adapters, allowing MCP targets to be used with LangGraph workflows.
    """

    def __init__(self, target: Target):
        """Initialize the LangGraph MCP client adapter.

        :param target: The MCP target to adapt for LangGraph use
        :raises ImportError: If langchain_mcp_adapters is not installed
        """
        try:
            from langchain_mcp_adapters.tools import load_mcp_tools

            self._load_mcp_tools = load_mcp_tools
        except ImportError as e:
            raise ImportError(
                "The 'langchain_mcp_adapters' package is required for LangGraphMultiServerMCPClient. "
                "Please install it with 'pip install mcp-kit[langgraph]'.",
            ) from e

        self.target = target
        self._session: ClientSessionAdapter | None = None

    @asynccontextmanager
    async def session(
        self,
        server_name: str,
        *,
        auto_initialize: bool = True,
    ) -> AsyncIterator[Any]:
        """Create a new client session for the specified server.

        :param server_name: Name of the server to connect to
        :param auto_initialize: Whether to automatically initialize the target
        :yield: ClientSessionAdapter for the target
        :raises ValueError: If the server name doesn't match the target name
        """
        if self.target.name != server_name:
            raise ValueError(
                f"Couldn't find a server with name '{server_name}', expected '{self.target.name}'",
            )
        try:
            if auto_initialize:
                await self.target.initialize()
            self._session = ClientSessionAdapter(self.target)
            yield self._session
        finally:
            await self.target.close()
            self._session = None

    async def get_tools(self, *, server_name: str | None = None) -> list[BaseTool]:
        """Get LangChain tools from the MCP server.

        Converts MCP tools to LangChain-compatible tools using the langchain_mcp_adapters.

        :param server_name: Optional server name to validate against
        :return: List of LangChain tools
        :raises ValueError: If the server name doesn't match the target name
        """
        # The session is kept alive by the context manager
        if server_name is not None:
            if self.target.name != server_name:
                raise ValueError(
                    f"Couldn't find a server with name '{server_name}', expected one of '{self.target.name}'",
                )

        if self._session is None:
            await self.target.initialize()
            self._session = ClientSessionAdapter(self.target)
        # Use load_mcp_tools to convert MCP tools to LangChain tools
        return await self._load_mcp_tools(self._session)  # type: ignore
