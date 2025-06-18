"""OpenAI Agents SDK adapter for MCP targets."""

import logging
from typing import Any

from mcp import Tool
from mcp.types import CallToolResult, TextContent

from mcp_kit.targets.interfaces import Target

logger = logging.getLogger(__name__)


class OpenAIMCPServerAdapter:
    """Adapter class to convert MCP targets to OpenAI Agents SDK compatible interface.

    This adapter provides compatibility with OpenAI's Agents SDK by implementing
    the expected interface for MCP server connections.
    """

    def __init__(self, target: Target):
        """Initialize the OpenAI MCP server adapter.

        :param target: The MCP target to adapt
        """
        self.target = target

    async def connect(self) -> None:
        """Connect to the server.

        This might involve spawning a subprocess or opening a network connection.
        The server is expected to remain connected until `cleanup()` is called.
        """
        await self.target.initialize()

    @property
    def name(self) -> str:
        """Get a readable name for the server.

        :return: The server name
        """
        return self.target.name

    async def cleanup(self) -> None:
        """Cleanup the server.

        This might involve closing a subprocess or closing a network connection.
        """
        await self.target.close()

    async def list_tools(self) -> list[Tool]:
        """List the tools available on the server.

        :return: List of available MCP tools
        """
        return await self.target.list_tools()

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None,
    ) -> CallToolResult:
        """Invoke a tool on the server.

        :param tool_name: Name of the tool to invoke
        :param arguments: Arguments to pass to the tool
        :return: Result of the tool call with error handling
        """
        try:
            return CallToolResult(
                content=await self.target.call_tool(
                    name=tool_name,
                    arguments=arguments,
                ),
                isError=False,
            )
        except Exception as e:
            msg = f"Error calling tool {tool_name} with arguments {arguments}: {e}"
            logger.exception(msg)
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                isError=True,
            )
