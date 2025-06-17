"""Tests for factory module."""

import pytest
from mcp import Tool
from omegaconf import OmegaConf

from mcp_kit.factory import (
    create_response_generator_from_config,
    create_target_from_config,
    create_tools_from_config,
)
from mcp_kit.generators import LlmResponseGenerator, RandomResponseGenerator
from mcp_kit.targets import McpTarget, MockedTarget, MultiplexTarget, OasTarget


class TestCreateTargetFromConfig:
    """Test cases for create_target_from_config function."""

    def test_create_mcp_target(self):
        """Test creating MCP target from config."""
        config = OmegaConf.create(
            {"type": "mcp", "name": "test-mcp", "url": "http://example.com/mcp"}
        )

        target = create_target_from_config(config)
        assert isinstance(target, McpTarget)
        assert target.name == "test-mcp"

    def test_create_oas_target(self):
        """Test creating OAS target from config."""
        config = OmegaConf.create(
            {
                "type": "oas",
                "name": "test-oas",
                "spec_url": "http://example.com/openapi.json",
            }
        )

        target = create_target_from_config(config)
        assert isinstance(target, OasTarget)
        assert target.name == "test-oas"

    def test_create_mocked_target(self):
        """Test creating mocked target from config."""
        config = OmegaConf.create(
            {
                "type": "mocked",
                "base_target": {
                    "type": "mcp",
                    "name": "base-mcp",
                    "url": "http://example.com/mcp",
                },
                "response_generator": {"type": "random"},
            }
        )

        target = create_target_from_config(config)
        assert isinstance(target, MockedTarget)
        assert isinstance(target.target, McpTarget)

    def test_create_multiplex_target(self):
        """Test creating multiplex target from config."""
        config = OmegaConf.create(
            {
                "type": "multiplex",
                "name": "multi-target",
                "targets": [
                    {"type": "mcp", "name": "mcp1", "url": "http://example1.com"},
                    {
                        "type": "oas",
                        "name": "oas1",
                        "spec_url": "http://example2.com/spec.json",
                    },
                ],
            }
        )

        target = create_target_from_config(config)
        assert isinstance(target, MultiplexTarget)
        assert target.name == "multi-target"

    def test_create_target_invalid_type(self):
        """Test create_target_from_config with invalid type."""
        config = OmegaConf.create({"type": "invalid_type", "name": "test"})

        with pytest.raises(ValueError, match="Unknown target type 'invalid_type'"):
            create_target_from_config(config)

    def test_create_target_missing_type(self):
        """Test create_target_from_config with missing type."""
        config = OmegaConf.create({"name": "test"})

        with pytest.raises(Exception):  # Could be KeyError or ConfigAttributeError
            create_target_from_config(config)

    def test_create_target_case_sensitivity(self):
        """Test that target type is case-sensitive."""
        config = OmegaConf.create({"type": "MCP", "name": "test-mcp"})  # Uppercase

        with pytest.raises(ValueError, match="Unknown target type 'MCP'"):
            create_target_from_config(config)

    def test_create_target_with_extra_config(self):
        """Test creating target with extra configuration parameters."""
        config = OmegaConf.create(
            {
                "type": "mcp",
                "name": "test-mcp",
                "url": "http://example.com/mcp",
                "headers": {"Authorization": "Bearer token"},
                "extra_param": "ignored",  # Should be ignored
            }
        )

        target = create_target_from_config(config)
        assert isinstance(target, McpTarget)
        assert target.name == "test-mcp"
        assert target.url == "http://example.com/mcp"
        assert target.headers == {"Authorization": "Bearer token"}


