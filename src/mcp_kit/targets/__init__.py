"""MCP target implementations.

This module provides various targets for different types of model interactions,
including direct MCP connections (hosted or spec), OpenAPI REST APIs (hosted or OAS spec), etc.
It also provides a mocked target that wraps any target to allow mocking
and a multiplex target that combines multiple targets into a single interface.
"""

from .interfaces import Target
from .mcp import McpTarget
from .mocked import MockedTarget
from .multiplex import MultiplexTarget
from .oas import OasTarget

__all__ = [
    "McpTarget",
    "MockedTarget",
    "MultiplexTarget",
    "OasTarget",
    "Target",
]
