"""Proxy target implementation for adding custom behavior before forwarding requests."""

from collections.abc import Awaitable
from typing import Any

from mcp import Tool
from mcp.types import Content, GetPromptResult, Prompt
from omegaconf import DictConfig
from typing_extensions import Self

from mcp_kit.factory import create_target_from_config
from mcp_kit.targets.interfaces import Target
from mcp_kit.types import CallToolDispatch, CallToolHandler


def default_call_tool_dispatch(
    name: str, arguments: dict[str, Any] | None, call_next: CallToolHandler
) -> Awaitable[list[Content]]:
    """Default call tool dispatch function.
    It is just a passthrough, forwarding the call to the next handler in the chain.

    :param name: Name of the tool to call
    :param arguments: Arguments to pass to the tool
    :param call_next: The next handler to call in the chain
    :return: Awaitable iterable of Content responses
    """
    return call_next(name, arguments)


class ProxyTarget(Target):
    """Target implementation for proxying call tool requests.

    This target runs as a proxy target that can run custom code before forwarding requests to an underlying target.
    """

    def __init__(
        self,
        target: Target,
        call_tool_dispatch: CallToolDispatch = default_call_tool_dispatch,
    ) -> None:
        """Initialize the Proxy target.

        :param target: The underlying target to proxy requests to
        :param call_tool_dispatch: Optional custom dispatch function for tool calls
        """
        self.target = target
        self.call_tool_dispatch = call_tool_dispatch

    @property
    def name(self) -> str:
        """Get the target name.

        :return: The target name
        """
        return self.target.name

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create ProxyTarget from configuration.

        :param config: Target configuration from OmegaConf
        :return: ProxyTarget instance
        """
        # Create the base target
        base_target = create_target_from_config(config.base_target)

        return cls(target=base_target)

    async def initialize(self) -> None:
        """Initialize the base target."""
        await self.target.initialize()

    async def list_tools(self) -> list[Tool]:
        """List tools from the base target.

        :return: List of available tools from the base target
        """
        return await self.target.list_tools()

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Call a tool on the underlying target through our dispatch.

        :param name: Name of the tool to call
        :param arguments: Arguments to pass to the tool
        :return: List of content responses from the tool
        """
        return await self.call_tool_dispatch(name, arguments, self.target.call_tool)

    async def list_prompts(self) -> list[Prompt]:
        """List prompts from the base target.

        :return: List of available prompts from the base target
        """
        return await self.target.list_prompts()

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
    ) -> GetPromptResult:
        """Get a specific prompt by name with optional arguments.

        :param name: Name of the prompt to get
        :param arguments: Arguments to pass to the prompt
        :return: Prompt result with messages
        """
        return await self.target.get_prompt(name=name, arguments=arguments)

    async def close(self) -> None:
        """Close the base target."""
        await self.target.close()