class TestCreateResponseGeneratorFromConfig:
    """Test cases for create_response_generator_from_config function."""

    def test_create_random_generator(self):
        """Test creating random generator from config."""
        config = OmegaConf.create({"type": "random"})

        generator = create_response_generator_from_config(config)
        assert isinstance(generator, RandomResponseGenerator)

    def test_create_llm_generator(self):
        """Test creating LLM generator from config."""
        config = OmegaConf.create({"type": "llm", "model": "gpt-4"})

        generator = create_response_generator_from_config(config)
        assert isinstance(generator, LlmResponseGenerator)
        assert generator.model == "gpt-4"

    def test_create_llm_generator_different_models(self):
        """Test creating LLM generator with different models."""
        models = ["gpt-3.5-turbo", "claude-3-sonnet", "gemini-pro"]

        for model in models:
            config = OmegaConf.create({"type": "llm", "model": model})

            generator = create_response_generator_from_config(config)
            assert isinstance(generator, LlmResponseGenerator)
            assert generator.model == model

    def test_create_generator_invalid_type(self):
        """Test create_response_generator_from_config with invalid type."""
        config = OmegaConf.create({"type": "invalid_generator"})

        with pytest.raises(
            ValueError, match="Unknown generator type 'invalid_generator'"
        ):
            create_response_generator_from_config(config)

    def test_create_generator_missing_type(self):
        """Test create_response_generator_from_config with missing type."""
        config = OmegaConf.create({})

        with pytest.raises(Exception):  # Could be KeyError or ConfigAttributeError
            create_response_generator_from_config(config)

    def test_create_llm_generator_missing_model(self):
        """Test creating LLM generator without model parameter."""
        config = OmegaConf.create({"type": "llm"})

        with pytest.raises(
            ValueError, match="Configuration must include a 'model' parameter"
        ):
            create_response_generator_from_config(config)

    def test_create_generator_case_sensitivity(self):
        """Test that generator type is case-sensitive."""
        config = OmegaConf.create({"type": "RANDOM"})

        with pytest.raises(ValueError, match="Unknown generator type 'RANDOM'"):
            create_response_generator_from_config(config)

    def test_create_random_generator_with_extra_params(self):
        """Test creating random generator ignores extra parameters."""
        config = OmegaConf.create({"type": "random", "extra_param": "ignored"})

        generator = create_response_generator_from_config(config)
        assert isinstance(generator, RandomResponseGenerator)


class TestCreateToolsFromConfig:
    """Test cases for create_tools_from_config function."""

    def test_create_tools_from_list(self):
        """Test creating tools from list configuration."""
        config = OmegaConf.create(
            {
                "tools": [
                    {"name": "tool1", "description": "First tool"},
                    {
                        "name": "tool2",
                        "description": "Second tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"param": {"type": "string"}},
                        },
                    },
                ]
            }
        )

        tools = create_tools_from_config(config)
        assert len(tools) == 2
        assert all(isinstance(tool, Tool) for tool in tools)
        assert tools[0].name == "tool1"
        assert tools[0].description == "First tool"
        assert tools[1].name == "tool2"
        assert tools[1].description == "Second tool"
        assert tools[1].inputSchema is not None

    def test_create_tools_empty_list(self):
        """Test creating tools from empty list."""
        config = OmegaConf.create({"tools": []})

        tools = create_tools_from_config(config)
        assert tools == []

    def test_create_tools_minimal_config(self):
        """Test creating tools with minimal configuration."""
        config = OmegaConf.create(
            {"tools": [{"name": "minimal_tool", "description": "Minimal tool"}]}
        )

        tools = create_tools_from_config(config)
        assert tools is not None
        assert len(tools) == 1
        assert tools[0].name == "minimal_tool"
        assert tools[0].description == "Minimal tool"
        assert tools[0].inputSchema == {}  # Default is empty dict, not None

    def test_create_tools_with_complex_schema(self):
        """Test creating tools with complex input schema."""
        config = OmegaConf.create(
            {
                "tools": [
                    {
                        "name": "complex_tool",
                        "description": "Tool with complex schema",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "string_param": {"type": "string"},
                                "number_param": {"type": "number"},
                                "array_param": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "nested_param": {
                                    "type": "object",
                                    "properties": {"nested_field": {"type": "boolean"}},
                                },
                            },
                            "required": ["string_param"],
                        },
                    }
                ]
            }
        )

        tools = create_tools_from_config(config)
        assert tools is not None
        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "complex_tool"
        assert tool.inputSchema is not None
        assert tool.inputSchema["type"] == "object"
        assert "string_param" in tool.inputSchema["properties"]
        assert "required" in tool.inputSchema

    def test_create_tools_missing_required_fields(self):
        """Test creating tools with missing required fields."""
        # Missing name
        config = [{"description": "Tool without name"}]

        with pytest.raises(
            Exception
        ):  # Could be various exceptions depending on Tool validation
            create_tools_from_config(config)

        # Missing description
        config = [{"name": "tool_without_description"}]

        with pytest.raises(
            Exception
        ):  # Could be various exceptions depending on Tool validation
            create_tools_from_config(config)

    def test_create_tools_with_invalid_schema(self):
        """Test creating tools with invalid input schema."""
        config = OmegaConf.create(
            {
                "tools": [
                    {
                        "name": "invalid_schema_tool",
                        "description": "Tool with invalid schema",
                        "inputSchema": "not_an_object",  # Should be object/dict
                    }
                ]
            }
        )

        # Should raise validation error due to invalid schema
        with pytest.raises(Exception):  # Pydantic ValidationError
            create_tools_from_config(config)

    def test_create_tools_preserves_order(self):
        """Test that tool creation preserves order."""
        config = OmegaConf.create(
            {
                "tools": [
                    {"name": f"tool_{i}", "description": f"Tool {i}"} for i in range(10)
                ]
            }
        )

        tools = create_tools_from_config(config)
        assert tools is not None
        assert len(tools) == 10
        for i, tool in enumerate(tools):
            assert tool.name == f"tool_{i}"
            assert tool.description == f"Tool {i}"

    def test_create_tools_with_duplicate_names(self):
        """Test creating tools with duplicate names."""
        config = OmegaConf.create(
            {
                "tools": [
                    {"name": "duplicate_tool", "description": "First instance"},
                    {"name": "duplicate_tool", "description": "Second instance"},
                ]
            }
        )

        # Should create both tools (no deduplication at this level)
        tools = create_tools_from_config(config)
        assert tools is not None
        assert len(tools) == 2
        assert tools[0].name == "duplicate_tool"
        assert tools[1].name == "duplicate_tool"
        assert tools[0].description != tools[1].description


