"""Multiplex target implementation for combining multiple MCP targets."""

import asyncio
from typing import Any

from mcp import ErrorData, McpError
from mcp.types import Content, Tool
from omegaconf import DictConfig
from typing_extensions import Self

from mcp_kit.factory import create_target_from_config
from mcp_kit.targets.interfaces import Target


class MultiplexTarget(Target):
    """Target that combines multiple targets into a single interface.

    This target implementation allows multiple MCP targets to be accessed
    through a single interface. Tools from different targets are namespaced
    to avoid conflicts.
    """

    def __init__(self, name: str, *targets: Target) -> None:
        """Initialize the multiplex target.

        :param name: Name of the multiplex target
        :param targets: Variable number of targets to multiplex
        """
        self._name = name
        self._targets_dict = {target.name: target for target in targets}

    @property
    def name(self) -> str:
        """Get the target name.

        :return: The target name
        """
        return self._name

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create MultiplexTarget from configuration.

        :param config: Target configuration from OmegaConf
        :return: MultiplexTarget instance
        """
        # Create all sub-targets
        targets = []
        for sub_target_config in config.targets:
            # TODO validate that none of the sub-targets have the same name
            # TODO validate that none of the sub-targets have "." in their name
            targets.append(create_target_from_config(sub_target_config))

        return cls(config.name, *targets)

    async def initialize(self) -> None:
        """Initialize all sub-targets concurrently."""
        await asyncio.gather(
            *[target.initialize() for target in self._targets_dict.values()],
        )

    async def list_tools(self) -> list[Tool]:
        """List all tools from all targets with namespace prefixes.

        Each tool name is prefixed with the target name to ensure uniqueness
        across multiple targets.

        :return: List of all namespaced tools from all targets
        """
        tools = []
        for target in self._targets_dict.values():
            target_tools = await target.list_tools()
            for tool in target_tools:
                # Ensure unique tool names across targets
                namespaced_tool_name = self._get_namespaced_tool_name(target, tool.name)
                tools.append(
                    Tool(
                        name=namespaced_tool_name,
                        description=tool.description,
                        inputSchema=tool.inputSchema,
                        annotations=tool.annotations,
                    ),
                )
        return tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Call a tool on the appropriate target.

        The tool name must be in the format 'target_name.tool_name' to identify
        which target should handle the call.

        :param name: Namespaced tool name (target_name.tool_name)
        :param arguments: Arguments to pass to the tool
        :return: List of content responses from the tool
        :raises McpError: If the tool name is invalid or target not found
        """
        target_name = self._get_namespace_from_tool_name(name)
        if target_name not in self._targets_dict:
            raise McpError(
                ErrorData(
                    code=400,
                    message=f"Tool '{name}' not found",
                ),
            )
        return await self._targets_dict[target_name].call_tool(name, arguments)

    def _get_namespaced_tool_name(self, target: Target, tool_name: str) -> str:
        """Create a namespaced tool name.

        :param target: The target that owns the tool
        :param tool_name: The original tool name
        :return: Namespaced tool name in format 'target_name.tool_name'
        """
        return target.name + "." + tool_name

    def _get_namespace_from_tool_name(self, name: str) -> str:
        """Extract target name from a namespaced tool name.

        :param name: Namespaced tool name
        :return: Target name
        :raises McpError: If the tool name format is invalid
        """
        if "." not in name:
            raise McpError(
                ErrorData(
                    code=400,
                    message=f"Invalid tool name '{name}', expected format 'target_name.tool_name'",
                ),
            )
        return name.split(".")[0]

    async def close(self) -> None:
        """Close all sub-targets concurrently."""
        await asyncio.gather(
            *[target.close() for target in self._targets_dict.values()],
        )
