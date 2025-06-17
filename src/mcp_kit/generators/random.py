"""Random response generator for testing purposes."""

import random
import string
from typing import Any

from mcp import Tool
from mcp.types import Content, TextContent
from omegaconf import DictConfig
from typing_extensions import Self

from mcp_kit.generators.interfaces import ResponseGenerator


class RandomResponseGenerator(ResponseGenerator):
    """Generate random text content for testing.

    This generator creates synthetic responses containing random text,
    useful for testing MCP integrations without needing real data sources.
    """

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create RandomResponseGenerator from configuration.

        :param config: Configuration data (no parameters needed for random generator)
        :return: RandomResponseGenerator instance
        """
        _ = config  # Unused in this generator, but required for interface compliance
        return cls()

    async def generate(
        self,
        target_name: str,
        tool: Tool,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Generate a random text response.

        :param target_name: Name of the target (unused in random generation)
        :param tool: The MCP tool definition (unused in random generation)
        :param arguments: Tool arguments (unused in random generation)
        :return: List containing a single TextContent with random text
        """
        _, _, _ = target_name, tool, arguments  # Unused in this generator

        return [
            TextContent(
                type="text",
                text="".join(
                    random.choices(string.ascii_letters + string.digits + " ", k=100),
                ),
            ),
        ]
