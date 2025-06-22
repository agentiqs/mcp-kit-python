"""Additional integration tests for InterpolationPromptEngine focused specifically on interpolation functionality."""

import pytest
from mcp.types import Prompt
from omegaconf import OmegaConf

from mcp_kit.prompts.interpolation import InterpolationPromptEngine, InterpolationPrompt


class TestInterpolationEngineIntegration:
    """Integration tests specifically for InterpolationPromptEngine functionality."""

    @pytest.mark.asyncio
    async def test_real_world_customer_service_example(self):
        """Test realistic customer service prompt interpolation."""
        prompts_config = {
            "welcome": InterpolationPrompt(text="Hello {customer_name}! Welcome to {company}. How can I help you today?"),
            "ticket_response": InterpolationPrompt(text="Thank you for contacting {company}, {customer_name}. Your ticket #{ticket_id} has been {status}. We will {next_action} within {timeframe}."),
            "escalation": InterpolationPrompt(text="I understand your concern, {customer_name}. Let me escalate this to {department} for immediate attention."),
        }

        engine = InterpolationPromptEngine(prompts_config)

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
    async def test_configuration_validation_edge_cases(self):
        """Test edge cases in configuration validation."""
        # Empty prompts config should work
        engine = InterpolationPromptEngine({})
        assert len(engine.prompts) == 0

        # Single character prompt names should work
        engine = InterpolationPromptEngine({"a": InterpolationPrompt(text="Short prompt for {x}")})
        prompt = Prompt(name="a", description="Test")
        result = await engine.generate("test", prompt, {"x": "testing"})
        assert result.messages[0].content.text == "Short prompt for testing"

    @pytest.mark.asyncio
    async def test_complex_placeholder_patterns(self):
        """Test complex placeholder patterns and edge cases."""
        prompts_config = {
            "numbers": "Process {item_1} and {item_2} with {count_3}",
            "special_chars": "Email: {user_email}, Phone: {phone_number}",
            "mixed": "User {user_id} has {item_count} items in {category_name}",
        }

        engine = InterpolationPromptEngine(prompts_config)

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
    async def test_error_handling_comprehensive(self):
        """Comprehensive error handling tests."""
        prompts_config = {
            "partial": "Hello {name}, missing {missing_var}",
            "empty": "",
            "only_text": "No placeholders here",
        }

        engine = InterpolationPromptEngine(prompts_config)

        # Test partial argument provision
        prompt = Prompt(name="partial", description="Partial args test")
        with pytest.raises(ValueError, match="Missing required argument 'missing_var'"):
            await engine.generate("test", prompt, {"name": "Alice"})

        # Test empty string prompt
        prompt = Prompt(name="empty", description="Empty prompt")
        result = await engine.generate("test", prompt, {})
        assert result.messages[0].content.text == ""

        # Test prompt with no placeholders
        prompt = Prompt(name="only_text", description="No placeholders")
        result = await engine.generate("test", prompt, {"unused": "value"})
        assert result.messages[0].content.text == "No placeholders here"

    def test_from_config_comprehensive(self):
        """Comprehensive tests for from_config class method."""
        # Test successful configuration
        config = OmegaConf.create({
            "type": "interpolation",
            "prompts": {
                "test1": "Hello {name}",
                "test2": "Goodbye {name}",
            }
        })

        engine = InterpolationPromptEngine.from_config(config)
        assert isinstance(engine, InterpolationPromptEngine)
        assert len(engine.prompts) == 2
        assert "test1" in engine.prompts
        assert "test2" in engine.prompts

        # Test with empty prompts dict
        config = OmegaConf.create({
            "type": "interpolation",
            "prompts": {}
        })

        engine = InterpolationPromptEngine.from_config(config)
        assert len(engine.prompts) == 0

        # Test missing prompts key
        config = OmegaConf.create({"type": "interpolation"})
        with pytest.raises(ValueError, match="Configuration must include a 'prompts' parameter"):
            InterpolationPromptEngine.from_config(config)
