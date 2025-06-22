"""Tests for InterpolationPromptEngine."""

import pytest
from mcp.types import GetPromptResult, Prompt, PromptMessage, TextContent
from omegaconf import OmegaConf

from mcp_kit.prompts.interpolation import InterpolationPromptEngine


class TestInterpolationPromptEngine:
    """Test cases for InterpolationPromptEngine."""

    def test_init(self):
        """Test InterpolationPromptEngine initialization."""
        prompts = {
            "greeting": "Hello {name}",
            "report": "Report for {period}: {summary}",
        }
        engine = InterpolationPromptEngine(prompts)
        assert engine.prompts == prompts

    def test_from_config_with_prompts(self):
        """Test from_config with prompts specified."""
        config = OmegaConf.create({
            "type": "interpolation",
            "prompts": {
                "greeting": "Hello {name}",
                "status": "System {system} is {status}",
            }
        })
        engine = InterpolationPromptEngine.from_config(config)
        assert isinstance(engine, InterpolationPromptEngine)
        assert "greeting" in engine.prompts
        assert "status" in engine.prompts
        assert engine.prompts["greeting"] == "Hello {name}"

    def test_from_config_missing_prompts(self):
        """Test from_config raises error when prompts are missing."""
        config = OmegaConf.create({"type": "interpolation"})
        with pytest.raises(
            ValueError, match="Configuration must include a 'prompts' parameter"
        ):
            InterpolationPromptEngine.from_config(config)

    @pytest.mark.asyncio
    async def test_generate_simple_interpolation(self):
        """Test successful interpolation with simple prompt."""
        prompts = {"greeting": "Hello {name}, welcome to {service}!"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="greeting", description="A greeting prompt")
        arguments = {"name": "Alice", "service": "MCP Kit"}

        result = await engine.generate("test-target", prompt, arguments)

        assert isinstance(result, GetPromptResult)
        assert result.description == "Interpolated response for prompt 'greeting' from test-target"
        assert len(result.messages) == 1
        assert isinstance(result.messages[0], PromptMessage)
        assert result.messages[0].role == "user"
        assert isinstance(result.messages[0].content, TextContent)
        assert result.messages[0].content.text == "Hello Alice, welcome to MCP Kit!"

    @pytest.mark.asyncio
    async def test_generate_multiline_prompt(self):
        """Test interpolation with multiline prompt."""
        prompts = {
            "email": "Dear {recipient},\n\nSubject: {subject}\n\nMessage: {message}\n\nBest regards,\n{sender}"
        }
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="email", description="Email prompt")
        arguments = {
            "recipient": "John",
            "subject": "Meeting Update",
            "message": "The meeting has been rescheduled.",
            "sender": "Alice"
        }

        result = await engine.generate("test-target", prompt, arguments)

        expected_text = (
            "Dear John,\n\nSubject: Meeting Update\n\n"
            "Message: The meeting has been rescheduled.\n\nBest regards,\nAlice"
        )
        assert result.messages[0].content.text == expected_text

    @pytest.mark.asyncio
    async def test_generate_no_arguments(self):
        """Test interpolation with prompt that requires no arguments."""
        prompts = {"simple": "This is a simple message without placeholders."}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="simple", description="Simple prompt")

        result = await engine.generate("test-target", prompt, {})

        assert result.messages[0].content.text == "This is a simple message without placeholders."

    @pytest.mark.asyncio
    async def test_generate_none_arguments(self):
        """Test interpolation with None arguments."""
        prompts = {"simple": "No placeholders here"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="simple", description="Simple prompt")

        result = await engine.generate("test-target", prompt, None)

        assert result.messages[0].content.text == "No placeholders here"

    @pytest.mark.asyncio
    async def test_generate_missing_prompt(self):
        """Test generate raises error when prompt is not found."""
        prompts = {"greeting": "Hello {name}"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="unknown", description="Unknown prompt")

        with pytest.raises(
            ValueError,
            match="No prompt found for prompt 'unknown' in interpolation engine"
        ):
            await engine.generate("test-target", prompt, {})

    @pytest.mark.asyncio
    async def test_generate_missing_argument(self):
        """Test generate raises error when required argument is missing."""
        prompts = {"greeting": "Hello {name}, your role is {role}"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="greeting", description="Greeting prompt")
        arguments = {"name": "Alice"}  # Missing 'role'

        with pytest.raises(
            ValueError,
            match="Missing required argument 'role' for prompt 'greeting'"
        ):
            await engine.generate("test-target", prompt, arguments)

    @pytest.mark.asyncio
    async def test_generate_extra_arguments(self):
        """Test generate ignores extra arguments."""
        prompts = {"greeting": "Hello {name}"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="greeting", description="Greeting prompt")
        arguments = {"name": "Alice", "extra": "ignored"}

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Hello Alice"

    @pytest.mark.asyncio
    async def test_generate_empty_string_arguments(self):
        """Test generate with empty string arguments."""
        prompts = {"test": "Value: '{value}', Empty: '{empty}'"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="test", description="Test prompt")
        arguments = {"value": "something", "empty": ""}

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Value: 'something', Empty: ''"

    @pytest.mark.asyncio
    async def test_generate_numeric_string_arguments(self):
        """Test generate with numeric string arguments."""
        prompts = {"report": "Count: {count}, Price: ${price}"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="report", description="Report prompt")
        arguments = {"count": "42", "price": "19.99"}

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Count: 42, Price: $19.99"

    @pytest.mark.asyncio
    async def test_generate_special_characters(self):
        """Test generate with special characters in arguments."""
        prompts = {"message": "Alert: {message} [Priority: {priority}]"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="message", description="Message prompt")
        arguments = {
            "message": "System failure! @#$%^&*()",
            "priority": "HIGH!!!"
        }

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Alert: System failure! @#$%^&*() [Priority: HIGH!!!]"

    @pytest.mark.asyncio
    async def test_generate_duplicate_placeholders(self):
        """Test generate with prompts that have duplicate placeholders."""
        prompts = {"repeat": "Hello {name}, yes {name}, I'm talking to you {name}!"}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="repeat", description="Repeat prompt")
        arguments = {"name": "Bob"}

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Hello Bob, yes Bob, I'm talking to you Bob!"

    @pytest.mark.asyncio
    async def test_generate_complex_prompt(self):
        """Test generate with complex real-world prompt."""
        prompts = {
            "ticket_response": (
                "Dear {customer_name},\n\n"
                "Thank you for contacting {company} support.\n\n"
                "Ticket ID: {ticket_id}\n"
                "Subject: {subject}\n"
                "Priority: {priority}\n\n"
                "We will respond within {response_time}.\n\n"
                "Best regards,\n{agent_name}"
            )
        }
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="ticket_response", description="Support ticket response")
        arguments = {
            "customer_name": "John Doe",
            "company": "ACME Corp",
            "ticket_id": "TKT-12345",
            "subject": "Login Issues",
            "priority": "High",
            "response_time": "24 hours",
            "agent_name": "Alice Support"
        }

        result = await engine.generate("test-target", prompt, arguments)

        expected = (
            "Dear John Doe,\n\n"
            "Thank you for contacting ACME Corp support.\n\n"
            "Ticket ID: TKT-12345\n"
            "Subject: Login Issues\n"
            "Priority: High\n\n"
            "We will respond within 24 hours.\n\n"
            "Best regards,\nAlice Support"
        )
        assert result.messages[0].content.text == expected
