"""Factory for creating instances from configuration using reflection.
This module provides a central registry to avoid circular imports and supports
both Target and ResponseGenerator creation.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any, cast

from mcp import Tool
from mcp.types import ToolAnnotations
from omegaconf import DictConfig, ListConfig, OmegaConf

from mcp_kit.generators import ResponseGenerator
from mcp_kit.mixins import ConfigurableMixin
from mcp_kit.targets import Target


def create_object_from_config(
    config: DictConfig,
    get_class_name: Callable[[str], str],
    get_module_name: Callable[[str], str],
    object_type_name: str = "object",
) -> Any:
    """Generic factory function to create any object instance from configuration using reflection.

    :param config: Configuration from OmegaConf with a 'type' field
    :param get_class_name: Function that converts type string to class name
    :param get_module_name: Function that converts type string to module name
    :param object_type_name: Name of object type for error messages (e.g., "target", "generator")
    :return: Object instance
    :raises ValueError: If type is unknown or cannot be instantiated
    """
    object_type = config.type

    if not object_type:
        raise ValueError(
            f"Configuration must specify a 'type' field for {object_type_name}",
        )

    # Get class and module names using provided functions
    class_name = get_class_name(object_type)
    module_name = get_module_name(object_type)

    try:
        # Import the module
        module = importlib.import_module(module_name)

        # Get the class from the module
        object_class: ConfigurableMixin = getattr(module, class_name)

        # Create instance from config
        return object_class.from_config(config)

    except ModuleNotFoundError as e:
        raise ValueError(
            f"Unknown {object_type_name} type '{object_type}'. No module found for this {object_type_name} type.",
        ) from e
    except AttributeError as e:
        raise ValueError(
            f"Unknown {object_type_name} type '{object_type}'. Class '{class_name}' not found in module.",
        ) from e
    except Exception as e:
        raise ValueError(
            f"Failed to create {object_type_name} of type '{object_type}': {e!s}",
        ) from e


def create_target_from_config(config: DictConfig) -> Target:
    """Factory function to create any Target instance from configuration using reflection.

    :param config: Target configuration from OmegaConf
    :return: Target instance
    :raises ValueError: If target type is unknown or cannot be instantiated
    """
    return cast(
        Target,
        create_object_from_config(
            config,
            get_class_name=lambda target_type: target_type.capitalize() + "Target",
            get_module_name=lambda target_type: f"mcp_kit.targets.{target_type}",
            object_type_name="target",
        ),
    )


def create_response_generator_from_config(config: DictConfig) -> ResponseGenerator:
    """Factory function to create any ResponseGenerator instance from configuration using reflection.

    :param config: ResponseGenerator configuration from OmegaConf
    :return: ResponseGenerator instance
    :raises ValueError: If generator type is unknown or cannot be instantiated
    """
    return cast(
        ResponseGenerator,
        create_object_from_config(
            config,
            get_class_name=lambda generator_type: generator_type.capitalize() + "ResponseGenerator",
            get_module_name=lambda generator_type: f"mcp_kit.generators.{generator_type}",
            object_type_name="generator",
        ),
    )


def create_tools_from_config(config: DictConfig) -> list[Tool] | None:
    """Factory function to create any Tool instance from configuration using reflection.

    :param config: Tool configuration from OmegaConf
    :return: List of Tool instances or None if no tools are defined
    """
    tools_config: ListConfig | None = config.get("tools")
    if tools_config is None:
        return None

    tools = []
    for tool_config in tools_config:
        # Handle tool annotations if present
        annotations = None
        annotations_config: DictConfig | None = tool_config.get("annotations")
        if annotations_config is not None:
            annotations = ToolAnnotations(
                title=annotations_config.get("title"),
                readOnlyHint=annotations_config.get("readOnlyHint"),
                destructiveHint=annotations_config.get("destructiveHint"),
                idempotentHint=annotations_config.get("idempotentHint"),
                openWorldHint=annotations_config.get("openWorldHint"),
            )

        input_schema = tool_config.get("inputSchema", OmegaConf.create({}))

        tool = Tool(
            name=tool_config.name,
            description=tool_config.description,
            inputSchema=OmegaConf.to_object(input_schema) if isinstance(input_schema, DictConfig) else input_schema,  # type: ignore[arg-type]
            annotations=annotations,
        )
        tools.append(tool)

    return tools
