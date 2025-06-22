#!/usr/bin/env python3
"""
Documentation synchronization service module.

This module handles the synchronization of different documentation sections.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import ConfigManager
    from content_processor import ContentProcessor
    from file_operations import FileOperations


class DocumentationSyncer:
    """Handles synchronization of different documentation sections."""

    def __init__(
        self, config_manager: "ConfigManager", file_operations: "FileOperations", content_processor: "ContentProcessor"
    ) -> None:
        self.config = config_manager
        self.file_ops = file_operations
        self.content_processor = content_processor

    def sync_user_guide(self) -> bool:
        """Sync user guide documentation."""
        return self._sync_section(
            "user guide", self.config.source_user_guide, self.config.user_guide_dir, add_comments=True
        )

    def sync_reference_docs(self) -> bool:
        """Sync manual reference documentation."""
        return self._sync_section(
            "reference", self.config.docs_dir / "reference", self.config.reference_dir, add_comments=True
        )

    def sync_examples_base(self) -> bool:
        """Sync base examples documentation (index files, etc.)."""
        return self._sync_section("examples", self.config.source_examples, self.config.examples_dir, add_comments=True)

    def _sync_section(self, section_name: str, source_dir: Path, dest_dir: Path, add_comments: bool = True) -> bool:
        """Generic method to sync any documentation section."""
        print(f"📄 Synchronizing {section_name} documentation...")

        if not source_dir.exists():
            print(f"⚠️  No {section_name} documentation source directory found")
            return True

        try:
            # Copy markdown files
            md_count = self.file_ops.copy_files_recursive(source_dir, dest_dir, ["*.md", "*.mdx"], "markdown")

            # Add autogeneration comments if requested
            if add_comments:
                for md_file in dest_dir.rglob("*.md"):
                    self.content_processor.add_autogeneration_comment(md_file)

            # Copy image assets
            img_count = self.file_ops.copy_files_recursive(
                source_dir, dest_dir, self.file_ops.IMAGE_EXTENSIONS, "image"
            )

            # Copy JSON files (except sidebar.json)
            json_count = self.file_ops.copy_files_recursive(source_dir, dest_dir, ["*.json"], "JSON")

            print(
                f"✅ {section_name} documentation synchronized successfully! "
                f"({md_count} MD, {img_count} images, {json_count} JSON)"
            )
            return True

        except Exception as e:
            print(f"❌ Error synchronizing {section_name} documentation: {e}")
            return False
