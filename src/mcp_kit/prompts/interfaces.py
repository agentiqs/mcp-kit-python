"""Interface definitions for prompt engines."""

from abc import abstractmethod

from mcp.types import GetPromptResult, Prompt

from mcp_kit.mixins import ConfigurableMixin


class PromptEngine(ConfigurableMixin):
    """Interface for generating prompt responses for MCP get_prompt calls.

    Prompt engines can resolve a request from an MCP client to instantiate a prompt with
    specific arguments.
    """

    @abstractmethod
    async def generate(
        self,
        target_name: str,
        prompt: Prompt,
        arguments: dict[str, str] | None = None,
    ) -> GetPromptResult:
        """Generate an MCP get_prompt response.

        :param target_name: Name of the target that would handle the prompt call
        :param prompt: The MCP prompt definition
        :param arguments: Arguments that would be passed to the prompt
        :return: Generated prompt result response
        """
