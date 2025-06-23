"""Tests for InterpolationPromptEngine."""

import pytest
from mcp.types import GetPromptResult, Prompt, PromptMessage, TextContent
from omegaconf import OmegaConf

from mcp_kit.prompts.interpolation import InterpolationPromptEngine, InterpolationPrompt


class TestInterpolationPromptEngine:
    """Test cases for InterpolationPromptEngine."""

    def test_init(self):
        """Test InterpolationPromptEngine initialization."""
        prompts = {
            "greeting": InterpolationPrompt(text="Hello {name}"),
            "report": InterpolationPrompt(text="Report for {period}: {summary}"),
        }
        engine = InterpolationPromptEngine(prompts)
        assert engine.prompts == prompts

    def test_from_config_with_prompts(self):
        """Test from_config with prompts specified."""
        config = OmegaConf.create({
            "type": "interpolation",
            "prompts": {
                "greeting": {
                    "text": "Hello {name}"
                },
                "status": {
                    "text": "System {system} is {status}"
                },
            }
        })
        engine = InterpolationPromptEngine.from_config(config)
        assert isinstance(engine, InterpolationPromptEngine)
        assert "greeting" in engine.prompts
        assert "status" in engine.prompts
        assert engine.prompts["greeting"].text == "Hello {name}"

    def test_from_config_with_defaults(self):
        """Test from_config with prompts that have defaults specified."""
        config = OmegaConf.create({
            "type": "interpolation",
            "prompts": {
                "greeting": {
                    "text": "Hello {name}, welcome to {service}!",
                    "defaults": {
                        "service": "our platform"
                    }
                },
                "report": {
                    "text": "Report for {period}: {summary}",
                    "defaults": {
                        "period": "today",
                        "summary": "No summary provided"
                    }
                }
            }
        })
        engine = InterpolationPromptEngine.from_config(config)
        assert isinstance(engine, InterpolationPromptEngine)
        assert "greeting" in engine.prompts
        assert "report" in engine.prompts
        assert engine.prompts["greeting"].text == "Hello {name}, welcome to {service}!"
        assert engine.prompts["greeting"].defaults == {"service": "our platform"}
        assert engine.prompts["report"].defaults == {"period": "today", "summary": "No summary provided"}

    def test_from_config_missing_text_field(self):
        """Test from_config raises error when text field is missing."""
        config = OmegaConf.create({
            "type": "interpolation",
            "prompts": {
                "invalid": {
                    "defaults": {"arg": "value"}
                }
            }
        })
        with pytest.raises(
            ValueError, match="Prompt 'invalid' must have a 'text' field"
        ):
            InterpolationPromptEngine.from_config(config)

    @pytest.mark.asyncio
    async def test_generate_simple_interpolation(self):
        """Test successful interpolation with simple prompt."""
        prompts = {"greeting": InterpolationPrompt(text="Hello {name}, welcome to {service}!")}
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
            "email": InterpolationPrompt(text="Dear {recipient},\n\nSubject: {subject}\n\nMessage: {message}\n\nBest regards,\n{sender}")
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
        prompts = {"simple": InterpolationPrompt(text="This is a simple message without placeholders.")}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="simple", description="Simple prompt")

        result = await engine.generate("test-target", prompt, {})

        assert result.messages[0].content.text == "This is a simple message without placeholders."

    @pytest.mark.asyncio
    async def test_generate_none_arguments(self):
        """Test interpolation with None arguments."""
        prompts = {"simple": InterpolationPrompt(text="No placeholders here")}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="simple", description="Simple prompt")

        result = await engine.generate("test-target", prompt, None)

        assert result.messages[0].content.text == "No placeholders here"

    @pytest.mark.asyncio
    async def test_generate_missing_prompt(self):
        """Test generate raises error when prompt is not found."""
        prompts = {"greeting": InterpolationPrompt(text="Hello {name}")}
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
        prompts = {"greeting": InterpolationPrompt(text="Hello {name}, your role is {role}")}
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
        prompts = {"greeting": InterpolationPrompt(text="Hello {name}")}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="greeting", description="Greeting prompt")
        arguments = {"name": "Alice", "extra": "ignored"}

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Hello Alice"

    @pytest.mark.asyncio
    async def test_generate_empty_string_arguments(self):
        """Test generate with empty string arguments."""
        prompts = {"test": InterpolationPrompt(text="Value: '{value}', Empty: '{empty}'")}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="test", description="Test prompt")
        arguments = {"value": "something", "empty": ""}

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Value: 'something', Empty: ''"

    @pytest.mark.asyncio
    async def test_generate_numeric_string_arguments(self):
        """Test generate with numeric string arguments."""
        prompts = {"report": InterpolationPrompt(text="Count: {count}, Price: ${price}")}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="report", description="Report prompt")
        arguments = {"count": "42", "price": "19.99"}

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Count: 42, Price: $19.99"

    @pytest.mark.asyncio
    async def test_generate_special_characters(self):
        """Test generate with special characters in arguments."""
        prompts = {"message": InterpolationPrompt(text="Alert: {message} [Priority: {priority}]")}
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
        prompts = {"repeat": InterpolationPrompt(text="Hello {name}, yes {name}, I'm talking to you {name}!")}
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="repeat", description="Repeat prompt")
        arguments = {"name": "Bob"}

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Hello Bob, yes Bob, I'm talking to you Bob!"

    @pytest.mark.asyncio
    async def test_generate_complex_prompt(self):
        """Test generate with complex real-world prompt."""
        prompts = {
            "ticket_response": InterpolationPrompt(text=(
                "Dear {customer_name},\n\n"
                "Thank you for contacting {company} support.\n\n"
                "Ticket ID: {ticket_id}\n"
                "Subject: {subject}\n"
                "Priority: {priority}\n\n"
                "We will respond within {response_time}.\n\n"
                "Best regards,\n{agent_name}"
            ))
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

    @pytest.mark.asyncio
    async def test_generate_with_defaults(self):
        """Test generate uses default values when arguments are missing."""
        prompts = {
            "greeting": InterpolationPrompt(
                text="Hello {name}, welcome to {service}!",
                defaults={"service": "our platform"}
            )
        }
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="greeting", description="A greeting prompt")
        arguments = {"name": "Alice"}  # No service provided, should use default

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Hello Alice, welcome to our platform!"

    @pytest.mark.asyncio
    async def test_generate_override_defaults(self):
        """Test generate allows provided arguments to override defaults."""
        prompts = {
            "greeting": InterpolationPrompt(
                text="Hello {name}, welcome to {service}!",
                defaults={"service": "our platform"}
            )
        }
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="greeting", description="A greeting prompt")
        arguments = {"name": "Alice", "service": "MCP Kit"}  # Override default service

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Hello Alice, welcome to MCP Kit!"

    @pytest.mark.asyncio
    async def test_generate_multiple_defaults(self):
        """Test generate with multiple default values."""
        prompts = {
            "ticket": InterpolationPrompt(
                text="Ticket {id}: {status} - Priority: {priority} - Assigned: {assignee}",
                defaults={
                    "status": "Open",
                    "priority": "Medium",
                    "assignee": "Unassigned"
                }
            )
        }
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="ticket", description="Ticket prompt")
        arguments = {"id": "TKT-001", "priority": "High"}  # Override priority, use other defaults

        result = await engine.generate("test-target", prompt, arguments)

        assert result.messages[0].content.text == "Ticket TKT-001: Open - Priority: High - Assigned: Unassigned"

    @pytest.mark.asyncio
    async def test_generate_missing_argument_with_no_default(self):
        """Test generate raises error when argument is missing and no default provided."""
        prompts = {
            "greeting": InterpolationPrompt(
                text="Hello {name}, welcome to {service}!",
                defaults={"service": "our platform"}  # No default for 'name'
            )
        }
        engine = InterpolationPromptEngine(prompts)

        prompt = Prompt(name="greeting", description="Greeting prompt")
        arguments = {}  # Missing 'name' and no default

        with pytest.raises(
            ValueError,
            match="Missing required argument 'name' for prompt 'greeting'"
        ):
            await engine.generate("test-target", prompt, arguments)

    @pytest.mark.asyncio
    async def test_from_config_exact_yaml_format(self):
        """Test from_config with the exact YAML format requested."""
        config = OmegaConf.create({
            "type": "interpolation",
            "prompts": {
                "prompt_name": {
                    "text": "Prompt string with {arg1} and {arg2}",
                    "defaults": {
                        "arg2": "default_value"
                    }
                },
                "another_prompt": {
                    "text": "Hello {name}, welcome to {service}!",
                    "defaults": {
                        "service": "our service"
                    }
                }
            }
        })
        engine = InterpolationPromptEngine.from_config(config)

        # Test first prompt with defaults
        prompt1 = Prompt(name="prompt_name", description="Test prompt")
        result1 = await engine.generate("test-target", prompt1, {"arg1": "value1"})
        assert result1.messages[0].content.text == "Prompt string with value1 and default_value"

        # Test first prompt with override
        result2 = await engine.generate("test-target", prompt1, {"arg1": "value1", "arg2": "custom_value"})
        assert result2.messages[0].content.text == "Prompt string with value1 and custom_value"

        # Test second prompt with defaults
        prompt2 = Prompt(name="another_prompt", description="Another test prompt")
        result3 = await engine.generate("test-target", prompt2, {"name": "Alice"})
        assert result3.messages[0].content.text == "Hello Alice, welcome to our service!"

        # Test second prompt with override
        result4 = await engine.generate("test-target", prompt2, {"name": "Alice", "service": "MCP Kit"})
        assert result4.messages[0].content.text == "Hello Alice, welcome to MCP Kit!"

    @pytest.mark.asyncio
    async def test_real_world_customer_service_scenario(self):
        """Test realistic customer service prompt interpolation scenario."""
        prompts = {
            "welcome": InterpolationPrompt(text="Hello {customer_name}! Welcome to {company}. How can I help you today?"),
            "ticket_response": InterpolationPrompt(text="Thank you for contacting {company}, {customer_name}. Your ticket #{ticket_id} has been {status}. We will {next_action} within {timeframe}."),
            "escalation": InterpolationPrompt(text="I understand your concern, {customer_name}. Let me escalate this to {department} for immediate attention."),
        }

        engine = InterpolationPromptEngine(prompts)

        # Test welcome prompt
        welcome_prompt = Prompt(name="welcome", description="Welcome message")
        result = await engine.generate(
            "customer-service",
            welcome_prompt,
            {"customer_name": "Alice", "company": "TechCorp"}
        )

        assert result.messages[0].content.text == "Hello Alice! Welcome to TechCorp. How can I help you today?"
        assert result.description == "Interpolated response for prompt 'welcome' from customer-service"

        # Test ticket response prompt
        ticket_prompt = Prompt(name="ticket_response", description="Ticket response")
        result = await engine.generate(
            "customer-service",
            ticket_prompt,
            {
                "customer_name": "Bob",
                "company": "TechCorp",
                "ticket_id": "12345",
                "status": "received",
                "next_action": "respond",
                "timeframe": "24 hours"
            }
        )

        expected = "Thank you for contacting TechCorp, Bob. Your ticket #12345 has been received. We will respond within 24 hours."
        assert result.messages[0].content.text == expected

    @pytest.mark.asyncio
    async def test_complex_placeholder_patterns(self):
        """Test complex placeholder patterns and edge cases."""
        prompts = {
            "numbers": InterpolationPrompt(text="Process {item_1} and {item_2} with {count_3}"),
            "special_chars": InterpolationPrompt(text="Email: {user_email}, Phone: {phone_number}"),
            "mixed": InterpolationPrompt(text="User {user_id} has {item_count} items in {category_name}"),
        }

        engine = InterpolationPromptEngine(prompts)

        # Test with numbers in placeholder names
        prompt = Prompt(name="numbers", description="Numbers test")
        result = await engine.generate(
            "test",
            prompt,
            {"item_1": "A", "item_2": "B", "count_3": "5"}
        )
        assert result.messages[0].content.text == "Process A and B with 5"

        # Test with special characters in values
        prompt = Prompt(name="special_chars", description="Special chars test")
        result = await engine.generate(
            "test",
            prompt,
            {"user_email": "test@example.com", "phone_number": "+1-555-123-4567"}
        )
        assert result.messages[0].content.text == "Email: test@example.com, Phone: +1-555-123-4567"

    @pytest.mark.asyncio
    async def test_empty_prompt_handling(self):
        """Test handling of empty prompts and prompts without placeholders."""
        prompts = {
            "empty": InterpolationPrompt(text=""),
            "only_text": InterpolationPrompt(text="No placeholders here"),
        }

        engine = InterpolationPromptEngine(prompts)

        # Test empty string prompt
        prompt = Prompt(name="empty", description="Empty prompt")
        result = await engine.generate("test", prompt, {})
        assert result.messages[0].content.text == ""

        # Test prompt with no placeholders
        prompt = Prompt(name="only_text", description="No placeholders")
        result = await engine.generate("test", prompt, {"unused": "value"})
        assert result.messages[0].content.text == "No placeholders here"

    def test_from_config_empty_prompts(self):
        """Test from_config with empty prompts dict."""
        config = OmegaConf.create({
            "type": "interpolation",
            "prompts": {}
        })

        engine = InterpolationPromptEngine.from_config(config)
        assert len(engine.prompts) == 0
