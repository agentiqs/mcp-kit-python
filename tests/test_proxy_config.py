import tempfile
from pathlib import Path

import pytest
import yaml

from mcp_kit.generators import LlmResponseGenerator, RandomResponseGenerator
from mcp_kit import ProxyMCP
from mcp_kit.targets import McpTarget, MockedTarget, MultiplexTarget, OasTarget


class TestProxyMCPFromConfig:
    """Test cases for ProxyMCP.from_config factory method."""

    def test_create_mcp_target_from_config(self):
        """Test creating an MCP target from configuration."""
        config_data = {
            "target": {
                "type": "mcp",
                "name": "test-mcp",
                "url": "http://example.com/mcp",
                "headers": {"Authorization": "Bearer token123"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, McpTarget)
            assert base_target.name == "test-mcp"
            assert base_target.url == "http://example.com/mcp"
            assert base_target.headers == {"Authorization": "Bearer token123"}
        finally:
            Path(config_file).unlink()

    def test_create_oas_target_from_config(self):
        """Test creating an OAS target from configuration."""
        config_data = {
            "target": {
                "type": "oas",
                "name": "test-oas",
                "spec_url": "http://example.com/openapi.json",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, OasTarget)
            assert base_target.name == "test-oas"
            assert base_target._spec_url == "http://example.com/openapi.json"
        finally:
            Path(config_file).unlink()

    def test_create_mocked_target_from_config(self):
        """Test creating a mocked target from configuration."""
        config_data = {
            "target": {
                "type": "mocked",
                "base_target": {
                    "type": "mcp",
                    "name": "base-mcp",
                    "url": "http://example.com/mcp",
                },
                "tool_response_generator": {"type": "random"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, MockedTarget)
            assert isinstance(base_target.target, McpTarget)
            assert base_target.target.name == "base-mcp"
            assert isinstance(
                base_target.mock_config.tool_response_generator,
                RandomResponseGenerator,
            )
        finally:
            Path(config_file).unlink()

    def test_create_mocked_target_with_llm_generator(self):
        """Test creating a mocked target with LLM response generator."""
        config_data = {
            "target": {
                "type": "mocked",
                "base_target": {
                    "type": "oas",
                    "name": "base-oas",
                    "spec_url": "http://example.com/openapi.json",
                },
                "tool_response_generator": {"type": "llm", "model": "gpt-4"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, MockedTarget)
            assert isinstance(base_target.target, OasTarget)
            assert isinstance(
                base_target.mock_config.tool_response_generator,
                LlmResponseGenerator,
            )
        finally:
            Path(config_file).unlink()

    def test_create_multiplex_target_from_config(self):
        """Test creating a multiplex target from configuration."""
        config_data = {
            "target": {
                "type": "multiplex",
                "name": "multi-target",
                "targets": [
                    {"type": "mcp", "name": "mcp-1", "url": "http://example.com/mcp1"},
                    {
                        "type": "oas",
                        "name": "oas-1",
                        "spec_url": "http://example.com/openapi.json",
                    },
                ],
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, MultiplexTarget)
            assert base_target.name == "multi-target"
            assert len(base_target._targets_dict) == 2
            assert isinstance(base_target._targets_dict["mcp-1"], McpTarget)
            assert isinstance(base_target._targets_dict["oas-1"], OasTarget)
        finally:
            Path(config_file).unlink()

    def test_create_from_json_config(self):
        """Test creating ProxyMCP from JSON configuration file."""
        config_data = {
            "target": {
                "type": "mcp",
                "name": "test-mcp-json",
                "url": "http://example.com/mcp",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, McpTarget)
            assert base_target.name == "test-mcp-json"
        finally:
            Path(config_file).unlink()

    def test_create_from_pathlib_path(self):
        """Test creating ProxyMCP using pathlib.Path."""
        config_data = {
            "target": {
                "type": "mcp",
                "name": "test-mcp-path",
                "url": "http://example.com/mcp",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = Path(f.name)

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, McpTarget)
            assert base_target.name == "test-mcp-path"
        finally:
            config_file.unlink()

    def test_invalid_target_type_raises_error(self):
        """Test that invalid target type raises ValueError."""
        config_data = {"target": {"type": "invalid_type", "name": "test"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            with pytest.raises(ValueError, match="Unknown target type 'invalid_type'"):
                ProxyMCP.from_config(config_file)
        finally:
            Path(config_file).unlink()

    def test_invalid_response_generator_type_raises_error(self):
        """Test that invalid response generator type raises ValueError."""
        config_data = {
            "target": {
                "type": "mocked",
                "base_target": {
                    "type": "mcp",
                    "name": "base-mcp",
                    "url": "http://example.com/mcp",
                },
                "tool_response_generator": {"type": "invalid_generator"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            with pytest.raises(
                ValueError,
                match="Unknown generator type 'invalid_generator'",
            ):
                ProxyMCP.from_config(config_file)
        finally:
            Path(config_file).unlink()

    def test_mcp_target_with_minimal_config(self):
        """Test creating MCP target with minimal required configuration."""
        config_data = {"target": {"type": "mcp", "name": "minimal-mcp"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, McpTarget)
            assert base_target.name == "minimal-mcp"
            assert base_target.url is None
            assert base_target.headers is None
            assert base_target.tools is None
        finally:
            Path(config_file).unlink()

    def test_mocked_target_with_default_generator(self):
        """Test creating mocked target with no generator (delegates to base target)."""
        config_data = {
            "target": {
                "type": "mocked",
                "base_target": {
                    "type": "mcp",
                    "name": "base-mcp",
                    "url": "http://example.com/mcp",
                },
                # No tool_response_generator specified - should delegate to base target
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            proxy = ProxyMCP.from_config(config_file)
            base_target = proxy.target.target

            assert isinstance(base_target, MockedTarget)
            assert base_target.mock_config.tool_response_generator is None
        finally:
            Path(config_file).unlink()
