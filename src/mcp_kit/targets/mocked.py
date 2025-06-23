"""Mocked target implementation that generates fake responses."""

import logging
from dataclasses import dataclass
from typing import Any

from mcp.types import Content, GetPromptResult, Prompt, Tool
from omegaconf import DictConfig
from typing_extensions import Self

from mcp_kit.factory import (
    create_prompt_engine_from_config,
    create_response_generator_from_config,
    create_target_from_config,
)
from mcp_kit.generators import LlmAuthenticationError, ToolResponseGenerator
from mcp_kit.prompts import PromptEngine
from mcp_kit.targets import Target

logger = logging.getLogger(__name__)


@dataclass
class MockConfig:
    """Configuration for mocked target behavior.

    :param tool_response_generator: The generator to use for creating mock responses
    :param prompt_engine: The engine to use for creating mock prompt responses
    """

    tool_response_generator: ToolResponseGenerator | None = None
    prompt_engine: PromptEngine | None = None


class MockedTarget(Target):
    """Target that wraps another target and generates mock responses.

    This target implementation intercepts tool calls and generates synthetic
    responses instead of calling the actual target. Useful for testing and
    development scenarios.
    """

    def __init__(self, target: Target, mock_config: MockConfig) -> None:
        """Initialize the mocked target.

        :param target: The base target to wrap
        :param mock_config: Configuration for mock behavior
        """
        self.target = target
        self.mock_config = mock_config

    @property
    def name(self) -> str:
        """Get the target name with '_mocked' suffix.

        :return: The target name with mocked indicator
        """
        return f"{self.target.name}_mocked"

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create MockedTarget from configuration.

        :param config: Target configuration from OmegaConf
        :return: MockedTarget instance
        """
        # Create the base target
        base_target = create_target_from_config(config.base_target)

        # Create response generator if specified
        generator = None
        if "tool_response_generator" in config:
            generator = create_response_generator_from_config(config.tool_response_generator)

        # Create prompt engine if specified
        prompt_engine = None
        if "prompt_engine" in config:
            prompt_engine = create_prompt_engine_from_config(config.prompt_engine)

        mock_config = MockConfig(
            tool_response_generator=generator,
            prompt_engine=prompt_engine,
        )
        return cls(base_target, mock_config)

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
        """Generate a mock response for the specified tool.

        If a tool_response_generator is configured, generates a synthetic response.
        Otherwise, delegates to the base target.

        :param name: Name of the tool to mock
        :param arguments: Arguments that would be passed to the tool
        :return: Generated mock content response or response from base target
        :raises ValueError: If the specified tool is not found
        :raises LlmAuthenticationError: If LLM authentication fails (exits program)
        """
        if self.mock_config.tool_response_generator is not None:
            # Use tool response generator to generate mock response
            try:
                tools = await self.list_tools()
                for tool in tools:
                    if tool.name == name:
                        return await self.mock_config.tool_response_generator.generate(
                            self.target.name,
                            tool,
                            arguments,
                        )
                raise ValueError(
                    f"Tool {name} not found in tools for server {self.target.name}",
                )
            except LlmAuthenticationError as e:
                logger.exception(e)
                exit(1)
            except Exception as e:
                raise e from None
        else:
            # Delegate to base target
            return await self.target.call_tool(name, arguments)

    async def close(self) -> None:
        """Close the base target."""
        await self.target.close()

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
        """Generate a mock response for the specified prompt.

        If a prompt_engine is configured, generates a synthetic response.
        Otherwise, delegates to the base target.

        :param name: Name of the prompt to get
        :param arguments: Arguments to pass to the prompt
        :return: Prompt result (generated or from base target)
        """
        if self.mock_config.prompt_engine is not None:
            # Use prompt engine to generate mock response
            prompts = await self.list_prompts()
            for prompt in prompts:
                if prompt.name == name:
                    return await self.mock_config.prompt_engine.generate(
                        self.target.name,
                        prompt,
                        arguments,
                    )
            raise ValueError(
                f"Prompt {name} not found in prompts for server {self.target.name}",
            )
        else:
            # Delegate to base target for now
            return await self.target.get_prompt(name, arguments)
