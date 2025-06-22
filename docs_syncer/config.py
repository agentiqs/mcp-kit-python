#!/usr/bin/env python3
"""
Configuration management for the documentation generator.

This module handles all path configuration and setup for the documentation generator.
"""

from pathlib import Path


class ConfigManager:
    """Manages paths and configuration for the documentation generator."""

    def __init__(self) -> None:
        self.syncer_dir = Path(__file__).parent
        self.project_root = self.syncer_dir.parent
        self.docs_dir = self.project_root / "docs"

        # Website directory is 2 levels up from docs_syncer/ in GitHub Actions
        workspace_root = self.syncer_dir.parent.parent
        self.website_dir = workspace_root / "website"

        # Destination directories
        self.user_guide_dir = self.website_dir / "mcp-kit-python" / "docs" / "user-guide"
        self.reference_dir = self.website_dir / "mcp-kit-python" / "docs" / "reference"
        self.examples_dir = self.website_dir / "mcp-kit-python" / "docs" / "examples"

        # Source directories
        self.source_user_guide = self.docs_dir / "user-guide"
        self.source_examples = self.docs_dir / "examples"
        self.source_src = self.project_root / "src"
