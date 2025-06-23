"""Prompt engine implementations for creating mock MCP prompt responses.

This module provides different strategies for generating synthetic responses
to MCP prompt calls, similar to how response generators work for tool calls.
"""

from .interfaces import PromptEngine
from .interpolation import InterpolationPromptEngine

__all__ = [
    "PromptEngine",
    "InterpolationPromptEngine",
]
