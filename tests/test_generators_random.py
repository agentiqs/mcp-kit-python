"""Tests for random response generator."""

import string

import pytest
from mcp import Tool
from mcp.types import TextContent
from omegaconf import OmegaConf

from mcp_kit.generators.random import RandomResponseGenerator


class TestRandomResponseGenerator:
    """Test cases for RandomResponseGenerator."""

    def test_from_config(self):
        """Test RandomResponseGenerator.from_config."""
        config = OmegaConf.create({"type": "random"})
        generator = RandomResponseGenerator.from_config(config)
        assert isinstance(generator, RandomResponseGenerator)

    def test_from_config_with_extra_params(self):
        """Test from_config ignores extra parameters."""
        config = OmegaConf.create({"type": "random", "extra_param": "ignored"})
        generator = RandomResponseGenerator.from_config(config)
        assert isinstance(generator, RandomResponseGenerator)

    @pytest.mark.asyncio
    async def test_generate_returns_text_content(self):
        """Test that generate returns TextContent."""
        generator = RandomResponseGenerator()
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        result = await generator.generate("test_target", tool, {"param": "value"})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
        assert len(result[0].text) > 0

    @pytest.mark.asyncio
    async def test_generate_with_none_arguments(self):
        """Test generate with None arguments."""
        generator = RandomResponseGenerator()
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        result = await generator.generate("test_target", tool, None)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert len(result[0].text) > 0

    @pytest.mark.asyncio
    async def test_generate_randomness(self):
        """Test that multiple calls to generate produce different results."""
        generator = RandomResponseGenerator()
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        results = []
        for _ in range(10):
            result = await generator.generate("test_target", tool, {"param": "value"})
            results.append(result[0].text)

        # Should have some variety in the responses (not all identical)
        unique_results = set(results)
        assert len(unique_results) > 1, (
            "Random generator should produce varied responses"
        )

    @pytest.mark.asyncio
    async def test_generate_contains_random_elements(self):
        """Test that generated text contains expected random elements."""
        generator = RandomResponseGenerator()
        tool = Tool(name="test_tool", description="A test tool", inputSchema={})

        result = await generator.generate("test_target", tool, {"param": "value"})
        text = result[0].text

        # Should contain random alphanumeric characters and spaces
        assert len(text) == 100  # Default length
        # Should only contain allowed characters
        allowed_chars = set(string.ascii_letters + string.digits + " ")
        assert all(c in allowed_chars for c in text)

    @pytest.mark.asyncio
    async def test_generate_different_tools(self):
        """Test generate with different tool names."""
        generator = RandomResponseGenerator()

        tool1 = Tool(name="first_tool", description="First tool", inputSchema={})
        tool2 = Tool(name="second_tool", description="Second tool", inputSchema={})

        result1 = await generator.generate("target1", tool1, {"param": "value1"})
        result2 = await generator.generate("target2", tool2, {"param": "value2"})

        # Results should be different (high probability with random generation)
        assert result1[0].text != result2[0].text
        # Both should be 100 characters long
        assert len(result1[0].text) == 100
        assert len(result2[0].text) == 100

    @pytest.mark.asyncio
    async def test_generate_consistent_format(self):
        """Test that all generated responses follow consistent format."""
        generator = RandomResponseGenerator()
        tool = Tool(
            name="format_test", description="Test format consistency", inputSchema={}
        )

        for i in range(5):
            result = await generator.generate(
                f"target_{i}", tool, {"param": f"value_{i}"}
            )
            text = result[0].text

            # Should always be 100 characters long
            assert len(text) == 100
            # Should only contain allowed characters
            allowed_chars = set(string.ascii_letters + string.digits + " ")
            assert all(c in allowed_chars for c in text)

    @pytest.mark.asyncio
    async def test_generate_with_complex_arguments(self):
        """Test generate with complex argument structures."""
        generator = RandomResponseGenerator()
        tool = Tool(name="complex_tool", description="Complex tool", inputSchema={})

        complex_args = {
            "string_param": "test_string",
            "number_param": 42,
            "list_param": [1, 2, 3],
            "nested_param": {"key": "value"},
        }

        result = await generator.generate("test_target", tool, complex_args)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        # Should generate 100 random characters regardless of arguments
        assert len(result[0].text) == 100

    @pytest.mark.asyncio
    async def test_generate_with_empty_arguments(self):
        """Test generate with empty arguments."""
        generator = RandomResponseGenerator()
        tool = Tool(
            name="empty_args_tool", description="Tool with empty args", inputSchema={}
        )

        result = await generator.generate("test_target", tool, {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        # Should generate 100 random characters regardless of arguments
        assert len(result[0].text) == 100

    @pytest.mark.asyncio
    async def test_generate_performance(self):
        """Test that generate completes quickly for performance."""
        import time

        generator = RandomResponseGenerator()
        tool = Tool(
            name="perf_tool", description="Performance test tool", inputSchema={}
        )

        start_time = time.time()

        # Generate multiple responses
        for _ in range(100):
            await generator.generate("test_target", tool, {"param": "value"})

        elapsed_time = time.time() - start_time

        # Should complete quickly (less than 1 second for 100 generations)
        assert elapsed_time < 1.0, (
            f"Random generation took too long: {elapsed_time:.2f}s"
        )
