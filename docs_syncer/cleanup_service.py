#!/usr/bin/env python3
"""
Documentation cleanup service module.

This module handles cleanup operations for documentation directories.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import ConfigManager
    from file_operations import FileOperations


class CleanupService:
    """Handles cleanup operations for documentation generation."""

    def __init__(self, config_manager: "ConfigManager", file_operations: "FileOperations") -> None:
        self.config = config_manager
        self.file_ops = file_operations

    def clean_all_directories(self) -> None:
        """Clean all documentation directories."""
        print("🧹 Cleaning existing documentation...")

        self._ensure_website_directory_exists()
        self._remove_sidebar_files()
        self._clean_documentation_directories()

    def _ensure_website_directory_exists(self) -> None:
        """Ensure the website directory exists."""
        if not self.config.website_dir.exists():
            print("⚠️  Website directory not found. Creating temporary directory for testing...")
            self.config.website_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Created temporary website structure")

    def _remove_sidebar_files(self) -> None:
        """Remove any existing sidebar.json files from the website directory."""
        print("🗑️  Removing any existing sidebar.json files from website directory...")

        if not self.config.website_dir.exists():
            return

        removed_count = 0
        for sidebar_file in self.config.website_dir.rglob("sidebar.json"):
            try:
                sidebar_file.unlink()
                rel_path = sidebar_file.relative_to(self.config.website_dir)
                print(f"   🗑️  Removed existing sidebar.json: {rel_path}")
                removed_count += 1
            except Exception as e:
                print(f"   ⚠️  Could not remove {sidebar_file}: {e}")

        if removed_count > 0:
            print(f"✅ Removed {removed_count} existing sidebar.json files")
        else:
            print("✅ No existing sidebar.json files found")

    def _clean_documentation_directories(self) -> None:
        """Clean all documentation directories."""
        directories = [
            (self.config.reference_dir, "API reference directory"),
            (self.config.user_guide_dir, "user guide directory"),
            (self.config.examples_dir, "examples directory"),
        ]

        for directory, description in directories:
            self.file_ops.clean_directory(directory, description)
