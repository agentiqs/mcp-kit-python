#!/usr/bin/env python3
"""
Documentation reporting service module.

This module handles the reporting and summary of generated documentation files.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import ConfigManager


class ReportingService:
    """Handles reporting and summary of documentation generation results."""

    def __init__(self, config_manager: "ConfigManager") -> None:
        self.config = config_manager

    def generate_summary_report(self) -> bool:
        """Generate and display a summary report of created files."""
        created_files = self._collect_created_files()
        total_files = sum(len(files) for files in created_files.values())

        if total_files > 0:
            self._display_success_report(created_files, total_files)
        else:
            self._display_no_files_warning()

        return total_files > 0

    def _collect_created_files(self) -> dict[str, list[Path]]:
        """Collect all documentation files that were created."""
        files: dict[str, list[Path]] = {
            "user_guide": [],
            "examples": [],
            "api_reference": [],
            "categories": [],
        }

        # User guide files
        if self.config.user_guide_dir.exists():
            files["user_guide"] = list(self.config.user_guide_dir.rglob("*.md"))

        # Examples files
        if self.config.examples_dir.exists():
            files["examples"] = list(self.config.examples_dir.rglob("*.md"))

        # API reference files
        if self.config.reference_dir.exists():
            files["api_reference"] = list(self.config.reference_dir.rglob("*.md"))

        # Category files (both main and subdirectories)
        generated_docs_dir = self.config.website_dir / "mcp-kit-python" / "docs"
        if generated_docs_dir.exists():
            files["categories"] = list(generated_docs_dir.rglob("_category_.json"))

        return files

    def _display_success_report(self, created_files: dict[str, list[Path]], total_files: int) -> None:
        """Display a success report with file counts and listings."""
        print(f"\n📄 Successfully created {total_files} documentation files:")

        report_sections = [
            ("user_guide", "📖 User Guide", self.config.user_guide_dir, "user-guide"),
            ("examples", "📚 Examples", self.config.examples_dir, "examples"),
            ("api_reference", "🔧 API Reference", self.config.reference_dir, "reference"),
            ("categories", "📁 Category Files", self.config.website_dir, ""),
        ]

        for section_key, section_title, base_dir, prefix in report_sections:
            files = created_files[section_key]
            if files:
                print(f"\n{section_title} ({len(files)} files):")
                for file_path in sorted(files):
                    if section_key == "categories":
                        rel_path = file_path.relative_to(base_dir)
                        print(f"   - {rel_path}")
                    else:
                        rel_path = file_path.relative_to(base_dir)
                        print(f"   - {prefix}/{rel_path}")

    def _display_no_files_warning(self) -> None:
        """Display warning when no files were created."""
        print("⚠️  No documentation files were created")
