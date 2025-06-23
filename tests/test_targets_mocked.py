"""Tests for mocked target implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import Tool
from mcp.types import TextContent
from omegaconf import OmegaConf

from mcp_kit.generators import LlmAuthenticationError
from mcp_kit.generators.interfaces import ToolResponseGenerator
from mcp_kit.prompts.interfaces import PromptEngine
from mcp_kit.prompts.interpolation import InterpolationPrompt
from mcp_kit.targets.interfaces import Target
from mcp_kit.targets.mocked import MockConfig, MockedTarget


@pytest.fixture
def mock_prompt_engine():
    """Create a mock prompt engine."""
    engine = MagicMock(spec=PromptEngine)
    engine.generate_prompt = AsyncMock()
    return engine


@pytest.fixture
def mock_generator():
    """Create a mock response generator."""
    generator = MagicMock(spec=ToolResponseGenerator)
    generator.generate = AsyncMock()
    return generator


@pytest.fixture
def mock_config(mock_generator):
    """Create a mock configuration."""
    return MockConfig(tool_response_generator=mock_generator)


@pytest.fixture
def mock_config_with_prompt_engine(mock_prompt_engine):
    """Create a mock configuration with prompt engine."""
    return MockConfig(prompt_engine=mock_prompt_engine)


@pytest.fixture
def mock_config_with_both(mock_generator, mock_prompt_engine):
    """Create a mock configuration with both tool response generator and prompt engine."""
    return MockConfig(tool_response_generator=mock_generator, prompt_engine=mock_prompt_engine)


@pytest.fixture
def mock_base_target():
    """Create a mock base target."""
    target = MagicMock(spec=Target)
    target.name = "base-target"
    target.initialize = AsyncMock()
    target.close = AsyncMock()
    target.list_tools = AsyncMock()
    target.call_tool = AsyncMock()
    return target


@pytest.fixture
def mocked_target(mock_base_target, mock_config):
    """Create a MockedTarget instance."""
    return MockedTarget(mock_base_target, mock_config)


class TestMockConfig:
    """Test cases for MockConfig dataclass."""

    def test_mock_config_creation(self, mock_generator):
        """Test MockConfig creation."""
        config = MockConfig(tool_response_generator=mock_generator)
        assert config.tool_response_generator == mock_generator

    def test_mock_config_creation_with_prompt_engine(self, mock_prompt_engine):
        """Test MockConfig creation with prompt engine."""
        config = MockConfig(prompt_engine=mock_prompt_engine)
        assert config.prompt_engine == mock_prompt_engine
        assert config.tool_response_generator is None

    def test_mock_config_creation_with_both(self, mock_generator, mock_prompt_engine):
        """Test MockConfig creation with both tool response generator and prompt engine."""
        config = MockConfig(tool_response_generator=mock_generator, prompt_engine=mock_prompt_engine)
        assert config.tool_response_generator == mock_generator
        assert config.prompt_engine == mock_prompt_engine

    def test_mock_config_dataclass_behavior(self, mock_generator):
        """Test MockConfig behaves like a dataclass."""
        config1 = MockConfig(tool_response_generator=mock_generator)
        config2 = MockConfig(tool_response_generator=mock_generator)

        # Should be equal if same generator
        assert config1.tool_response_generator == config2.tool_response_generator


class TestMockedTarget:
    """Test cases for MockedTarget class."""

    def test_init(self, mock_base_target, mock_config):
        """Test MockedTarget initialization."""
        target = MockedTarget(mock_base_target, mock_config)
        assert target.target == mock_base_target
        assert target.mock_config == mock_config

    def test_name_property(self, mocked_target):
        """Test name property adds '_mocked' suffix."""
        assert mocked_target.name == "base-target_mocked"

    def test_from_config_with_random_generator(self):
        """Test MockedTarget.from_config with random generator."""
        config = OmegaConf.create(
            {
                "type": "mocked",
                "base_target": {
                    "type": "mcp",
                    "name": "base-mcp",
                    "url": "http://example.com/mcp",
                },
                "tool_response_generator": {"type": "random"},
            }
        )

        with (
            patch(
                "mcp_kit.targets.mocked.create_target_from_config"
            ) as mock_create_target,
            patch(
                "mcp_kit.targets.mocked.create_response_generator_from_config"
            ) as mock_create_generator,
        ):
            mock_base = MagicMock(spec=Target)
            mock_base.name = "base-mcp"
            mock_create_target.return_value = mock_base

            mock_gen = MagicMock(spec=ToolResponseGenerator)
            mock_create_generator.return_value = mock_gen

            target = MockedTarget.from_config(config)

            assert target.target == mock_base
            assert target.mock_config.tool_response_generator == mock_gen

    def test_from_config_with_llm_generator(self):
        """Test MockedTarget.from_config with LLM generator."""
        config = OmegaConf.create(
            {
                "type": "mocked",
                "base_target": {
                    "type": "oas",
                    "name": "base-oas",
                    "spec_url": "http://example.com/openapi.json",
                },
                "tool_response_generator": {"type": "llm", "model": "gpt-4"},
            }
        )

        with (
            patch(
                "mcp_kit.targets.mocked.create_target_from_config"
            ) as mock_create_target,
            patch(
                "mcp_kit.targets.mocked.create_response_generator_from_config"
            ) as mock_create_generator,
        ):
            mock_base = MagicMock(spec=Target)
            mock_base.name = "base-oas"
            mock_create_target.return_value = mock_base

            mock_gen = MagicMock(spec=ToolResponseGenerator)
            mock_create_generator.return_value = mock_gen

            target = MockedTarget.from_config(config)

            assert target.target == mock_base
            assert target.mock_config.tool_response_generator == mock_gen

    def test_from_config_with_default_generator(self):
        """Test MockedTarget.from_config with no generator (delegates to base target)."""
        config = OmegaConf.create(
            {
                "type": "mocked",
                "base_target": {
                    "type": "mcp",
                    "name": "base-mcp",
                    "url": "http://example.com/mcp",
                },
                # No tool_response_generator specified - should delegate to base target
            }
        )

        with (
            patch(
                "mcp_kit.targets.mocked.create_target_from_config"
            ) as mock_create_target,
            patch(
                "mcp_kit.targets.mocked.create_response_generator_from_config"
            ) as mock_create_generator,
        ):
            mock_base = MagicMock(spec=Target)
            mock_base.name = "base-mcp"
            mock_create_target.return_value = mock_base

            target = MockedTarget.from_config(config)

            # Should NOT call create_response_generator_from_config since no generator specified
            mock_create_generator.assert_not_called()

            # The target should have no generator configured
            assert target.mock_config.tool_response_generator is None

    @pytest.mark.asyncio
    async def test_initialize(self, mocked_target, mock_base_target):
        """Test initialize calls base target initialize."""
        await mocked_target.initialize()
        mock_base_target.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, mocked_target, mock_base_target):
        """Test close calls base target close."""
        await mocked_target.close()
        mock_base_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools(self, mocked_target, mock_base_target):
        """Test list_tools delegates to base target."""
        expected_tools = [
            Tool(name="tool1", description="Tool 1", inputSchema={}),
            Tool(name="tool2", description="Tool 2", inputSchema={}),
        ]
        mock_base_target.list_tools.return_value = expected_tools

        result = await mocked_target.list_tools()
        assert result == expected_tools
        mock_base_target.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_success(
        self, mocked_target, mock_base_target, mock_generator
    ):
        """Test call_tool generates mock response instead of calling base target."""
        tool = Tool(name="test_tool", description="Test tool", inputSchema={})
        mock_base_target.list_tools.return_value = [tool]

        mock_content = [TextContent(type="text", text="Mock response")]
        mock_generator.generate.return_value = mock_content

        result = await mocked_target.call_tool("test_tool", {"param": "value"})

        assert result == mock_content
        mock_generator.generate.assert_called_once_with(
            "base-target", tool, {"param": "value"}
        )
        # Should NOT call the base target's call_tool
        mock_base_target.call_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_call_tool_tool_not_found(self, mocked_target, mock_base_target):
        """Test call_tool raises error when tool is not found."""
        mock_base_target.list_tools.return_value = []

        with pytest.raises(
            ValueError, match="Tool unknown_tool not found in tools for server"
        ):
            await mocked_target.call_tool("unknown_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_with_none_arguments(
        self, mocked_target, mock_base_target, mock_generator
    ):
        """Test call_tool with None arguments."""
        tool = Tool(name="test_tool", description="Test tool", inputSchema={})
        mock_base_target.list_tools.return_value = [tool]

        mock_content = [TextContent(type="text", text="Mock response")]
        mock_generator.generate.return_value = mock_content

        result = await mocked_target.call_tool("test_tool", None)

        assert result == mock_content
        mock_generator.generate.assert_called_once_with("base-target", tool, None)

    @pytest.mark.asyncio
    async def test_call_tool_llm_authentication_error(
        self, mocked_target, mock_base_target, mock_generator
    ):
        """Test call_tool handles LLM authentication errors."""
        tool = Tool(name="test_tool", description="Test tool", inputSchema={})
        mock_base_target.list_tools.return_value = [tool]

        mock_generator.generate.side_effect = LlmAuthenticationError("Auth failed")

        # Should call exit(1) when LlmAuthenticationError occurs
        with pytest.raises(SystemExit, match="1"):
            await mocked_target.call_tool("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_general_exception(
        self, mocked_target, mock_base_target, mock_generator
    ):
        """Test call_tool handles general exceptions from generator."""
        tool = Tool(name="test_tool", description="Test tool", inputSchema={})
        mock_base_target.list_tools.return_value = [tool]

        mock_generator.generate.side_effect = RuntimeError("Generation failed")

        with pytest.raises(RuntimeError, match="Generation failed"):
            await mocked_target.call_tool("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_full_lifecycle(
        self, mocked_target, mock_base_target, mock_generator
    ):
        """Test full lifecycle: initialize, list_tools, call_tool, close."""
        # Setup
        tools = [
            Tool(name="lifecycle_tool", description="Lifecycle tool", inputSchema={})
        ]
        mock_base_target.list_tools.return_value = tools
        mock_content = [TextContent(type="text", text="Lifecycle mock response")]
        mock_generator.generate.return_value = mock_content

        # Initialize
        await mocked_target.initialize()

        # List tools
        result_tools = await mocked_target.list_tools()
        assert result_tools == tools

        # Call tool (should return mock response)
        result = await mocked_target.call_tool("lifecycle_tool", {"test": "param"})
        assert result == mock_content

        # Close
        await mocked_target.close()

        # Verify calls
        mock_base_target.initialize.assert_called_once()
        mock_base_target.list_tools.assert_called()
        mock_generator.generate.assert_called_once()
        mock_base_target.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_nested_mocked_target(self):
        """Test MockedTarget wrapping another MockedTarget."""
        # Create base target
        base_target = MagicMock(spec=Target)
        base_target.name = "base"
        base_target.initialize = AsyncMock()
        base_target.close = AsyncMock()
        base_target.list_tools = AsyncMock()

        # Create first level mock
        gen1 = MagicMock(spec=ToolResponseGenerator)
        config1 = MockConfig(tool_response_generator=gen1)
        mocked1 = MockedTarget(base_target, config1)

        # Create second level mock
        gen2 = MagicMock(spec=ToolResponseGenerator)
        config2 = MockConfig(tool_response_generator=gen2)
        mocked2 = MockedTarget(mocked1, config2)

        assert mocked2.name == "base_mocked_mocked"
        assert mocked2.target == mocked1
        assert mocked1.target == base_target

    @pytest.mark.asyncio
    async def test_call_tool_caching_behavior(
        self, mocked_target, mock_base_target, mock_generator
    ):
        """Test that list_tools is called each time for call_tool (no caching)."""
        tool = Tool(name="test_tool", description="Test tool", inputSchema={})
        mock_base_target.list_tools.return_value = [tool]
        mock_content = [TextContent(type="text", text="Mock response")]
        mock_generator.generate.return_value = mock_content

        # Call tool multiple times
        await mocked_target.call_tool("test_tool", {"param": "value1"})
        await mocked_target.call_tool("test_tool", {"param": "value2"})

        # list_tools should be called each time (no caching)
        assert mock_base_target.list_tools.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling_in_initialization(
        self, mock_base_target, mock_config
    ):
        """Test error handling when base target initialization fails."""
        mock_base_target.initialize.side_effect = RuntimeError("Init failed")

        mocked_target = MockedTarget(mock_base_target, mock_config)

        with pytest.raises(RuntimeError, match="Init failed"):
            await mocked_target.initialize()

    @pytest.mark.asyncio
    async def test_error_handling_in_close(self, mock_base_target, mock_config):
        """Test error handling when base target close fails."""
        mock_base_target.close.side_effect = RuntimeError("Close failed")

        mocked_target = MockedTarget(mock_base_target, mock_config)

        with pytest.raises(RuntimeError, match="Close failed"):
            await mocked_target.close()


class TestMockedTargetPromptEngine:
    """Test cases for MockedTarget prompt engine functionality."""

    @pytest.mark.asyncio
    async def test_from_config_with_interpolation_prompt_engine(self):
        """Test MockedTarget.from_config with interpolation prompt engine."""
        config = OmegaConf.create({
            "type": "mocked",
            "base_target": {
                "type": "mcp",
                "name": "base-mcp",
                "url": "http://example.com/mcp",
            },
            "prompt_engine": {
                "type": "interpolation",
                "prompts": {
                    "test_prompt": "Execute prompt {prompt_name} with {arguments}",
                    "default": "Call {prompt_name}"
                }
            }
        })

        with (
            patch("mcp_kit.targets.mocked.create_target_from_config") as mock_create_target,
            patch("mcp_kit.targets.mocked.create_prompt_engine_from_config") as mock_create_prompt_engine,
        ):
            mock_base = MagicMock(spec=Target)
            mock_base.name = "base-mcp"
            mock_create_target.return_value = mock_base

            mock_engine = MagicMock(spec=PromptEngine)
            mock_create_prompt_engine.return_value = mock_engine

            target = MockedTarget.from_config(config)

            assert target.target == mock_base
            assert target.mock_config.prompt_engine == mock_engine
            assert target.mock_config.tool_response_generator is None

    @pytest.mark.asyncio
    async def test_get_prompt_success(self, mock_base_target, mock_prompt_engine):
        """Test get_prompt generates mock response instead of calling base target."""
        from mcp.types import Prompt, GetPromptResult, PromptMessage, TextContent

        prompt = Prompt(name="test_prompt", description="Test prompt", arguments=[])
        mock_base_target.list_prompts.return_value = [prompt]

        mock_content = GetPromptResult(
            description="Mock prompt response",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text="Mock prompt result"))]
        )
        mock_prompt_engine.generate.return_value = mock_content

        config = MockConfig(prompt_engine=mock_prompt_engine)
        mocked_target = MockedTarget(mock_base_target, config)

        result = await mocked_target.get_prompt("test_prompt", {"param": "value"})

        assert result == mock_content
        mock_prompt_engine.generate.assert_called_once_with(
            "base-target", prompt, {"param": "value"}
        )
        # Should NOT call the base target's get_prompt
        mock_base_target.get_prompt.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_prompt_delegates_to_base_when_no_prompt_engine(self):
        """Test that get_prompt delegates to base target when no prompt engine is configured."""
        from mcp.types import GetPromptResult, PromptMessage, TextContent

        # Create base target
        base_target = MagicMock(spec=Target)
        base_target.name = "base-target"
        base_target.get_prompt = AsyncMock()

        # Expected response from base target
        expected_response = GetPromptResult(
            description="Base prompt response",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text="Base response"))]
        )
        base_target.get_prompt.return_value = expected_response

        # Mock config with no prompt engine
        config = MockConfig()
        mocked_target = MockedTarget(base_target, config)

        result = await mocked_target.get_prompt("test_prompt", {"param": "value"})

        # Should delegate to base target
        assert result == expected_response
        base_target.get_prompt.assert_called_once_with("test_prompt", {"param": "value"})

    @pytest.mark.asyncio
    async def test_get_prompt_prompt_not_found(self, mock_base_target, mock_prompt_engine):
        """Test get_prompt raises error when prompt is not found."""
        mock_base_target.list_prompts.return_value = []

        config = MockConfig(prompt_engine=mock_prompt_engine)
        mocked_target = MockedTarget(mock_base_target, config)

        with pytest.raises(
            ValueError, match="Prompt unknown_prompt not found in prompts for server"
        ):
            await mocked_target.get_prompt("unknown_prompt", {"param": "value"})

    @pytest.mark.asyncio
    async def test_integration_with_real_interpolation_prompt_engine(self):
        """Integration test with actual InterpolationPromptEngine."""
        from mcp_kit.prompts.interpolation import InterpolationPromptEngine
        from mcp.types import Prompt

        # Create base target
        base_target = MagicMock(spec=Target)
        base_target.name = "test-target"
        base_target.list_prompts = AsyncMock()

        # Create real InterpolationPromptEngine
        prompts_config = {
            "greeting": InterpolationPrompt(
                text="Hello {name}, welcome to {service}!",
                defaults={"service": "our platform"}
            ),
        }
        prompt_engine = InterpolationPromptEngine(prompts_config)

        # Create MockedTarget with prompt engine
        config = MockConfig(prompt_engine=prompt_engine)
        mocked_target = MockedTarget(base_target, config)

        # Setup prompt
        prompt = Prompt(name="greeting", description="Greeting prompt", arguments=[])
        base_target.list_prompts.return_value = [prompt]

        # Test with explicit service override
        result = await mocked_target.get_prompt("greeting", {"name": "Alice", "service": "MCP"})
        assert result.description == "Interpolated response for prompt 'greeting' from test-target"
        assert len(result.messages) == 1
        assert result.messages[0].content.text == "Hello Alice, welcome to MCP!"

        # Test with default service value (service not provided)
        result_default = await mocked_target.get_prompt("greeting", {"name": "Bob"})
        assert result_default.description == "Interpolated response for prompt 'greeting' from test-target"
        assert len(result_default.messages) == 1
        assert result_default.messages[0].content.text == "Hello Bob, welcome to our platform!"
        assert result.messages[0].role == "user"
