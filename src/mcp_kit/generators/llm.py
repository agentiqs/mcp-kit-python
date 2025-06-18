"""LLM-based response generator for realistic mock responses."""

import logging
from typing import Any

import litellm
from litellm import acompletion
from litellm.exceptions import AuthenticationError
from litellm.types.utils import Choices, ModelResponse
from mcp import Tool
from mcp.types import Content, TextContent
from omegaconf import DictConfig
from typing_extensions import Self

from mcp_kit.generators.interfaces import ResponseGenerator

# Suppress INFO logging from LiteLLM
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
litellm.suppress_debug_info = True  # Suppress extra debug info from litellm


class LlmAuthenticationError(Exception):
    """Exception raised when LLM authentication fails.

    This exception is raised when the LLM service rejects the authentication
    credentials (API key, token, etc.).
    """

    pass


class LlmResponseGenerator(ResponseGenerator):
    """Generate mock responses using an LLM agent.

    This generator uses a Large Language Model to create realistic mock responses
    based on the tool context, making it suitable for testing scenarios that
    require believable synthetic data.
    """

    def __init__(self, model: str):
        """Initialize the LLM response generator.

        :param model: The LLM model identifier to use for generation
        """
        self.model = model
        self.messages = [
            {
                "role": "system",
                "content": """
You are a Mock Response Generator that creates realistic mock responses for tool calls.

Your task is to:
1. Analyze the provided tool call context.
2. Generate a realistic mock response that matches that context.
3. Consider the tool name, description, input schema, and call arguments to create appropriate content.
4. Return only the mock response content, without any explanations or metadata
5. Don't use a markdown code block or any other formatting, just plain text

Make the response realistic and contextually appropriate for the given tool call.
""",
            },
        ]

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create LLMResponseGenerator from configuration.

        :param config: Configuration data with required 'model' parameter
        :return: LLMResponseGenerator instance
        :raises ValueError: If model parameter is missing from configuration
        """
        model = config.get("model")
        if model is None:
            raise ValueError(
                "Configuration must include a 'model' parameter for LLMResponseGenerator.",
            )
        return cls(model=model)

    async def generate(
        self,
        target_name: str,
        tool: Tool,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Generate mock response using the LLM agent.

        Creates a contextual prompt based on the tool information and uses
        the configured LLM to generate a realistic response.

        :param target_name: Name of the target server
        :param tool: The MCP tool definition
        :param arguments: Arguments passed to the tool
        :return: List containing generated text content
        :raises LlmAuthenticationError: If LLM authentication fails
        :raises ValueError: If the LLM response is empty
        """
        # Create a detailed prompt with server request information
        prompt = f"""
        Generate a mock response for the following tool call, using all contextual
        information.

        Server Name: {target_name}
        Tool Name: {tool.name or "Not provided"}
        Tool Description: {tool.description or "Not provided"}
        Input Schema: {tool.inputSchema or "Not provided"}
        Call Arguments: {arguments or "Not provided"}

        Please generate a realistic mock response for this tool call.
        """

        try:
            response: ModelResponse = await acompletion(
                model=self.model,
                messages=self.messages + [{"role": "user", "content": prompt}],
            )
        except AuthenticationError:
            raise LlmAuthenticationError(
                f"Authentication failed for model '{self.model}'. Please check your API key and model configuration.",
            ) from None
        choice: Choices = response.choices[0]  # type: ignore[assignment]
        if not choice.message.content:
            raise ValueError(
                "LLM response is empty. Please check the model and prompt.",
            )
        return [TextContent(type="text", text=choice.message.content.strip())]
