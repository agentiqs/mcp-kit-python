"""MCP target implementation for connecting to MCP servers (hosted or with a spec)."""

from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, Tool
from mcp.types import Content
from omegaconf import DictConfig
from typing_extensions import Self

from mcp_kit.factory import create_tools_from_config
from mcp_kit.patch_mcp import http_streamable_session
from mcp_kit.targets.interfaces import Target


class McpTarget(Target):
    """Target implementation for connecting to MCP servers (hosted or with a spec).

    This target can connect to remote MCP servers or use predefined tools.
    It supports HTTP connections with optional headers and authentication.
    """

    def __init__(
        self,
        name: str,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        tools: list[Tool] | None = None,
    ) -> None:
        """Initialize the MCP target.

        :param name: Name of the target
        :param url: Optional URL of the remote MCP server
        :param headers: Optional HTTP headers for server requests
        :param tools: Optional predefined tools to use instead of remote server tools
        """
        self._name = name
        self.url = url
        self.headers = headers
        self.tools = tools
        self.target_mcp: ClientSession | None = None
        self.target_mcp_exit_stack: AsyncExitStack | None = None

    @property
    def name(self) -> str:
        """Get the target name.

        :return: The target name
        """
        return self._name

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create McpTarget from configuration.

        :param config: Target configuration from OmegaConf
        :return: McpTarget instance
        """
        return cls(
            name=config.name,
            url=config.get("url"),
            headers=config.get("headers"),
            tools=create_tools_from_config(config),
        )

    async def initialize(self) -> None:
        """Initialize the target by connecting to the MCP server if URL is provided.

        Sets up the HTTP connection to the remote MCP server using the configured
        URL and headers.
        """
        if self.url is not None:
            self.target_mcp, self.target_mcp_exit_stack = await http_streamable_session(
                self.url,
                self.headers,
            )

    async def list_tools(self) -> list[Tool]:
        """List all available tools.

        Returns predefined tools if available, otherwise queries the remote MCP server.

        :return: List of available tools
        :raises ValueError: If no tools are available and MCP is not initialized
        """
        if self.tools is not None:
            return self.tools
        if self.target_mcp is not None:
            return (await self.target_mcp.list_tools()).tools
        raise ValueError("No tools available. Initialize the MCP or provide tools.")

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Call a tool on the remote MCP server.

        :param name: Name of the tool to call
        :param arguments: Arguments to pass to the tool
        :return: List of content responses from the tool
        :raises ValueError: If MCP client is not initialized
        """
        if self.target_mcp is None:
            raise ValueError("MCP client is not initialized. Call initialize() first.")
        return (await self.target_mcp.call_tool(name=name, arguments=arguments)).content

    async def close(self) -> None:
        """Close the connection to the MCP server.

        Cleans up the HTTP connection and releases resources.
        """
        return await self.target_mcp_exit_stack.aclose() if self.target_mcp_exit_stack else None
