#!/usr/bin/env python3
"""
Content processing module for the documentation generator.

This module handles content processing operations like frontmatter and link insertion.
"""

import re
from pathlib import Path


class ContentProcessor:
    """Handles content processing operations like frontmatter and link insertion."""

    @staticmethod
    def add_autogeneration_comment(file_path: Path) -> None:
        """Add autogeneration warning comment inside frontmatter as YAML comment."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check if comment already exists
            if "This file was auto-generated" in content:
                return

            # Parse frontmatter
            frontmatter_pattern = r"^---\n(.*?)\n---\n(.*)"
            match = re.match(frontmatter_pattern, content, re.DOTALL)

            yaml_comment = "# This file was auto-generated and should not be edited manually"

            if match:
                # Extract existing frontmatter and body
                existing_fm = match.group(1)
                body_content = match.group(2)

                # Add comment to frontmatter
                new_frontmatter = f"---\n{existing_fm}\n{yaml_comment}\n---\n"
                new_content = new_frontmatter + body_content
            else:
                # Create new frontmatter with just the comment
                new_frontmatter = f"---\n{yaml_comment}\n---\n\n"
                new_content = new_frontmatter + content

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

        except Exception as e:
            print(f"⚠️  Could not add comment to {file_path}: {e}")

    @staticmethod
    def insert_github_link_at_section_end(content: str, github_link: str) -> str:
        """Insert GitHub link at the end of the first section."""
        lines = content.split("\n")
        if not lines or not lines[0].startswith("#"):
            return content

        # Find the end of the first section (before next heading or end of content)
        insert_position = len(lines)  # Default to end of content

        # Look for the next heading (section break)
        for i in range(1, len(lines)):
            if lines[i].startswith("#"):
                insert_position = i
                break

        # Skip any trailing empty lines in the first section
        while insert_position > 1 and lines[insert_position - 1].strip() == "":
            insert_position -= 1

        # Insert the GitHub link with proper spacing
        lines.insert(insert_position, "")  # Add empty line before
        lines.insert(insert_position + 1, github_link.rstrip())  # Add link
        return "\n".join(lines)

    @staticmethod
    def add_frontmatter_to_reference_files(reference_dir: Path) -> bool:
        """Add frontmatter to reference markdown files with simple sequential positioning."""
        print("📝 Adding frontmatter to reference files...")

        try:
            # Process only auto-generated markdown files in the mcp_kit subdirectory
            mcp_kit_dir = reference_dir / "mcp_kit"
            if not mcp_kit_dir.exists():
                print("⚠️  No mcp_kit directory found in reference")
                return True

            for md_file in mcp_kit_dir.rglob("*.md"):
                with open(md_file, encoding="utf-8") as f:
                    content = f.read()

                # Extract existing frontmatter if any
                frontmatter_pattern = r"^---\n(.*?)\n---\n"
                match = re.match(frontmatter_pattern, content, re.DOTALL)

                if match:
                    # Update existing frontmatter
                    existing_fm = match.group(1)
                    # Remove content after frontmatter
                    remaining_content = content[match.end() :]
                else:
                    existing_fm = ""
                    remaining_content = content

                # Build new frontmatter
                fm_lines = []

                # Parse existing frontmatter
                existing_data = {}
                if existing_fm:
                    for line in existing_fm.split("\n"):
                        if ":" in line and line.strip():
                            key, value = line.split(":", 1)
                            existing_data[key.strip()] = value.strip()

                # Keep existing keys (sidebar_label and title from pydoc-markdown)
                if "sidebar_label" in existing_data:
                    fm_lines.append(f"sidebar_label: {existing_data['sidebar_label']}")
                if "title" in existing_data:
                    fm_lines.append(f"title: {existing_data['title']}")

                # Add autogeneration comment as YAML comment
                fm_lines.append("# This file was auto-generated and should not be edited manually")

                # Build new content
                if fm_lines:
                    new_frontmatter = "---\n" + "\n".join(fm_lines) + "\n---\n"
                else:
                    new_frontmatter = ""

                new_content = new_frontmatter + remaining_content

                # Write updated file
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(new_content)

            print("✅ Frontmatter added to reference files!")
            return True

        except Exception as e:
            print(f"❌ Error adding frontmatter to reference files: {e}")
            return False

    @staticmethod
    def remove_empty_headings(reference_dir: Path) -> bool:
        """Remove empty headings (levels 1-4) that have no content before the next heading or EOF."""
        print("🧹 Removing empty headings from reference files...")

        try:
            # Process only auto-generated markdown files in the mcp_kit subdirectory
            mcp_kit_dir = reference_dir / "mcp_kit"
            if not mcp_kit_dir.exists():
                print("⚠️  No mcp_kit directory found in reference")
                return True

            for md_file in mcp_kit_dir.rglob("*.md"):
                with open(md_file, encoding="utf-8") as f:
                    content = f.read()

                # Use multi-pass approach to handle nested empty headings
                original_content = content
                max_passes = 5  # Prevent infinite loops
                pass_count = 0

                while pass_count < max_passes:
                    pass_count += 1
                    lines = content.split("\n")
                    filtered_lines = []
                    i = 0
                    removed_headings_this_pass = []

                    while i < len(lines):
                        line = lines[i]

                        # Check if this is a heading (level 1-4)
                        heading_level = ContentProcessor._get_heading_level(line)
                        if heading_level > 0:
                            # Look ahead to see if this heading is empty
                            j = i + 1
                            has_content = False

                            # Check all lines until we find another heading or EOF
                            while j < len(lines):
                                next_line = lines[j]

                                # Get the level of the next line if it's a heading
                                next_heading_level = ContentProcessor._get_heading_level(next_line)

                                # If we hit another heading of same or higher level, stop looking
                                if next_heading_level > 0 and next_heading_level <= heading_level:
                                    break

                                # If we find any non-empty content, this heading is not empty
                                if next_line.strip() != "":
                                    has_content = True
                                    break

                                j += 1

                            if not has_content:
                                # This heading is empty - skip it
                                removed_headings_this_pass.append(line.strip())
                                i += 1
                                # Skip any empty lines that immediately follow the removed heading
                                while i < len(lines) and lines[i].strip() == "":
                                    i += 1
                                continue
                            else:
                                # Keep the heading as it has content
                                filtered_lines.append(line)
                        else:
                            # Keep all other lines
                            filtered_lines.append(line)

                        i += 1

                    # Check if any changes were made in this pass
                    new_content = "\n".join(filtered_lines)
                    if new_content == content:
                        # No changes in this pass, we're done
                        break
                    else:
                        content = new_content
                        # Log removed headings for this pass
                        for heading in removed_headings_this_pass:
                            print(f"   🗑️  Removed empty heading: {heading} from {md_file.name}")

                # Write the final content back to the file if changes were made
                if content != original_content:
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.write(content)

            print("✅ Empty headings removed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error removing empty headings: {e}")
            return False

    @staticmethod
    def _get_heading_level(line: str) -> int:
        """Get the heading level of a markdown line (1-4), or 0 if not a heading.

        :param line: The line to check
        :return: Heading level (1-4) or 0 if not a heading
        """
        line = line.strip()
        if line.startswith("#### "):
            return 4
        elif line.startswith("### "):
            return 3
        elif line.startswith("## "):
            return 2
        elif line.startswith("# "):
            return 1
        else:
            return 0

    @staticmethod
    def rename_init_files_to_index(reference_dir: Path) -> bool:
        """Rename __init__.md files to index.md in the reference section for better navigation."""
        print("📝 Renaming __init__.md files to index.md in reference section...")

        try:
            # Find all __init__.md files in the reference directory
            for init_file in reference_dir.rglob("__init__.md"):
                # Calculate the new index.md path
                index_file = init_file.parent / "index.md"

                # Rename the file
                init_file.rename(index_file)

                # Calculate relative path for logging
                rel_path = index_file.relative_to(reference_dir)
                print(f"   📄 Renamed __init__.md → {rel_path}")

            print("✅ Reference __init__.md files renamed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error renaming __init__.md files: {e}")
            return False