class TestFactoryIntegration:
    """Integration tests for factory functions."""

    def test_nested_target_creation(self):
        """Test creating nested targets through factory."""
        config = OmegaConf.create(
            {
                "type": "mocked",
                "base_target": {
                    "type": "multiplex",
                    "name": "multi-base",
                    "targets": [
                        {"type": "mcp", "name": "mcp1", "url": "http://example1.com"},
                        {
                            "type": "oas",
                            "name": "oas1",
                            "spec_url": "http://example2.com/spec.json",
                        },
                    ],
                },
                "response_generator": {"type": "llm", "model": "gpt-4"},
            }
        )

        target = create_target_from_config(config)
        assert isinstance(target, MockedTarget)
        assert isinstance(target.target, MultiplexTarget)
        assert isinstance(target.mock_config.response_generator, LlmResponseGenerator)

    def test_factory_function_consistency(self):
        """Test that factory functions produce consistent results."""
        # Create the same target multiple times
        config = OmegaConf.create(
            {"type": "mcp", "name": "consistency-test", "url": "http://example.com/mcp"}
        )

        target1 = create_target_from_config(config)
        target2 = create_target_from_config(config)

        # Should be different instances but same type and properties
        assert target1 is not target2
        assert type(target1) == type(target2)
        assert target1.name == target2.name
        assert target1.url == target2.url

    def test_factory_error_propagation(self):
        """Test that factory functions properly propagate errors."""
        # Test with config that would cause target creation to fail
        invalid_config = OmegaConf.create(
            {
                "type": "mocked",
                "base_target": {"type": "invalid_type", "name": "invalid"},
            }
        )

        with pytest.raises(ValueError, match="Unknown target type 'invalid_type'"):
            create_target_from_config(invalid_config)

    def test_all_target_types_supported(self):
        """Test that all known target types are supported by factory."""
        target_configs = [
            {"type": "mcp", "name": "test-mcp"},
            {
                "type": "oas",
                "name": "test-oas",
                "spec_url": "http://example.com/spec.json",
            },
            {
                "type": "mocked",
                "base_target": {"type": "mcp", "name": "base-mcp"},
                "response_generator": {"type": "random"},
            },
            {
                "type": "multiplex",
                "name": "test-multiplex",
                "targets": [{"type": "mcp", "name": "sub-mcp"}],
            },
        ]

        for config_data in target_configs:
            config = OmegaConf.create(config_data)
            target = create_target_from_config(config)
            assert target is not None
            assert hasattr(target, "name")

    def test_all_generator_types_supported(self):
        """Test that all known generator types are supported by factory."""
        generator_configs = [{"type": "random"}, {"type": "llm", "model": "gpt-4"}]

        for config_data in generator_configs:
            config = OmegaConf.create(config_data)
            generator = create_response_generator_from_config(config)
            assert generator is not None
            assert hasattr(generator, "generate")
