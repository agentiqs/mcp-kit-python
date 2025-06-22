"""Tests for multiplex target implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import McpError, Tool
from mcp.types import TextContent, Prompt, PromptArgument, GetPromptResult
from omegaconf import OmegaConf

from mcp_kit.targets.interfaces import Target
from mcp_kit.targets.multiplex import MultiplexTarget


@pytest.fixture
def mock_target1():
    """Create first mock target."""
    target = MagicMock(spec=Target)
    target.name = "target1"
    target.initialize = AsyncMock()
    target.close = AsyncMock()
    target.list_tools = AsyncMock()
    target.call_tool = AsyncMock()
    target.list_prompts = AsyncMock()
    target.get_prompt = AsyncMock()
    return target


@pytest.fixture
def mock_target2():
    """Create second mock target."""
    target = MagicMock(spec=Target)
    target.name = "target2"
    target.initialize = AsyncMock()
    target.close = AsyncMock()
    target.list_tools = AsyncMock()
    target.call_tool = AsyncMock()
    target.list_prompts = AsyncMock()
    target.get_prompt = AsyncMock()
    return target


@pytest.fixture
def multiplex_target(mock_target1, mock_target2):
    """Create a MultiplexTarget with mock targets."""
    return MultiplexTarget("multi-target", mock_target1, mock_target2)


class TestMultiplexTarget:
    """Test cases for MultiplexTarget class."""

    def test_init_with_targets(self, mock_target1, mock_target2):
        """Test MultiplexTarget initialization with targets."""
        target = MultiplexTarget("test-multiplex", mock_target1, mock_target2)
        assert target.name == "test-multiplex"
        assert len(target._targets_dict) == 2
        assert target._targets_dict["target1"] == mock_target1
        assert target._targets_dict["target2"] == mock_target2

    def test_init_single_target(self, mock_target1):
        """Test MultiplexTarget initialization with single target."""
        target = MultiplexTarget("single-multiplex", mock_target1)
        assert target.name == "single-multiplex"
        assert len(target._targets_dict) == 1
        assert target._targets_dict["target1"] == mock_target1

    def test_init_no_targets(self):
        """Test MultiplexTarget initialization with no targets."""
        target = MultiplexTarget("empty-multiplex")
        assert target.name == "empty-multiplex"
        assert len(target._targets_dict) == 0

    def test_from_config(self):
        """Test MultiplexTarget.from_config."""
        config = OmegaConf.create(
            {
                "type": "multiplex",
                "name": "config-multiplex",
                "targets": [
                    {
                        "type": "mcp",
                        "name": "config-target1",
                        "url": "http://example1.com",
                    },
                    {
                        "type": "mcp",
                        "name": "config-target2",
                        "url": "http://example2.com",
                    },
                ],
            }
        )

        with patch(
            "mcp_kit.targets.multiplex.create_target_from_config"
        ) as mock_create:
            mock_target1 = MagicMock(spec=Target)
            mock_target1.name = "config-target1"
            mock_target2 = MagicMock(spec=Target)
            mock_target2.name = "config-target2"
            mock_create.side_effect = [mock_target1, mock_target2]

            target = MultiplexTarget.from_config(config)
            assert target.name == "config-multiplex"
            assert len(target._targets_dict) == 2
            assert target._targets_dict["config-target1"] == mock_target1
            assert target._targets_dict["config-target2"] == mock_target2

    @pytest.mark.asyncio
    async def test_initialize(self, multiplex_target, mock_target1, mock_target2):
        """Test initialize calls initialize on all targets."""
        await multiplex_target.initialize()

        mock_target1.initialize.assert_called_once()
        mock_target2.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_empty_targets(self):
        """Test initialize with no targets."""
        target = MultiplexTarget("empty")
        # Should not raise any errors
        await target.initialize()

    @pytest.mark.asyncio
    async def test_close(self, multiplex_target, mock_target1, mock_target2):
        """Test close calls close on all targets."""
        await multiplex_target.close()

        mock_target1.close.assert_called_once()
        mock_target2.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_empty_targets(self):
        """Test close with no targets."""
        target = MultiplexTarget("empty")
        # Should not raise any errors
        await target.close()

    @pytest.mark.asyncio
    async def test_list_tools(self, multiplex_target, mock_target1, mock_target2):
        """Test list_tools combines tools from all targets with prefixes."""
        tools1 = [Tool(name="tool1", description="Tool 1 from target1", inputSchema={})]
        tools2 = [Tool(name="tool2", description="Tool 2 from target2", inputSchema={})]

        mock_target1.list_tools.return_value = tools1
        mock_target2.list_tools.return_value = tools2

        result = await multiplex_target.list_tools()

        assert len(result) == 2
        # Tools should be prefixed with target name
        assert result[0].name == "target1.tool1"
        assert result[0].description == "Tool 1 from target1"
        assert result[1].name == "target2.tool2"
        assert result[1].description == "Tool 2 from target2"

    @pytest.mark.asyncio
    async def test_list_tools_empty_targets(self):
        """Test list_tools with no targets."""
        target = MultiplexTarget("empty")
        result = await target.list_tools()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_tools_some_empty(self, mock_target1, mock_target2):
        """Test list_tools when some targets have no tools."""
        mock_target1.list_tools.return_value = [
            Tool(name="tool1", description="Tool 1", inputSchema={})
        ]
        mock_target2.list_tools.return_value = []

        target = MultiplexTarget("mixed", mock_target1, mock_target2)
        result = await target.list_tools()

        assert len(result) == 1
        assert result[0].name == "target1.tool1"

    @pytest.mark.asyncio
    async def test_call_tool_success(self, multiplex_target, mock_target1):
        """Test successful call_tool with prefixed tool name."""
        mock_content = [TextContent(type="text", text="Tool response")]
        mock_target1.call_tool.return_value = mock_content

        result = await multiplex_target.call_tool("target1.tool1", {"param": "value"})

        assert result == mock_content
        mock_target1.call_tool.assert_called_once_with(
            "target1.tool1", {"param": "value"}
        )

    @pytest.mark.asyncio
    async def test_call_tool_no_prefix(self, multiplex_target):
        """Test call_tool with tool name without prefix raises error."""
        with pytest.raises(
            McpError,
            match="Invalid tool name 'unprefixed_tool', expected format 'target_name.tool_name'",
        ):
            await multiplex_target.call_tool("unprefixed_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_unknown_target(self, multiplex_target):
        """Test call_tool with unknown target raises error."""
        with pytest.raises(McpError, match="Tool 'unknown.tool' not found"):
            await multiplex_target.call_tool("unknown.tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_propagates_exceptions(
        self, multiplex_target, mock_target1
    ):
        """Test call_tool propagates exceptions from underlying targets."""
        mock_target1.call_tool.side_effect = RuntimeError("Tool execution failed")

        with pytest.raises(RuntimeError, match="Tool execution failed"):
            await multiplex_target.call_tool("target1.tool1", {"param": "value"})

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self, multiplex_target, mock_target1, mock_target2
    ):
        """Test that concurrent operations work correctly."""
        # Setup async responses
        tools1 = [Tool(name="tool1", description="Tool 1", inputSchema={})]
        tools2 = [Tool(name="tool2", description="Tool 2", inputSchema={})]
        mock_target1.list_tools.return_value = tools1
        mock_target2.list_tools.return_value = tools2

        content1 = [TextContent(type="text", text="Response 1")]
        content2 = [TextContent(type="text", text="Response 2")]
        mock_target1.call_tool.return_value = content1
        mock_target2.call_tool.return_value = content2

        # Run concurrent operations

        async def list_and_call():
            tools = await multiplex_target.list_tools()
            call1 = await multiplex_target.call_tool("target1.tool1", {})
            call2 = await multiplex_target.call_tool("target2.tool2", {})
            return tools, call1, call2

        tools, call1, call2 = await list_and_call()

        assert len(tools) == 2
        assert call1 == content1
        assert call2 == content2

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, multiplex_target, mock_target1, mock_target2):
        """Test full lifecycle: initialize, list_tools, call_tool, close."""
        # Setup
        tools1 = [
            Tool(name="lifecycle1", description="Lifecycle tool 1", inputSchema={})
        ]
        tools2 = [
            Tool(name="lifecycle2", description="Lifecycle tool 2", inputSchema={})
        ]
        mock_target1.list_tools.return_value = tools1
        mock_target2.list_tools.return_value = tools2

        content1 = [TextContent(type="text", text="Lifecycle response 1")]
        content2 = [TextContent(type="text", text="Lifecycle response 2")]
        mock_target1.call_tool.return_value = content1
        mock_target2.call_tool.return_value = content2

        # Initialize
        await multiplex_target.initialize()

        # List tools
        tools = await multiplex_target.list_tools()
        assert len(tools) == 2
        assert tools[0].name == "target1.lifecycle1"
        assert tools[1].name == "target2.lifecycle2"

        # Call tools
        result1 = await multiplex_target.call_tool(
            "target1.lifecycle1", {"test": "param1"}
        )
        assert result1 == content1

        result2 = await multiplex_target.call_tool(
            "target2.lifecycle2", {"test": "param2"}
        )
        assert result2 == content2

        # Close
        await multiplex_target.close()

        # Verify all methods were called
        mock_target1.initialize.assert_called_once()
        mock_target2.initialize.assert_called_once()
        mock_target1.close.assert_called_once()
        mock_target2.close.assert_called_once()

    def test_name_property(self, multiplex_target):
        """Test name property."""
        assert multiplex_target.name == "multi-target"

    @pytest.mark.asyncio
    async def test_initialize_partial_failure(self, mock_target1, mock_target2):
        """Test initialize when one target fails."""
        mock_target1.initialize = AsyncMock()
        mock_target2.initialize = AsyncMock(side_effect=RuntimeError("Init failed"))

        target = MultiplexTarget("test", mock_target1, mock_target2)

        with pytest.raises(RuntimeError, match="Init failed"):
            await target.initialize()

        # First target should still have been initialized
        mock_target1.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_partial_failure(self, mock_target1, mock_target2):
        """Test close when one target fails."""
        mock_target1.close = AsyncMock()
        mock_target2.close = AsyncMock(side_effect=RuntimeError("Close failed"))

        target = MultiplexTarget("test", mock_target1, mock_target2)

        with pytest.raises(RuntimeError, match="Close failed"):
            await target.close()

        # First target should still have been closed
        mock_target1.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_prompts(self, multiplex_target, mock_target1, mock_target2):
        """Test list_prompts returns namespaced prompts from all targets."""
        # Setup prompts for each target
        prompt1 = Prompt(name="prompt1", description="First prompt")
        prompt2 = Prompt(
            name="prompt2",
            description="Second prompt",
            arguments=[
                PromptArgument(name="arg1", description="Argument 1", required=True)
            ]
        )
        prompt3 = Prompt(name="prompt3", description="Third prompt")

        mock_target1.list_prompts.return_value = [prompt1, prompt2]
        mock_target2.list_prompts.return_value = [prompt3]

        prompts = await multiplex_target.list_prompts()

        # Should have 3 prompts total
        assert len(prompts) == 3

        # Check namespacing
        prompt_names = [p.name for p in prompts]
        assert "target1.prompt1" in prompt_names
        assert "target1.prompt2" in prompt_names
        assert "target2.prompt3" in prompt_names

        # Check that original descriptions and arguments are preserved
        for prompt in prompts:
            if prompt.name == "target1.prompt1":
                assert prompt.description == "First prompt"
                assert prompt.arguments is None
            elif prompt.name == "target1.prompt2":
                assert prompt.description == "Second prompt"
                assert prompt.arguments is not None
                assert len(prompt.arguments) == 1
                assert prompt.arguments[0].name == "arg1"
            elif prompt.name == "target2.prompt3":
                assert prompt.description == "Third prompt"

        # Verify calls
        mock_target1.list_prompts.assert_called_once()
        mock_target2.list_prompts.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_prompts_empty_targets(self, multiplex_target, mock_target1, mock_target2):
        """Test list_prompts with empty targets."""
        mock_target1.list_prompts.return_value = []
        mock_target2.list_prompts.return_value = []

        prompts = await multiplex_target.list_prompts()
        assert prompts == []

    @pytest.mark.asyncio
    async def test_list_prompts_some_empty(self, multiplex_target, mock_target1, mock_target2):
        """Test list_prompts when some targets have no prompts."""
        prompt1 = Prompt(name="only_prompt", description="Only prompt")

        mock_target1.list_prompts.return_value = [prompt1]
        mock_target2.list_prompts.return_value = []

        prompts = await multiplex_target.list_prompts()
        assert len(prompts) == 1
        assert prompts[0].name == "target1.only_prompt"

    @pytest.mark.asyncio
    async def test_get_prompt_success(self, multiplex_target, mock_target1, mock_target2):
        """Test get_prompt routes to correct target."""
        mock_result = GetPromptResult(
            description="Test prompt result",
            messages=[]
        )
        mock_target1.get_prompt.return_value = mock_result

        result = await multiplex_target.get_prompt(
            "target1.test_prompt",
            {"arg1": "value1"}
        )

        assert result == mock_result
        mock_target1.get_prompt.assert_called_once_with(
            "target1.test_prompt",
            {"arg1": "value1"}
        )
        mock_target2.get_prompt.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_prompt_no_prefix(self, multiplex_target):
        """Test get_prompt with prompt name without target prefix."""
        with pytest.raises(
            McpError,
            match="Invalid prompt name 'no_prefix_prompt', expected format 'target_name.prompt_name'",
        ):
            await multiplex_target.get_prompt("no_prefix_prompt")

    @pytest.mark.asyncio
    async def test_get_prompt_unknown_target(self, multiplex_target):
        """Test get_prompt with unknown target name."""
        with pytest.raises(McpError, match="Prompt 'unknown_target.test_prompt' not found"):
            await multiplex_target.get_prompt("unknown_target.test_prompt")

    @pytest.mark.asyncio
    async def test_get_prompt_propagates_exceptions(self, multiplex_target, mock_target1):
        """Test get_prompt propagates exceptions from targets."""
        mock_target1.get_prompt.side_effect = RuntimeError("Prompt error")

        with pytest.raises(RuntimeError, match="Prompt error"):
            await multiplex_target.get_prompt("target1.test_prompt")

    def test_get_namespaced_name_generic(self, multiplex_target, mock_target1):
        """Test the generic _get_namespaced_name method works for both tools and prompts."""
        # Test with tool name
        tool_name = multiplex_target._get_namespaced_name(mock_target1, "my_tool")
        assert tool_name == "target1.my_tool"

        # Test with prompt name
        prompt_name = multiplex_target._get_namespaced_name(mock_target1, "my_prompt")
        assert prompt_name == "target1.my_prompt"

    def test_get_namespace_from_name_generic(self, multiplex_target):
        """Test the generic _get_namespace_from_name method works for both tools and prompts."""
        # Test with tool
        target_name = multiplex_target._get_namespace_from_name("target1.my_tool", "tool")
        assert target_name == "target1"

        # Test with prompt
        target_name = multiplex_target._get_namespace_from_name("target1.my_prompt", "prompt")
        assert target_name == "target1"

    def test_get_namespace_from_name_invalid_format(self, multiplex_target):
        """Test _get_namespace_from_name with invalid format."""
        with pytest.raises(
            McpError,
            match="Invalid tool name 'no_dots', expected format 'target_name.tool_name'",
        ):
            multiplex_target._get_namespace_from_name("no_dots", "tool")

        with pytest.raises(
            McpError,
            match="Invalid prompt name 'no_dots', expected format 'target_name.prompt_name'",
        ):
            multiplex_target._get_namespace_from_name("no_dots", "prompt")

    @pytest.mark.asyncio
    async def test_prompts_and_tools_together(self, multiplex_target, mock_target1, mock_target2):
        """Test that prompts and tools work together correctly."""
        # Setup tools
        tool1 = Tool(name="tool1", description="First tool", inputSchema={})
        tool2 = Tool(name="tool2", description="Second tool", inputSchema={})
        mock_target1.list_tools.return_value = [tool1]
        mock_target2.list_tools.return_value = [tool2]

        # Setup prompts
        prompt1 = Prompt(name="prompt1", description="First prompt")
        prompt2 = Prompt(name="prompt2", description="Second prompt")
        mock_target1.list_prompts.return_value = [prompt1]
        mock_target2.list_prompts.return_value = [prompt2]

        # Test both work independently
        tools = await multiplex_target.list_tools()
        prompts = await multiplex_target.list_prompts()

        assert len(tools) == 2
        assert len(prompts) == 2

        # Check namespacing is consistent
        assert "target1.tool1" in [t.name for t in tools]
        assert "target1.prompt1" in [p.name for p in prompts]
        assert "target2.tool2" in [t.name for t in tools]
        assert "target2.prompt2" in [p.name for p in prompts]
