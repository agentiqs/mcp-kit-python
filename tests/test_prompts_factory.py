"""Tests for create_prompts_from_config function."""

import pytest
from mcp.types import Prompt, PromptArgument
from omegaconf import OmegaConf

from mcp_kit.factory import create_prompts_from_config


class TestCreatePromptsFromConfig:
    """Test cases for create_prompts_from_config function."""

    def test_create_prompts_from_list(self):
        """Test creating prompts from list configuration."""
        config = OmegaConf.create(
            {
                "prompts": [
                    {"name": "prompt1", "description": "First prompt"},
                    {
                        "name": "prompt2",
                        "description": "Second prompt",
                        "arguments": [
                            {
                                "name": "param1",
                                "description": "First parameter",
                                "required": True,
                            }
                        ],
                    },
                ]
            }
        )

        prompts = create_prompts_from_config(config)
        assert len(prompts) == 2
        assert all(isinstance(prompt, Prompt) for prompt in prompts)
        assert prompts[0].name == "prompt1"
        assert prompts[0].description == "First prompt"
        assert prompts[0].arguments is None
        assert prompts[1].name == "prompt2"
        assert prompts[1].description == "Second prompt"
        assert prompts[1].arguments is not None
        assert len(prompts[1].arguments) == 1

    def test_create_prompts_empty_list(self):
        """Test creating prompts from empty list."""
        config = OmegaConf.create({"prompts": []})

        prompts = create_prompts_from_config(config)
        assert prompts == []

    def test_create_prompts_no_prompts_config(self):
        """Test creating prompts when no prompts configuration is provided."""
        config = OmegaConf.create({})

        prompts = create_prompts_from_config(config)
        assert prompts is None

    def test_create_prompts_minimal_config(self):
        """Test creating prompts with minimal configuration."""
        config = OmegaConf.create(
            {"prompts": [{"name": "minimal_prompt", "description": "Minimal prompt"}]}
        )

        prompts = create_prompts_from_config(config)
        assert prompts is not None
        assert len(prompts) == 1
        assert prompts[0].name == "minimal_prompt"
        assert prompts[0].description == "Minimal prompt"
        assert prompts[0].arguments is None

    def test_create_prompts_with_complex_arguments(self):
        """Test creating prompts with complex argument configurations."""
        config = OmegaConf.create(
            {
                "prompts": [
                    {
                        "name": "complex_prompt",
                        "description": "Prompt with complex arguments",
                        "arguments": [
                            {
                                "name": "required_param",
                                "description": "A required parameter",
                                "required": True,
                            },
                            {
                                "name": "optional_param",
                                "description": "An optional parameter",
                                "required": False,
                            },
                            {
                                "name": "default_required_param",
                                "description": "Parameter with default required value",
                                # required defaults to None/False if not specified
                            },
                        ],
                    }
                ]
            }
        )

        prompts = create_prompts_from_config(config)
        assert prompts is not None
        assert len(prompts) == 1
        prompt = prompts[0]
        assert prompt.name == "complex_prompt"
        assert prompt.arguments is not None
        assert len(prompt.arguments) == 3

        # Check first argument
        arg1 = prompt.arguments[0]
        assert isinstance(arg1, PromptArgument)
        assert arg1.name == "required_param"
        assert arg1.description == "A required parameter"
        assert arg1.required is True

        # Check second argument
        arg2 = prompt.arguments[1]
        assert arg2.name == "optional_param"
        assert arg2.description == "An optional parameter"
        assert arg2.required is False

        # Check third argument
        arg3 = prompt.arguments[2]
        assert arg3.name == "default_required_param"
        assert arg3.description == "Parameter with default required value"
        assert arg3.required is None  # Default value

    def test_create_prompts_missing_required_fields(self):
        """Test creating prompts with missing required fields."""
        # Missing name
        config = OmegaConf.create(
            {"prompts": [{"description": "Prompt without name"}]}
        )

        with pytest.raises(
            Exception
        ):  # Could be various exceptions depending on Prompt validation
            create_prompts_from_config(config)

        # Missing description is allowed (description is optional)
        config = OmegaConf.create(
            {"prompts": [{"name": "prompt_without_description"}]}
        )

        prompts = create_prompts_from_config(config)
        assert prompts is not None
        assert len(prompts) == 1
        assert prompts[0].name == "prompt_without_description"
        assert prompts[0].description is None

    def test_create_prompts_preserves_order(self):
        """Test that prompt creation preserves order."""
        config = OmegaConf.create(
            {
                "prompts": [
                    {"name": f"prompt_{i}", "description": f"Prompt {i}"}
                    for i in range(10)
                ]
            }
        )

        prompts = create_prompts_from_config(config)
        assert prompts is not None
        assert len(prompts) == 10
        for i, prompt in enumerate(prompts):
            assert prompt.name == f"prompt_{i}"
            assert prompt.description == f"Prompt {i}"

    def test_create_prompts_with_duplicate_names(self):
        """Test creating prompts with duplicate names."""
        config = OmegaConf.create(
            {
                "prompts": [
                    {"name": "duplicate_prompt", "description": "First instance"},
                    {"name": "duplicate_prompt", "description": "Second instance"},
                ]
            }
        )

        # Should create both prompts (no deduplication at this level)
        prompts = create_prompts_from_config(config)
        assert prompts is not None
        assert len(prompts) == 2
        assert prompts[0].name == "duplicate_prompt"
        assert prompts[1].name == "duplicate_prompt"
        assert prompts[0].description != prompts[1].description

    def test_create_prompts_arguments_missing_name(self):
        """Test creating prompts with argument missing required name."""
        config = OmegaConf.create(
            {
                "prompts": [
                    {
                        "name": "prompt_with_invalid_arg",
                        "description": "Prompt with invalid argument",
                        "arguments": [
                            {
                                "description": "Argument without name",
                                "required": True,
                            }
                        ],
                    }
                ]
            }
        )

        with pytest.raises(
            Exception
        ):  # Could be various exceptions depending on PromptArgument validation
            create_prompts_from_config(config)

    def test_create_prompts_arguments_preserves_order(self):
        """Test that argument creation preserves order."""
        config = OmegaConf.create(
            {
                "prompts": [
                    {
                        "name": "ordered_args_prompt",
                        "description": "Prompt with ordered arguments",
                        "arguments": [
                            {
                                "name": f"arg_{i}",
                                "description": f"Argument {i}",
                                "required": i % 2 == 0,  # Even indexes are required
                            }
                            for i in range(5)
                        ],
                    }
                ]
            }
        )

        prompts = create_prompts_from_config(config)
        assert prompts is not None
        assert len(prompts) == 1
        prompt = prompts[0]
        assert len(prompt.arguments) == 5
        for i, arg in enumerate(prompt.arguments):
            assert arg.name == f"arg_{i}"
            assert arg.description == f"Argument {i}"
            assert arg.required == (i % 2 == 0)
