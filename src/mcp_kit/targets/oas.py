"""OpenAPI Specification (OAS) target implementation."""

import asyncio
from typing import Any

import click
import uvicorn
from mcp import Tool
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context
from mcp.server.session import ServerSessionT
from mcp.shared.context import LifespanContextT
from mcp.types import Content
from omegaconf import DictConfig
from openapi_mcp import create_mcp_server  #  type: ignore[import-untyped]
from typing_extensions import Self

from mcp_kit.targets.interfaces import Target


class OasTarget(Target):
    """Target implementation for OpenAPI Specification (OAS) endpoints.

    This target creates MCP tools from OpenAPI specifications, allowing
    interaction with REST APIs through the MCP protocol.
    """

    def __init__(
        self,
        name: str,
        spec_url: str,
    ) -> None:
        """Initialize the OAS target.

        :param name: Name of the target
        :param spec_url: URL of the OpenAPI specification
        """
        self._name = name
        self._spec_url = spec_url
        self._fast_mcp: FastMCP | None = None

    @property
    def name(self) -> str:
        """Get the target name.

        :return: The target name
        """
        return self._name

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create OasTarget from configuration.

        :param config: Target configuration from OmegaConf
        :return: OasTarget instance
        """
        return cls(name=config.name, spec_url=config.spec_url)

    async def initialize(self) -> None:
        """Initialize the target by creating MCP server from OpenAPI spec.

        Downloads and parses the OpenAPI specification to create the underlying
        FastMCP server with tools for each API endpoint.
        """
        self._fast_mcp = create_mcp_server(self._spec_url)
        call_tool = self._fast_mcp._tool_manager.call_tool

        async def call_tool_with_kwargs(
            name: str,
            arguments: dict[str, Any],
            context: Context[ServerSessionT, LifespanContextT] | None = None,
        ) -> Any:
            """Wrapper to add kwargs parameter to tool calls.

            :param name: Tool name
            :param arguments: Tool arguments
            :param context: Optional server context
            :return: Tool call result
            """
            arguments["kwargs"] = {}
            return await call_tool(name, arguments, context)

        setattr(self._fast_mcp._tool_manager, "call_tool", call_tool_with_kwargs)

    async def list_tools(self) -> list[Tool]:
        """List all tools generated from the OpenAPI specification.

        :return: List of tools corresponding to API endpoints
        :raises ValueError: If the target is not initialized
        """
        if self._fast_mcp is None:
            raise ValueError(
                "OasTarget server is not initialized. Call initialize() first.",
            )
        return await self._fast_mcp.list_tools()

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Call an API endpoint through the corresponding MCP tool.

        :param name: Name of the tool/endpoint to call
        :param arguments: Arguments to pass to the API endpoint
        :return: List of content responses from the API call
        :raises ValueError: If the target is not initialized
        """
        if self._fast_mcp is None:
            raise ValueError(
                "OasTarget server is not initialized. Call initialize() first.",
            )
        return list(await self._fast_mcp.call_tool(name, arguments or {}))

    async def close(self) -> None:
        """Clean up the target by releasing the FastMCP server."""
        self._fast_mcp = None


# TODO delete once we have a single main entry point with click
async def run_async(oas_name: str, spec_url: str, port: int) -> None:
    """Run the OAS target as a standalone HTTP server.

    :param oas_name: Name for the OAS instance
    :param spec_url: URL of the OpenAPI specification
    :param port: Port to run the server on
    :raises ValueError: If the target fails to initialize
    """
    oas = OasTarget(oas_name, spec_url=spec_url)
    await oas.initialize()
    if oas._fast_mcp is None:
        raise ValueError("OasTarget server did not initialize properly.")
    app = oas._fast_mcp.streamable_http_app()
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        loop="asyncio",
        log_config=None,
        access_log=True,
        use_colors=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


@click.command()
@click.option(
    "--oas-name",
    default="oas",
    help="Name of the OAS instance (default: oas)",
)
@click.option("--spec-url", required=True, help="OpenAPI spec URL")
@click.option(
    "--port",
    default=9000,
    show_default=True,
    help="Port to run the server on",
)
def run_sync(oas_name: str, spec_url: str, port: int) -> None:
    """Synchronous wrapper for running the OAS target server.

    :param oas_name: Name for the OAS instance
    :param spec_url: URL of the OpenAPI specification
    :param port: Port to run the server on
    """
    asyncio.run(run_async(oas_name, spec_url, port))


if __name__ == "__main__":
    asyncio.run(run_sync())
