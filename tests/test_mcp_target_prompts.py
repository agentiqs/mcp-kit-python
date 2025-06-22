"""Tests for MCP target prompt functionality."""

import pytest
from mcp.types import Prompt, PromptArgument
from omegaconf import OmegaConf

from mcp_kit.targets.mcp import McpTarget


class TestMcpTargetPrompts:
    """Test cases for MCP target prompt functionality."""

    def test_mcp_target_with_predefined_prompts(self):
        """Test MCP target with predefined prompts."""
        # Create prompts manually
        prompt = Prompt(
            name="test_prompt",
            description="A test prompt",
            arguments=[
                PromptArgument(
                    name="param1",
                    description="First parameter",
                    required=True,
                )
            ],
        )

        target = McpTarget(
            name="test_target",
            prompts=[prompt],
        )

        assert target.prompts is not None
        assert len(target.prompts) == 1
        assert target.prompts[0].name == "test_prompt"

    def test_mcp_target_from_config_with_prompts(self):
        """Test creating MCP target from config with prompts."""
        config = OmegaConf.create(
            {
                "name": "test_target",
                "prompts": [
                    {
                        "name": "config_prompt",
                        "description": "A prompt from config",
                        "arguments": [
                            {
                                "name": "user_input",
                                "description": "User input parameter",
                                "required": True,
                            }
                        ],
                    }
                ],
            }
        )

        target = McpTarget.from_config(config)
        assert target.name == "test_target"
        assert target.prompts is not None
        assert len(target.prompts) == 1
        prompt = target.prompts[0]
        assert prompt.name == "config_prompt"
        assert prompt.description == "A prompt from config"
        assert len(prompt.arguments) == 1
        assert prompt.arguments[0].name == "user_input"

    def test_mcp_target_no_prompts(self):
        """Test MCP target with no prompts."""
        target = McpTarget(name="no_prompts_target")
        assert target.prompts is None

    def test_mcp_target_from_config_no_prompts(self):
        """Test creating MCP target from config with no prompts."""
        config = OmegaConf.create({"name": "no_prompts_target"})

        target = McpTarget.from_config(config)
        assert target.name == "no_prompts_target"
        assert target.prompts is None

    @pytest.mark.asyncio
    async def test_list_prompts_with_predefined_prompts(self):
        """Test list_prompts method with predefined prompts."""
        prompt = Prompt(name="test_prompt", description="A test prompt")
        target = McpTarget(name="test_target", prompts=[prompt])

        prompts = await target.list_prompts()
        assert len(prompts) == 1
        assert prompts[0].name == "test_prompt"

    @pytest.mark.asyncio
    async def test_list_prompts_no_prompts_no_mcp(self):
        """Test list_prompts method with no prompts and no MCP connection."""
        target = McpTarget(name="test_target")

        with pytest.raises(ValueError, match="No prompts available"):
            await target.list_prompts()

    @pytest.mark.asyncio
    async def test_get_prompt_no_mcp(self):
        """Test get_prompt method with no MCP connection."""
        target = McpTarget(name="test_target")

        with pytest.raises(ValueError, match="MCP client is not initialized"):
            await target.get_prompt("test_prompt")
