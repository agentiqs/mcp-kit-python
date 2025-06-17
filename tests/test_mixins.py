"""Tests for mixins module."""

from abc import ABC

import pytest
from omegaconf import DictConfig, OmegaConf

from mcp_kit.mixins import ConfigurableMixin


class TestConfigurableMixin:
    """Test cases for ConfigurableMixin."""

    def test_configurable_mixin_is_abstract(self):
        """Test that ConfigurableMixin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ConfigurableMixin()

    def test_configurable_mixin_inheritance(self):
        """Test that classes can inherit from ConfigurableMixin."""

        class TestClass(ConfigurableMixin):
            @classmethod
            def from_config(cls, config: DictConfig):
                return cls()

        # Should be able to create instance via from_config
        config = OmegaConf.create({})
        instance = TestClass.from_config(config)
        assert isinstance(instance, TestClass)
        assert isinstance(instance, ConfigurableMixin)

    def test_abstract_from_config_method(self):
        """Test that from_config method must be implemented by subclasses."""

        class IncompleteClass(ConfigurableMixin):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteClass()

    def test_from_config_method_signature(self):
        """Test that from_config method has correct signature."""

        class TestClass(ConfigurableMixin):
            def __init__(self, value: str = "default"):
                self.value = value

            @classmethod
            def from_config(cls, config: DictConfig):
                value = config.get("value", "from_config")
                return cls(value)

        config = OmegaConf.create({"value": "test_value"})
        instance = TestClass.from_config(config)
        assert instance.value == "test_value"

    def test_multiple_inheritance_with_configurable_mixin(self):
        """Test ConfigurableMixin works with multiple inheritance."""

        class BaseClass:
            def __init__(self):
                self.base_attr = "base"

        class ConfigurableClass(BaseClass, ConfigurableMixin):
            def __init__(self, config_value: str = "default"):
                super().__init__()
                self.config_value = config_value

            @classmethod
            def from_config(cls, config: DictConfig):
                config_value = config.get("config_value", "default")
                return cls(config_value)

        config = OmegaConf.create({"config_value": "test"})
        instance = ConfigurableClass.from_config(config)
        assert instance.base_attr == "base"
        assert instance.config_value == "test"
        assert isinstance(instance, ConfigurableMixin)
        assert isinstance(instance, BaseClass)

    def test_configurable_mixin_with_abc(self):
        """Test ConfigurableMixin works with ABC."""

        class AbstractConfigurable(ConfigurableMixin, ABC):
            @classmethod
            def from_config(cls, config: DictConfig):
                return cls()

        class ConcreteClass(AbstractConfigurable):
            pass

        config = OmegaConf.create({})
        instance = ConcreteClass.from_config(config)
        assert isinstance(instance, ConcreteClass)
        assert isinstance(instance, ConfigurableMixin)
