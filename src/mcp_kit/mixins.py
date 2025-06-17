"""Mixins for configurable classes in the mcp_kit package."""

from abc import ABC, abstractmethod

from omegaconf import DictConfig
from typing_extensions import Self


class ConfigurableMixin(ABC):
    """Mixin that provides a from_config class method for creating instances from configuration.

    Classes that inherit from this mixin must implement from_config to handle their own
    instantiation from configuration data.
    """

    @classmethod
    @abstractmethod
    def from_config(cls, config: DictConfig) -> Self:
        """Factory method to create an instance from configuration.

        :param config: Configuration data
        :return: Instance of the class
        """
        ...
