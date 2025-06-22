"""Interpolation prompt engine for safe string substitution."""

from mcp.types import GetPromptResult, Prompt, PromptMessage, TextContent
from omegaconf import DictConfig
from typing_extensions import Self

from mcp_kit.prompts.interfaces import PromptEngine


class InterpolationPromptEngine(PromptEngine):
    """Prompt engine that performs safe string interpolation using predefined prompts.

    This engine uses a map of prompt names to prompt strings with {placeholder}
    syntax for argument substitution. It performs safe string replacement without
    executing arbitrary code like f-strings would.
    """

    def __init__(self, prompts: dict[str, str]):
        """Initialize the interpolation prompt engine.

        :param prompts: Map of prompt names to prompt strings with {placeholder} syntax
        """
        self.prompts = prompts

    @classmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Create InterpolationPromptEngine from configuration.

        Expected config format:
        {
            "type": "interpolation",
            "prompts": {
                "prompt_name": "Prompt string with {arg1} and {arg2}",
                "another_prompt": "Hello {name}, welcome to {service}!"
            }
        }

        :param config: Configuration data with prompts
        :return: InterpolationPromptEngine instance
        :raises ValueError: If prompts are missing from config
        """
        if "prompts" not in config:
            raise ValueError("Configuration must include a 'prompts' parameter")

        prompts = dict(config.prompts)
        return cls(prompts)

    async def generate(
        self,
        target_name: str,
        prompt: Prompt,
        arguments: dict[str, str] | None = None,
    ) -> GetPromptResult:
        """Generate a prompt response using prompt interpolation.

        Safely substitutes argument values into the prompt string using
        simple string replacement without executing code.

        :param target_name: Name of the target that would handle the prompt call
        :param prompt: The MCP prompt definition
        :param arguments: Arguments to substitute into the prompt
        :return: Generated prompt result with interpolated content
        :raises ValueError: If prompt is not found or substitution fails
        """
        if prompt.name not in self.prompts:
            raise ValueError(f"No prompt found for prompt '{prompt.name}' in interpolation engine")

        prompt_string = self.prompts[prompt.name]
        arguments = arguments or {}

        try:
            # Use safe string replacement with format() instead of f-strings
            # This only replaces named placeholders and doesn't execute code
            interpolated_text = prompt_string.format(**arguments)
        except KeyError as e:
            missing_arg = str(e).strip("'\"")
            raise ValueError(f"Missing required argument '{missing_arg}' for prompt '{prompt.name}'") from None
        except Exception as e:
            raise ValueError(f"Failed to interpolate prompt for prompt '{prompt.name}': {e}") from None

        # Return the interpolated content as a prompt message
        return GetPromptResult(
            description=f"Interpolated response for prompt '{prompt.name}' from {target_name}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=interpolated_text),
                )
            ],
        )
