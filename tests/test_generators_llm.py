"""Tests for LLM response generator."""

from unittest.mock import MagicMock, patch

import pytest
from mcp import Tool
from mcp.types import TextContent
from omegaconf import OmegaConf

from mcp_kit.generators.llm import LlmAuthenticationError, LlmResponseGenerator


class TestLlmResponseGenerator:
    """Test cases for LlmResponseGenerator."""

    def test_init(self):
        """Test LlmResponseGenerator initialization."""
        generator = LlmResponseGenerator("gpt-4")
        assert generator.model == "gpt-4"
        assert len(generator.messages) == 1
        assert generator.messages[0]["role"] == "system"

    def test_from_config_with_model(self):
        """Test from_config with model specified."""
        config = OmegaConf.create({"model": "gpt-3.5-turbo"})
        generator = LlmResponseGenerator.from_config(config)
        assert generator.model == "gpt-3.5-turbo"

    def test_from_config_missing_model(self):
        """Test from_config raises error when model is missing."""
        config = OmegaConf.create({})
        with pytest.raises(
            ValueError, match="Configuration must include a 'model' parameter"
        ):
            LlmResponseGenerator.from_config(config)

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful response generation."""
        generator = LlmResponseGenerator("gpt-4")
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        # Mock the LLM response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Generated response from LLM"
        mock_response.choices = [mock_choice]

        with patch(
            "mcp_kit.generators.llm.acompletion", return_value=mock_response
        ) as mock_completion:
            result = await generator.generate("test_target", tool, {"param": "value"})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert result[0].text == "Generated response from LLM"

            # Verify the completion was called with correct parameters
            mock_completion.assert_called_once()
            call_args = mock_completion.call_args
            assert call_args[1]["model"] == "gpt-4"
            assert len(call_args[1]["messages"]) == 2  # system + user message

    @pytest.mark.asyncio
    async def test_generate_with_none_arguments(self):
        """Test generate with None arguments."""
        generator = LlmResponseGenerator("gpt-4")
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Response without arguments"
        mock_response.choices = [mock_choice]

        with patch("mcp_kit.generators.llm.acompletion", return_value=mock_response):
            result = await generator.generate("test_target", tool, None)

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert result[0].text == "Response without arguments"

    @pytest.mark.asyncio
    async def test_generate_authentication_error(self):
        """Test generate raises LlmAuthenticationError for authentication failures."""
        generator = LlmResponseGenerator("gpt-4")
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        from litellm.exceptions import AuthenticationError as LiteLLMAuthError

        with patch(
            "mcp_kit.generators.llm.acompletion",
            side_effect=LiteLLMAuthError("Invalid API key", "openai", "gpt-4"),
        ):
            with pytest.raises(
                LlmAuthenticationError, match="Authentication failed for model 'gpt-4'"
            ):
                await generator.generate("test_target", tool, {"param": "value"})

    @pytest.mark.asyncio
    async def test_generate_general_exception(self):
        """Test generate handles general exceptions."""
        generator = LlmResponseGenerator("gpt-4")
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        with patch(
            "mcp_kit.generators.llm.acompletion", side_effect=RuntimeError("API Error")
        ):
            with pytest.raises(RuntimeError, match="API Error"):
                await generator.generate("test_target", tool, {"param": "value"})

    @pytest.mark.asyncio
    async def test_generate_empty_response(self):
        """Test generate handles empty LLM response."""
        generator = LlmResponseGenerator("gpt-4")
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = ""
        mock_response.choices = [mock_choice]

        with patch("mcp_kit.generators.llm.acompletion", return_value=mock_response):
            with pytest.raises(ValueError, match="LLM response is empty"):
                await generator.generate("test_target", tool, {"param": "value"})

    @pytest.mark.asyncio
    async def test_generate_multiple_choices(self):
        """Test generate with multiple choices in response."""
        generator = LlmResponseGenerator("gpt-4")
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        mock_response = MagicMock()
        mock_choice1 = MagicMock()
        mock_choice1.message.content = "First choice"
        mock_choice2 = MagicMock()
        mock_choice2.message.content = "Second choice"
        mock_response.choices = [mock_choice1, mock_choice2]

        with patch("mcp_kit.generators.llm.acompletion", return_value=mock_response):
            result = await generator.generate("test_target", tool, {"param": "value"})

            # Should only return the first choice
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert result[0].text == "First choice"

    @pytest.mark.asyncio
    async def test_generate_with_complex_tool(self):
        """Test generate with a more complex tool definition."""
        generator = LlmResponseGenerator("gpt-4")
        tool = Tool(
            name="complex_tool",
            description="A complex tool with parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"},
                },
            },
        )

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Complex tool response"
        mock_response.choices = [mock_choice]

        with patch(
            "mcp_kit.generators.llm.acompletion", return_value=mock_response
        ) as mock_completion:
            result = await generator.generate(
                "test_target", tool, {"param1": "value", "param2": 42}
            )

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert result[0].text == "Complex tool response"

            # Verify the user message contains tool and argument information
            call_args = mock_completion.call_args
            user_message = call_args[1]["messages"][1]["content"]
            assert "complex_tool" in user_message
            assert "param1" in user_message
            assert "param2" in user_message

    def test_model_property(self):
        """Test model property access."""
        generator = LlmResponseGenerator("claude-3-sonnet")
        assert generator.model == "claude-3-sonnet"

    def test_different_models(self):
        """Test generator works with different model identifiers."""
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "gemini-pro"]

        for model in models:
            generator = LlmResponseGenerator(model)
            assert generator.model == model

    @pytest.mark.asyncio
    async def test_generate_message_construction(self):
        """Test that messages are properly constructed for LLM."""
        generator = LlmResponseGenerator("gpt-4")
        tool = Tool(
            name="message_test", description="Test message construction", inputSchema={}
        )

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_response.choices = [mock_choice]

        with patch(
            "mcp_kit.generators.llm.acompletion", return_value=mock_response
        ) as mock_completion:
            await generator.generate("test_target", tool, {"test": "data"})

            call_args = mock_completion.call_args
            messages = call_args[1]["messages"]

            # Should have system message and user message
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

            # User message should contain target, tool, and arguments info
            user_content = messages[1]["content"]
            assert "test_target" in user_content
            assert "message_test" in user_content
            assert "test" in user_content
