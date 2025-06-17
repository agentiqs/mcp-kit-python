"""Test for the new response generator factory functionality."""

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import ConfigAttributeError

from mcp_kit.factory import create_response_generator_from_config
from mcp_kit.generators import LlmResponseGenerator, RandomResponseGenerator


class TestResponseGeneratorFactory:
    """Tests for the create_response_generator_from_config factory function."""

    def test_create_random_response_generator_from_config(self):
        """Test creating RandomResponseGenerator from configuration."""
        config_data = {"type": "random"}
        config = OmegaConf.create(config_data)
        generator = create_response_generator_from_config(config)

        assert isinstance(generator, RandomResponseGenerator)

    def test_create_llm_response_generator_from_config(self):
        """Test creating LLMResponseGenerator from configuration."""
        config_data = {"type": "llm", "model": "gpt-4"}
        config = OmegaConf.create(config_data)
        generator = create_response_generator_from_config(config)

        assert isinstance(generator, LlmResponseGenerator)

    def test_create_llm_response_generator_default_model(self):
        """Test creating LLMResponseGenerator with specified model."""
        config_data = {"type": "llm", "model": "gpt-3.5-turbo"}
        config = OmegaConf.create(config_data)
        generator = create_response_generator_from_config(config)

        assert isinstance(generator, LlmResponseGenerator)
        assert generator.model == "gpt-3.5-turbo"

    def test_create_llm_response_generator_missing_model(self):
        """Test creating LLMResponseGenerator without model parameter raises ValueError."""
        config_data = {"type": "llm"}
        config = OmegaConf.create(config_data)

        with pytest.raises(
            ValueError, match="Configuration must include a 'model' parameter"
        ):
            create_response_generator_from_config(config)

    def test_create_response_generator_invalid_type(self):
        """Test that invalid generator type raises ValueError."""
        config_data = {"type": "invalid_type"}
        config = OmegaConf.create(config_data)

        with pytest.raises(ValueError, match="Unknown generator type 'invalid_type'"):
            create_response_generator_from_config(config)

    def test_create_response_generator_missing_type(self):
        """Test that missing type field raises ValueError."""
        config_data = {}
        config = OmegaConf.create(config_data)

        with pytest.raises(ConfigAttributeError, match="Missing key type"):
            create_response_generator_from_config(config)
