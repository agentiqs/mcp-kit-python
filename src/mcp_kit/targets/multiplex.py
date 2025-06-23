"""Multiplex target implementation for combining multiple MCP targets."""

import asyncio
from typing import Any

from mcp import ErrorData, McpError
from mcp.types import Content, GetPromptResult, Prompt, Tool
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
                namespaced_tool_name = self._get_namespaced_name(target, tool.name)
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
        target_name = self._get_namespace_from_name(name, "tool")
        if target_name not in self._targets_dict:
            raise McpError(
                ErrorData(
                    code=400,
                    message=f"Tool '{name}' not found",
                ),
            )
        return await self._targets_dict[target_name].call_tool(name, arguments)

    async def list_prompts(self) -> list[Prompt]:
        """List all prompts from all targets with namespace prefixes.

        Each prompt name is prefixed with the target name to ensure uniqueness
        across multiple targets.

        :return: List of all namespaced prompts from all targets
        """
        prompts = []
        for target in self._targets_dict.values():
            target_prompts = await target.list_prompts()
            for prompt in target_prompts:
                # Ensure unique prompt names across targets
                namespaced_prompt_name = self._get_namespaced_name(target, prompt.name)
                prompts.append(
                    Prompt(
                        name=namespaced_prompt_name,
                        description=prompt.description,
                        arguments=prompt.arguments,
                    ),
                )
        return prompts

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
    ) -> GetPromptResult:
        """Get a prompt from the appropriate target.

        The prompt name must be in the format 'target_name.prompt_name' to identify
        which target should handle the request.

        :param name: Namespaced prompt name (target_name.prompt_name)
        :param arguments: Arguments to pass to the prompt
        :return: Prompt result from the target
        :raises McpError: If the prompt name is invalid or target not found
        """
        target_name = self._get_namespace_from_name(name, "prompt")
        if target_name not in self._targets_dict:
            raise McpError(
                ErrorData(
                    code=400,
                    message=f"Prompt '{name}' not found",
                ),
            )
        return await self._targets_dict[target_name].get_prompt(name, arguments)

    def _get_namespaced_name(self, target: Target, name: str) -> str:
        """Create a namespaced name for tools or prompts.

        :param target: The target that owns the item
        :param name: The original name
        :return: Namespaced name in format 'target_name.name'
        """
        return target.name + "." + name

    def _get_namespace_from_name(self, name: str, item_type: str) -> str:
        """Extract target name from a namespaced name.

        :param name: Namespaced name
        :param item_type: Type of item ("tool" or "prompt") for error messages
        :return: Target name
        :raises McpError: If the name format is invalid
        """
        if "." not in name:
            raise McpError(
                ErrorData(
                    code=400,
                    message=f"Invalid {item_type} name '{name}', expected format 'target_name.{item_type}_name'",
                ),
            )
        return name.split(".")[0]

    async def close(self) -> None:
        """Close all sub-targets concurrently."""
        await asyncio.gather(
            *[target.close() for target in self._targets_dict.values()],
        )
