"""Main proxy class for MCP Kit providing multiple adapter interfaces."""

import logging
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import Tool
from mcp.server import Server
from mcp.types import Content
from omegaconf import OmegaConf
from typing_extensions import Self

from mcp_kit.adapters import (
    ClientSessionAdapter,
    LangGraphMultiServerMCPClient,
    OpenAIMCPServerAdapter,
)
from mcp_kit.factory import create_target_from_config
from mcp_kit.targets import Target

logger = logging.getLogger(__name__)


class ProxyMCP:
    """Main proxy class for MCP Kit that provides multiple adapter interfaces.

    This class serves as the central entry point for MCP Kit, allowing a single
    MCP target to be exposed through various interfaces including client sessions,
    OpenAI Agents SDK, official MCP servers, and LangGraph compatibility.
    """

    def __init__(self, target: Target) -> None:
        """Initialize the ProxyMCP with a target MCP server.

        :param target: The target MCP server to proxy requests to
        """
        self.target = target

    @classmethod
    def from_config(cls, config_file: str | Path) -> Self:
        """Factory method to create ProxyMCP from a configuration file.

        :param config_file: Path to the configuration file (YAML or JSON)
        :return: ProxyMCP instance
        """
        config = OmegaConf.load(config_file)
        target = create_target_from_config(config.target)
        return cls(target)

    @asynccontextmanager
    async def client_session_adapter(self) -> AsyncIterator[Any]:
        """Create a client session adapter for the target.

        Provides a context manager that yields a ClientSessionAdapter for
        interacting with the target as a client session.

        :yield: ClientSessionAdapter for the target
        """
        try:
            await self.target.initialize()
            yield ClientSessionAdapter(self.target)
        finally:
            await self.target.close()

    @asynccontextmanager
    async def openai_agents_mcp_server(self) -> AsyncIterator[Any]:
        """Convert the target to an OpenAI Agents MCP server.

        Provides a context manager that yields an OpenAI Agents SDK compatible
        adapter for the target.

        :yield: OpenAIMCPServerAdapter for the target
        """
        adapter = OpenAIMCPServerAdapter(self.target)
        try:
            await adapter.connect()
            yield adapter
        finally:
            await adapter.cleanup()

    @asynccontextmanager
    async def official_mcp_server(self) -> AsyncIterator[Server[Any]]:
        """Convert the target to an official MCP server.

        Creates a standard MCP Server instance that wraps the target,
        allowing it to be used with official MCP tooling.

        :yield: Official MCP Server instance wrapping the target
        """
        await self.target.initialize()

        try:
            wrapped_mcp: Server[Any] = Server(self.target.name)

            @wrapped_mcp.list_tools()  # type: ignore[no-untyped-call, misc]
            async def handle_list_tools() -> list[Tool]:
                """Handle list_tools requests for the wrapped server.

                :return: List of available tools from the target
                """
                return await self.target.list_tools()

            @wrapped_mcp.call_tool()  # type: ignore[no-untyped-call, misc]
            async def handle_call_tool(
                name: str,
                arguments: dict[str, Any],
            ) -> Iterable[Content]:
                """Handle call_tool requests for the wrapped server.

                :param name: Name of the tool to call
                :param arguments: Arguments to pass to the tool
                :return: Iterable of content responses from the tool
                """
                return await self.target.call_tool(name=name, arguments=arguments)

            yield wrapped_mcp
        finally:
            await self.target.close()

    def langgraph_multi_server_mcp_client(self) -> Any:
        """Convert the target to a LangGraph-compatible multi-server MCP client.

        This provides an interface similar to MultiServerMCPClient from langchain-mcp-adapters
        for use with LangGraph workflows.

        :return: LangGraphMultiServerMCPClient adapter for the target
        """
        return LangGraphMultiServerMCPClient(self.target)
