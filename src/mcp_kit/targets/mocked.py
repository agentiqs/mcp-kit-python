"""Mocked target implementation that generates fake responses."""

import logging
from dataclasses import dataclass
from typing import Any

from mcp.types import Content, Tool
from omegaconf import DictConfig, OmegaConf
from typing_extensions import Self

from mcp_kit.factory import (
    create_response_generator_from_config,
    create_target_from_config,
)
from mcp_kit.generators import LlmAuthenticationError, ResponseGenerator
from mcp_kit.targets import Target

logger = logging.getLogger(__name__)


@dataclass
class MockConfig:
    """Configuration for mocked target behavior.

    :param response_generator: The generator to use for creating mock responses
    """

    response_generator: ResponseGenerator


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

        # Create response generator using the generator's own from_config method
        generator_config = config.get(
            "response_generator",
            OmegaConf.create({"type": "random"}),
        )
        generator = create_response_generator_from_config(generator_config)

        mock_config = MockConfig(response_generator=generator)
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

        Instead of calling the actual tool, this method generates a synthetic
        response using the configured response generator.

        :param name: Name of the tool to mock
        :param arguments: Arguments that would be passed to the tool
        :return: Generated mock content response
        :raises ValueError: If the specified tool is not found
        :raises LlmAuthenticationError: If LLM authentication fails (exits program)
        """
        try:
            tools = await self.list_tools()
            for tool in tools:
                if tool.name == name:
                    return await self.mock_config.response_generator.generate(
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

    async def close(self) -> None:
        """Close the base target."""
        await self.target.close()
