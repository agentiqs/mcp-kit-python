from typing import Any, cast

import aiohttp
from mcp import Tool
from mcp.types import Content, GetPromptResult, Prompt
from omegaconf import DictConfig, OmegaConf
from typing_extensions import Self

from mcp_kit.factory import create_target_from_config
from mcp_kit.targets.interfaces import Target


class RegistryTarget(Target):
    """Target that resolves tools via a registry service."""

    def __init__(self, name: str, registry_url: str, context: dict[str, Any]) -> None:
        # TODO: maybe add tools as another init param so we can filter tools
        """Initialize the registry target.

        :param name: Name of the target
        :param registry_url: URL of the registry service
        """
        super().__init__()
        self._name = name
        self._registry_url = registry_url
        self._context = context
        self._target: Target | None = None
        self._registry_session: aiohttp.ClientSession | None = None

    @property
    def name(self) -> str:
        """Get the name of this target.

        :return: The target name
        """
        return self._name

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create RegistryTarget from configuration.

        :param config: Target configuration from OmegaConf
        :return: RegistryTarget instance
        """
        return cls(
            name=config.name,
            registry_url=config.registry_url,
            context=config.context,
        )

    async def initialize(self) -> None:
        """Initialize the target for use.

        This method should be called before any other operations.
        """
        # TODO: connect to the registry service, send context, fetch resolution info and connect to target
        # POST on registry_url with context
        # initialize target based on the response
        if self._registry_session is None:
            self._registry_session = aiohttp.ClientSession()
        async with self._registry_session.post(
            self._registry_url,
            json={"context": self._context},
        ) as response:
            response.raise_for_status()
            data = await response.json()
            self._target = create_target_from_config(cast(DictConfig, OmegaConf.create(data["config"]["target"])))

    async def list_tools(self) -> list[Tool]:
        """List all available tools for this target.

        :return: List of available MCP tools
        """
        if self._target is None:
            raise ValueError("Target is not initialized. Call initialize() first.")

        return await self._target.list_tools()

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Call a specific tool with given arguments.

        :param name: Name of the tool to call
        :param arguments: Arguments to pass to the tool
        :return: List of content responses from the tool
        """
        if self._target is None:
            raise ValueError("Target is not initialized. Call initialize() first.")

        return await self._target.call_tool(name, arguments)

    async def list_prompts(self) -> list[Prompt]:
        """List all available prompts for this target.

        :return: List of prompts
        """
        if self._target is None:
            raise ValueError("Target is not initialized. Call initialize() first.")

        return await self._target.list_prompts()

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
    ) -> GetPromptResult:
        """Get a specific prompt by name with optional arguments."""
        if self._target is None:
            raise ValueError("Target is not initialized. Call initialize() first.")

        return await self._target.get_prompt(name, arguments)

    async def close(self) -> None:
        """Clean up and close the target.

        This method should be called when the target is no longer needed.
        """
        if self._registry_session is not None:
            await self._registry_session.close()
            self._registry_session = None
        if self._target is not None:
            await self._target.close()
            self._target = None
