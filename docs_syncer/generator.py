#!/usr/bin/env python3
"""
Simplified and refactored documentation generator for mcp-kit-python.

This refactored version is a simple orchestrator that delegates all work to specialized services.
"""

import sys
from collections.abc import Callable
from pathlib import Path

from api_generator import ApiGenerator
from category_manager import CategoryManager
from cleanup_service import CleanupService
from config import ConfigManager
from content_processor import ContentProcessor
from documentation_syncer import DocumentationSyncer
from examples_generator import ExamplesGenerator
from file_operations import FileOperations
from git_service import GitService
from reporting_service import ReportingService


class DocGenerator:
    """Simple orchestrator for documentation generation - delegates all work to services."""

    def __init__(self) -> None:
        """Initialize the documentation generator with all required services."""
        # Core configuration and utilities
        self.config = ConfigManager()
        self.file_ops = FileOperations(self._should_skip_file)
        self.content_processor = ContentProcessor()
        self.git_service = GitService(self.config.project_root)

        # Specialized services
        self.cleanup_service = CleanupService(self.config, self.file_ops)
        self.category_manager = CategoryManager(self.config, self._should_skip_file)
        self.documentation_syncer = DocumentationSyncer(self.config, self.file_ops, self.content_processor)
        self.examples_generator = ExamplesGenerator(self.config, self.content_processor, self.git_service)
        self.api_generator = ApiGenerator(self.config)
        self.reporting_service = ReportingService(self.config)

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during documentation generation."""
        return file_path.name == "sidebar.json"

    def run(self) -> bool:
        """Run the complete documentation generation process."""
        print("🚀 Starting comprehensive documentation generation...")

        # Step 1: Clean all directories
        self.cleanup_service.clean_all_directories()

        # Step 2: Copy category files
        self._execute_step("copy category files", self.category_manager.copy_category_files)

        # Step 3: Sync root files
        self._execute_step("sync root files", self.category_manager.sync_root_files)

        # Step 4: Sync user documentation
        self._execute_step("sync user documentation", self.documentation_syncer.sync_user_guide)

        # Step 5: Sync base examples documentation
        self._execute_step("sync examples base", self.documentation_syncer.sync_examples_base)

        # Step 6: Generate example docs from README files
        self._execute_step("generate example docs", self.examples_generator.generate_example_docs)

        # Step 7: Generate API reference (critical step)
        if not self._execute_step("generate API reference", self.api_generator.generate_api_reference, critical=True):
            return False

        # Step 8: Rename __init__.md files to index.md
        self._execute_step(
            "rename __init__.md files",
            lambda: self.content_processor.rename_init_files_to_index(self.config.reference_dir),
        )

        # Step 9: Sync manual reference documentation
        self._execute_step("sync reference docs", self.documentation_syncer.sync_reference_docs)

        # Step 10: Add frontmatter to reference files
        self._execute_step(
            "add frontmatter to reference files",
            lambda: self.content_processor.add_frontmatter_to_reference_files(self.config.reference_dir),
        )

        # Step 11: Remove empty headings
        self._execute_step(
            "remove empty headings", lambda: self.content_processor.remove_empty_headings(self.config.reference_dir)
        )

        # Step 12: Generate summary report
        self.reporting_service.generate_summary_report()

        print("\n✅ Documentation generation completed!")
        return True

    def _execute_step(self, step_name: str, step_function: Callable[[], bool], critical: bool = False) -> bool:
        """Execute a single step with consistent error handling."""
        try:
            result = step_function()
            if not result and critical:
                print(f"❌ Critical step '{step_name}' failed")
                return False
            elif not result:
                print(f"⚠️  Step '{step_name}' failed, continuing...")
            return result
        except Exception as e:
            print(f"❌ Error in step '{step_name}': {e}")
            if critical:
                return False
            print("⚠️  Continuing with next step...")
            return False


def main() -> None:
    """CLI entry point for documentation generation."""
    generator = DocGenerator()
    success = generator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
