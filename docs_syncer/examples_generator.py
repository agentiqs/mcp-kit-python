#!/usr/bin/env python3
"""
Examples documentation generator module.

This module handles the generation of documentation for example projects.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import ConfigManager
    from content_processor import ContentProcessor
    from git_service import GitService

# Configuration for GitHub repository links
GITHUB_ORG = "agentiqs"
GITHUB_REPO = "mcp-kit-python"


class ExamplesGenerator:
    """Handles examples documentation generation with GitHub links."""

    def __init__(
        self, config_manager: "ConfigManager", content_processor: "ContentProcessor", git_service: "GitService"
    ) -> None:
        self.config = config_manager
        self.content_processor = content_processor
        self.git_service = git_service

    def generate_example_docs(self) -> bool:
        """Generate documentation for each example subdirectory."""
        print("📚 Generating example documentation from README files...")

        examples_root = self.config.project_root / "examples"
        if not examples_root.exists():
            print("⚠️  No examples directory found")
            return True

        git_hash = self.git_service.get_commit_hash()
        sidebar_position = 2  # Start after index.md
        generated_count = 0

        for subdir in sorted(examples_root.iterdir()):
            if not self._is_valid_example_dir(subdir):
                continue

            readme_file = subdir / "README.md"
            if not self._has_valid_readme(readme_file):
                print(f"   ⚠️  Skipping {subdir.name} - no README.md or empty file")
                continue

            if self._process_example_readme(subdir, readme_file, git_hash, sidebar_position):
                generated_count += 1
                sidebar_position += 1

        print(f"✅ Generated {generated_count} example documentation files!")
        return True

    def _is_valid_example_dir(self, subdir: Path) -> bool:
        """Check if a subdirectory is a valid example directory."""
        return subdir.is_dir() and not subdir.name.startswith(".") and not subdir.name.startswith("__")

    def _has_valid_readme(self, readme_file: Path) -> bool:
        """Check if README file exists and has content."""
        return readme_file.exists() and readme_file.stat().st_size > 0

    def _process_example_readme(self, subdir: Path, readme_file: Path, git_hash: str, sidebar_position: int) -> bool:
        """Process a single example README file."""
        try:
            # Read and clean content
            with open(readme_file, encoding="utf-8") as f:
                readme_content = f.read()

            clean_content = self._remove_existing_frontmatter(readme_content)

            # Add GitHub link at the end of the first section
            github_link = self._create_github_link(subdir.name, git_hash)
            clean_content = self.content_processor.insert_github_link_at_section_end(clean_content, github_link)

            # Create final content with frontmatter
            final_content = self._create_final_content(clean_content, sidebar_position)

            # Write the file
            dest_file = self.config.examples_dir / f"{subdir.name}.md"
            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(final_content)

            print(f"   📄 Generated examples/{dest_file.name} from {subdir.name}/README.md")
            return True

        except Exception as e:
            print(f"   ❌ Error processing {subdir.name}: {e}")
            return False

    def _remove_existing_frontmatter(self, content: str) -> str:
        """Remove any existing frontmatter from content."""
        frontmatter_pattern = r"^---\n.*?\n---\n\n?"
        return re.sub(frontmatter_pattern, "", content, flags=re.DOTALL)

    def _create_github_link(self, example_name: str, git_hash: str) -> str:
        """Create GitHub source code link for an example."""
        return f"**📂 [View Source Code](https://github.com/{GITHUB_ORG}/{GITHUB_REPO}/tree/{git_hash}/examples/{example_name})**"

    def _create_final_content(self, clean_content: str, sidebar_position: int) -> str:
        """Create final content with frontmatter."""
        frontmatter = f"""---
sidebar_position: {sidebar_position}
# This file was auto-generated and should not be edited manually
---

"""
        return frontmatter + clean_content
