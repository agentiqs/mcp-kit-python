#!/usr/bin/env python3
"""
API reference generation module for the documentation generator.

This module handles the generation of API reference documentation using pydoc-markdown.
"""

import os
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import ConfigManager


class ApiGenerator:
    """Handles API reference documentation generation using pydoc-markdown."""

    def __init__(self, config_manager: "ConfigManager") -> None:
        self.config = config_manager

    def generate_api_reference(self) -> bool:
        """Generate API reference documentation using pydoc-markdown with DocusaurusRenderer."""
        print("📚 Generating API reference documentation...")

        # Change to docs_syncer directory for pydoc-markdown
        original_dir = os.getcwd()
        try:
            os.chdir(self.config.syncer_dir)

            # Run pydoc-markdown with verbose output
            _ = subprocess.run(
                ["uv", "run", "pydoc-markdown", "--verbose", "pydoc-markdown.yml"],
                check=True,
                capture_output=True,
                text=True,
            )
            print("✅ API reference generated successfully!")

            # Remove any sidebar.json files that pydoc-markdown might have created
            print("🗑️  Cleaning up any sidebar.json files created by pydoc-markdown...")
            for sidebar_file in self.config.website_dir.rglob("sidebar.json"):
                try:
                    sidebar_file.unlink()
                    rel_path = sidebar_file.relative_to(self.config.website_dir)
                    print(f"   🗑️  Removed pydoc-markdown sidebar.json: {rel_path}")
                except Exception as e:
                    print(f"   ⚠️  Could not remove {sidebar_file}: {e}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating API reference: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
        finally:
            os.chdir(original_dir)
