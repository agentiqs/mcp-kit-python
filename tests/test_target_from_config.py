import pytest
from omegaconf import OmegaConf

from mcp_kit.factory import create_target_from_config
from mcp_kit.generators import LlmResponseGenerator, RandomResponseGenerator
from mcp_kit.prompts.interpolation import InterpolationPromptEngine
from mcp_kit.targets import McpTarget, MockedTarget, MultiplexTarget, OasTarget


class TestTargetFromConfig:
    """Test cases for individual Target.from_config factory methods."""

    def test_mcp_target_from_config(self):
        """Test McpTarget.from_config factory method."""
        config_data = {
            "type": "mcp",
            "name": "test-mcp",
            "url": "http://example.com/mcp",
            "headers": {"Authorization": "Bearer token123"},
        }

        config = OmegaConf.create(config_data)
        target = McpTarget.from_config(config)

        assert isinstance(target, McpTarget)
        assert target.name == "test-mcp"
        assert target.url == "http://example.com/mcp"
        assert target.headers == {"Authorization": "Bearer token123"}

    def test_mcp_target_from_config_minimal(self):
        """Test McpTarget.from_config with minimal configuration."""
        config_data = {"type": "mcp", "name": "minimal-mcp"}

        config = OmegaConf.create(config_data)
        target = McpTarget.from_config(config)

        assert isinstance(target, McpTarget)
        assert target.name == "minimal-mcp"
        assert target.url is None
        assert target.headers is None
        assert target.tools is None

    def test_oas_target_from_config(self):
        """Test OasTarget.from_config factory method."""
        config_data = {"type": "oas", "name": "test-oas", "spec_url": "http://example.com/openapi.json"}

        config = OmegaConf.create(config_data)
        target = OasTarget.from_config(config)

        assert isinstance(target, OasTarget)
        assert target.name == "test-oas"
        assert target._spec_url == "http://example.com/openapi.json"

    def test_mocked_target_from_config_random_generator(self):
        """Test MockedTarget.from_config with random generator."""
        config_data = {
            "type": "mocked",
            "base_target": {"type": "mcp", "name": "base-mcp", "url": "http://example.com/mcp"},
            "tool_response_generator": {"type": "random"},
        }

        config = OmegaConf.create(config_data)
        target = MockedTarget.from_config(config)

        assert isinstance(target, MockedTarget)
        assert isinstance(target.target, McpTarget)
        assert target.target.name == "base-mcp"
        assert isinstance(target.mock_config.tool_response_generator, RandomResponseGenerator)

    def test_mocked_target_from_config_llm_generator(self):
        """Test MockedTarget.from_config with LLM generator."""
        config_data = {
            "type": "mocked",
            "base_target": {"type": "oas", "name": "base-oas", "spec_url": "http://example.com/openapi.json"},
            "tool_response_generator": {"type": "llm", "model": "gpt-4"},
        }

        config = OmegaConf.create(config_data)
        target = MockedTarget.from_config(config)

        assert isinstance(target, MockedTarget)
        assert isinstance(target.target, OasTarget)
        assert isinstance(target.mock_config.tool_response_generator, LlmResponseGenerator)

    def test_mocked_target_from_config_default_generator(self):
        """Test MockedTarget.from_config with no generator (delegates to base target)."""
        config_data = {
            "type": "mocked",
            "base_target": {"type": "mcp", "name": "base-mcp", "url": "http://example.com/mcp"},
            # No tool_response_generator specified - should delegate to base target
        }

        config = OmegaConf.create(config_data)
        target = MockedTarget.from_config(config)

        assert isinstance(target, MockedTarget)
        assert target.mock_config.tool_response_generator is None

    def test_multiplex_target_from_config(self):
        """Test MultiplexTarget.from_config factory method."""
        config_data = {
            "type": "multiplex",
            "name": "multi-target",
            "targets": [
                {"type": "mcp", "name": "mcp-1", "url": "http://example.com/mcp1"},
                {"type": "oas", "name": "oas-1", "spec_url": "http://example.com/openapi.json"},
            ],
        }

        config = OmegaConf.create(config_data)
        target = MultiplexTarget.from_config(config)

        assert isinstance(target, MultiplexTarget)
        assert target.name == "multi-target"
        assert len(target._targets_dict) == 2
        assert isinstance(target._targets_dict["mcp-1"], McpTarget)
        assert isinstance(target._targets_dict["oas-1"], OasTarget)

    def test_create_target_from_config_factory(self):
        """Test the create_target_from_config factory function."""
        config_data = {"type": "mcp", "name": "factory-test", "url": "http://example.com/mcp"}

        config = OmegaConf.create(config_data)
        target = create_target_from_config(config)

        assert isinstance(target, McpTarget)
        assert target.name == "factory-test"

    def test_create_target_from_config_invalid_type(self):
        """Test that create_target_from_config raises error for invalid type."""
        config_data = {"type": "invalid_type", "name": "test"}

        config = OmegaConf.create(config_data)

        with pytest.raises(ValueError, match="Unknown target type 'invalid_type'"):
            create_target_from_config(config)

    def test_mocked_target_invalid_generator_type(self):
        """Test that MockedTarget.from_config raises error for invalid generator type."""
        config_data = {
            "type": "mocked",
            "base_target": {"type": "mcp", "name": "base-mcp", "url": "http://example.com/mcp"},
            "tool_response_generator": {"type": "invalid_generator"},
        }

        config = OmegaConf.create(config_data)

        with pytest.raises(ValueError, match="Unknown generator type 'invalid_generator'"):
            MockedTarget.from_config(config)

    def test_nested_mocked_target_from_config(self):
        """Test creating a mocked target with another mocked target as base."""
        config_data = {
            "type": "mocked",
            "base_target": {
                "type": "mocked",
                "base_target": {"type": "mcp", "name": "nested-mcp", "url": "http://example.com/mcp"},
                "tool_response_generator": {"type": "random"},
            },
            "tool_response_generator": {"type": "llm", "model": "gpt-4"},
        }

        config = OmegaConf.create(config_data)
        target = MockedTarget.from_config(config)

        assert isinstance(target, MockedTarget)
        assert isinstance(target.target, MockedTarget)  # Base is also mocked
        assert isinstance(target.target.target, McpTarget)  # Nested base is MCP
        assert isinstance(target.mock_config.tool_response_generator, LlmResponseGenerator)
        assert isinstance(target.target.mock_config.tool_response_generator, RandomResponseGenerator)

    def test_mocked_target_from_config_with_prompt_engine(self):
        """Test MockedTarget.from_config with interpolation prompt engine."""
        config_data = {
            "type": "mocked",
            "base_target": {"type": "mcp", "name": "base-mcp", "url": "http://example.com/mcp"},
            "prompt_engine": {
                "type": "interpolation",
                "prompts": {
                    "test_prompt": {
                        "text": "Execute prompt {prompt_name} with {arguments}"
                    },
                    "default": {
                        "text": "Call {prompt_name}"
                    }
                }
            },
        }

        config = OmegaConf.create(config_data)
        target = MockedTarget.from_config(config)

        assert isinstance(target, MockedTarget)
        assert isinstance(target.target, McpTarget)
        assert target.target.name == "base-mcp"
        assert isinstance(target.mock_config.prompt_engine, InterpolationPromptEngine)
        assert target.mock_config.tool_response_generator is None

    def test_mocked_target_from_config_with_both_generators(self):
        """Test MockedTarget.from_config with both tool response generator and prompt engine."""
        config_data = {
            "type": "mocked",
            "base_target": {"type": "oas", "name": "base-oas", "spec_url": "http://example.com/openapi.json"},
            "tool_response_generator": {"type": "llm", "model": "gpt-4"},
            "prompt_engine": {
                "type": "interpolation",
                "prompts": {
                    "greeting": {
                        "text": "Hello {name}!"
                    },
                    "default": {
                        "text": "Default prompt"
                    }
                }
            },
        }

        config = OmegaConf.create(config_data)
        target = MockedTarget.from_config(config)

        assert isinstance(target, MockedTarget)
        assert isinstance(target.target, OasTarget)
        assert isinstance(target.mock_config.tool_response_generator, LlmResponseGenerator)
        assert isinstance(target.mock_config.prompt_engine, InterpolationPromptEngine)

    def test_mocked_target_invalid_prompt_engine_type(self):
        """Test that MockedTarget.from_config raises error for invalid prompt engine type."""
        config_data = {
            "type": "mocked",
            "base_target": {"type": "mcp", "name": "base-mcp", "url": "http://example.com/mcp"},
            "prompt_engine": {"type": "invalid_engine"},
        }

        config = OmegaConf.create(config_data)

        with pytest.raises(ValueError, match="Unknown engine type 'invalid_engine'"):
            MockedTarget.from_config(config)

    def test_nested_mocked_target_with_prompt_engines(self):
        """Test creating nested mocked targets with different prompt engines."""
        config_data = {
            "type": "mocked",
            "base_target": {
                "type": "mocked",
                "base_target": {"type": "mcp", "name": "nested-mcp", "url": "http://example.com/mcp"},
                "prompt_engine": {
                    "type": "interpolation",
                    "prompts": {
                        "inner": {
                            "text": "Inner prompt for {name}"
                        }
                    }
                },
            },
            "prompt_engine": {
                "type": "interpolation",
                "prompts": {
                    "outer": {
                        "text": "Outer prompt for {name}"
                    }
                }
            },
        }

        config = OmegaConf.create(config_data)
        target = MockedTarget.from_config(config)

        assert isinstance(target, MockedTarget)
        assert isinstance(target.target, MockedTarget)  # Base is also mocked
        assert isinstance(target.target.target, McpTarget)  # Nested base is MCP
        assert isinstance(target.mock_config.prompt_engine, InterpolationPromptEngine)
        assert isinstance(target.target.mock_config.prompt_engine, InterpolationPromptEngine)
        assert target.mock_config.tool_response_generator is None
        assert target.target.mock_config.tool_response_generator is None
