#!/usr/bin/env python3
"""
Category files management module for the documentation generator.

This module handles copying and managing _category_.json files for Docusaurus.
"""

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import ConfigManager


class CategoryManager:
    """Handles category files management for Docusaurus."""

    def __init__(self, config_manager: "ConfigManager", should_skip_file_func: Callable[[Path], bool]) -> None:
        self.config = config_manager
        self.should_skip_file = should_skip_file_func

    def copy_category_files(self) -> bool:
        """Copy _category_.json files to their proper locations."""
        print("📁 Copying _category_.json files...")

        try:
            # Main mcp-kit-python/docs _category_.json
            main_category = self.config.docs_dir / "_category_.json"
            if main_category.exists():
                dest_dir = self.config.website_dir / "mcp-kit-python" / "docs"
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(main_category, dest_dir / "_category_.json")
                print("   📄 Copied main _category_.json")

            # Recursively copy all _category_.json files from docs subdirectories
            for category_file in self.config.docs_dir.rglob("_category_.json"):
                # Skip the main _category_.json (already handled above)
                if category_file == main_category:
                    continue

                # Skip any sidebar.json files to prevent them from being moved to ../website
                if self.should_skip_file(category_file):
                    print(f"   ⚠️  Skipping file: {category_file.name}")
                    continue

                # Calculate relative path from docs directory
                relative_path = category_file.relative_to(self.config.docs_dir)

                # Determine destination based on the subdirectory
                if relative_path.parts[0] == "user-guide":
                    dest_file = self.config.user_guide_dir / Path(*relative_path.parts[1:])
                elif relative_path.parts[0] == "examples":
                    dest_file = self.config.examples_dir / Path(*relative_path.parts[1:])
                elif relative_path.parts[0] == "reference":
                    dest_file = self.config.reference_dir / Path(*relative_path.parts[1:])
                else:
                    # Skip unknown directories
                    continue

                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy the category file
                shutil.copy2(category_file, dest_file)
                print(f"   📄 Copied {relative_path}")

            print("✅ Category files copied successfully!")
            return True

        except Exception as e:
            print(f"❌ Error copying category files: {e}")
            return False

    def sync_root_files(self) -> bool:
        """Sync top-level files (images, index.md, etc.) from docs root to mcp-kit-python/docs/."""
        print("📄 Synchronizing root documentation files...")

        try:
            # Get the destination directory (mcp-kit-python/docs/)
            dest_dir = self.config.website_dir / "mcp-kit-python" / "docs"
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Copy all files from docs root (excluding subdirectories and _category_.json which is handled separately)
            for item in self.config.docs_dir.iterdir():
                # Skip directories and _category_.json files (handled elsewhere)
                if item.is_dir() or item.name.startswith("_category"):
                    continue

                # Skip files using centralized check
                if self.should_skip_file(item):
                    continue

                # Copy the file
                dest_file = dest_dir / item.name
                shutil.copy2(item, dest_file)
                print(f"   📄 Copied {item.name}")

            print("✅ Root documentation files synchronized successfully!")
            return True

        except Exception as e:
            print(f"❌ Error synchronizing root documentation files: {e}")
            return False
