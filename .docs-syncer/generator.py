#!/usr/bin/env python3
"""
Documentation generator module for mcp-kit Python SDK.

This module generates API reference documentation and synchronizes user documentation
using pydoc-markdown with DocusaurusRenderer and Docusaurus autosidebar with _category_.json files.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Configuration for GitHub repository links
GITHUB_ORG = "mynimbus"
GITHUB_REPO = "mcp-kit-python"


class DocGenerator:
    """Generates comprehensive documentation using Docusaurus autosidebar with _category_.json files.

    Note: This generator explicitly prevents sidebar.json files from being moved to the ../website
    directory to maintain proper documentation structure and avoid conflicts.
    """

    def __init__(self):
        """Initialize the documentation generator for CI environment."""
        # In GitHub Actions:
        # Working directory: /home/runner/work/mcp-kit-python/mcp-kit-python/mcp-kit-python/.docs-syncer
        # Website directory:  /home/runner/work/mcp-kit-python/mcp-kit-python/website
        #
        # From .docs-syncer/, we need: .docs-syncer/ -> mcp-kit-python/ -> mcp-kit-python/ -> website/
        # That's ../../website (2 levels up)

        self.syncer_dir = Path(__file__).parent  # mcp-kit-python/.docs-syncer
        self.project_root = self.syncer_dir.parent  # mcp-kit-python/
        self.docs_dir = self.project_root / "docs"  # mcp-kit-python/docs

        # Website directory is 2 levels up from .docs-syncer/ in GitHub Actions
        # .docs-syncer/ -> mcp-kit-python/ -> mcp-kit-python/ -> website/
        workspace_root = self.syncer_dir.parent.parent  # Go up 2 levels
        self.website_dir = workspace_root / "website"

        # For user guide, reference, and examples docs
        self.user_guide_dir = self.website_dir / "docs" / "python-sdk" / "user-guide"
        self.reference_dir = self.website_dir / "docs" / "python-sdk" / "reference"
        self.examples_dir = self.website_dir / "docs" / "python-sdk" / "examples"

        # Source directories
        self.source_user_guide = self.docs_dir / "user-guide"
        self.source_examples = self.docs_dir / "examples"
        self.source_src = self.project_root / "src"

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during documentation generation.

        :param file_path: Path to the file to check
        :return: True if the file should be skipped, False otherwise
        """
        # Only skip sidebar.json files to prevent them from being moved to ../website
        if file_path.name == "sidebar.json":
            return True

        return False

    def _remove_existing_sidebar_files(self) -> None:
        """Remove any existing sidebar.json files from the website directory."""
        print("🗑️  Removing any existing sidebar.json files from website directory...")

        if not self.website_dir.exists():
            return

        # Search for all sidebar.json files in the website directory
        for sidebar_file in self.website_dir.rglob("sidebar.json"):
            try:
                sidebar_file.unlink()
                rel_path = sidebar_file.relative_to(self.website_dir)
                print(f"   🗑️  Removed existing sidebar.json: {rel_path}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {sidebar_file}: {e}")

        print("✅ Existing sidebar.json files cleanup completed")

    def _get_git_commit_hash(self) -> str:
        """Get the current git commit hash for GitHub links."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to 'main' if git is not available or fails
            return "main"

    def clean_documentation_dirs(self) -> None:
        """Clean both reference and user guide directories."""
        print("🧹 Cleaning existing documentation...")

        if not self.website_dir.exists():
            print(
                "⚠️  Website directory not found. Creating temporary directory for testing..."
            )
            # Create a temporary directory structure for testing
            self.website_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Created temporary website structure")

        # Remove any existing sidebar.json files from the website directory
        self._remove_existing_sidebar_files()

        # Clean reference directory
        if self.reference_dir.exists():
            for item in self.reference_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print("✅ Cleaned API reference directory")
        else:
            self.reference_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Created API reference directory")

        # Clean user guide directory
        if self.user_guide_dir.exists():
            for item in self.user_guide_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print("✅ Cleaned user guide directory")
        else:
            self.user_guide_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Created user guide directory")

        # Clean examples directory
        if self.examples_dir.exists():
            for item in self.examples_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print("✅ Cleaned examples directory")
        else:
            self.examples_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Created examples directory")

    def copy_category_files(self) -> bool:
        """Copy _category_.json files to their proper locations."""
        print("📁 Copying _category_.json files...")

        try:
            # Main python-sdk _category_.json
            main_category = self.docs_dir / "_category_.json"
            if main_category.exists():
                dest_dir = self.website_dir / "docs" / "python-sdk"
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(main_category, dest_dir / "_category_.json")
                print("   📄 Copied main _category_.json")

            # Recursively copy all _category_.json files from docs subdirectories
            for category_file in self.docs_dir.rglob("_category_.json"):
                # Skip the main _category_.json (already handled above)
                if category_file == main_category:
                    continue

                # Skip any sidebar.json files to prevent them from being moved to ../website
                if self._should_skip_file(category_file):
                    print(f"   ⚠️  Skipping file: {category_file.name}")
                    continue

                # Calculate relative path from docs directory
                relative_path = category_file.relative_to(self.docs_dir)

                # Determine destination based on the subdirectory
                if relative_path.parts[0] == "user-guide":
                    dest_file = self.user_guide_dir / Path(*relative_path.parts[1:])
                elif relative_path.parts[0] == "examples":
                    dest_file = self.examples_dir / Path(*relative_path.parts[1:])
                elif relative_path.parts[0] == "reference":
                    dest_file = self.reference_dir / Path(*relative_path.parts[1:])
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

    def add_autogeneration_comment(self, file_path: Path) -> None:
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

            yaml_comment = (
                "# This file was auto-generated and should not be edited manually"
            )

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

    def sync_user_documentation(self) -> bool:
        """Sync user documentation from docs/user-guide to website with autogeneration comments."""
        print("📄 Synchronizing user documentation...")

        if not self.source_user_guide.exists():
            print("⚠️  No user documentation source directory found")
            return True  # Not an error, just no user docs

        try:
            # Copy all markdown files from user-guide
            for md_file in self.source_user_guide.rglob("*.md"):
                # Skip files using centralized check
                if self._should_skip_file(md_file):
                    continue

                # Preserve directory structure
                relative_path = md_file.relative_to(self.source_user_guide)
                dest_file = self.user_guide_dir / relative_path

                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(md_file, dest_file)

                # Add autogeneration comment
                self.add_autogeneration_comment(dest_file)

                print(f"   📄 Copied {relative_path}")

            # Copy image assets (PNG, SVG, JPG, JPEG, GIF, WebP)
            image_extensions = [
                "*.png",
                "*.svg",
                "*.jpg",
                "*.jpeg",
                "*.gif",
                "*.webp",
                "*.PNG",
                "*.SVG",
                "*.JPG",
                "*.JPEG",
                "*.GIF",
                "*.WEBP",
            ]
            for pattern in image_extensions:
                for image_file in self.source_user_guide.rglob(pattern):
                    # Skip files using centralized check
                    if self._should_skip_file(image_file):
                        continue

                    # Preserve directory structure
                    relative_path = image_file.relative_to(self.source_user_guide)
                    dest_file = self.user_guide_dir / relative_path

                    # Create destination directory if needed
                    dest_file.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(image_file, dest_file)
                    print(f"   🖼️  Copied {relative_path}")

            # Also copy any additional JSON files except sidebar.json
            for json_file in self.source_user_guide.rglob("*.json"):
                # Skip files using centralized check (includes sidebar.json)
                if self._should_skip_file(json_file):
                    print(f"   ⚠️  Skipping file: {json_file.name}")
                    continue

                # Preserve directory structure
                relative_path = json_file.relative_to(self.source_user_guide)
                dest_file = self.user_guide_dir / relative_path

                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(json_file, dest_file)
                print(f"   📄 Copied {relative_path}")

            print("✅ User documentation synchronized successfully!")
            return True

        except Exception as e:
            print(f"❌ Error synchronizing user documentation: {e}")
            return False

    def sync_reference_documentation(self) -> bool:
        """Sync manual reference documentation from docs/reference to website."""
        print("📄 Synchronizing manual reference documentation...")

        source_reference = self.docs_dir / "reference"
        if not source_reference.exists():
            print("⚠️  No manual reference documentation source directory found")
            return True  # Not an error, just no manual reference docs

        try:
            # Copy all markdown files from reference directory
            for md_file in source_reference.rglob("*.md"):
                # Skip files using centralized check
                if self._should_skip_file(md_file):
                    continue

                # Preserve directory structure
                relative_path = md_file.relative_to(source_reference)
                dest_file = self.reference_dir / relative_path

                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(md_file, dest_file)

                # Add autogeneration comment
                self.add_autogeneration_comment(dest_file)

                print(f"   📄 Copied reference/{relative_path}")

            # Copy image assets (PNG, SVG, JPG, JPEG, GIF, WebP)
            image_extensions = [
                "*.png",
                "*.svg",
                "*.jpg",
                "*.jpeg",
                "*.gif",
                "*.webp",
                "*.PNG",
                "*.SVG",
                "*.JPG",
                "*.JPEG",
                "*.GIF",
                "*.WEBP",
            ]
            for pattern in image_extensions:
                for image_file in source_reference.rglob(pattern):
                    # Skip files using centralized check
                    if self._should_skip_file(image_file):
                        continue

                    # Preserve directory structure
                    relative_path = image_file.relative_to(source_reference)
                    dest_file = self.reference_dir / relative_path

                    # Create destination directory if needed
                    dest_file.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(image_file, dest_file)
                    print(f"   🖼️  Copied reference/{relative_path}")

            # Also copy any additional JSON files except sidebar.json
            for json_file in source_reference.rglob("*.json"):
                # Skip files using centralized check (includes sidebar.json)
                if self._should_skip_file(json_file):
                    print(f"   ⚠️  Skipping file: {json_file.name}")
                    continue

                # Preserve directory structure
                relative_path = json_file.relative_to(source_reference)
                dest_file = self.reference_dir / relative_path

                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(json_file, dest_file)
                print(f"   📄 Copied reference/{relative_path}")

            print("✅ Manual reference documentation synchronized successfully!")
            return True

        except Exception as e:
            print(f"❌ Error synchronizing manual reference documentation: {e}")
            return False

    def sync_examples_documentation(self) -> bool:
        """Sync examples documentation from docs/examples to website and generate docs for each example."""
        print("📄 Synchronizing examples documentation...")

        if not self.source_examples.exists():
            print("⚠️  No examples documentation source directory found")
            return True  # Not an error, just no examples docs

        try:
            # Copy all markdown files from docs/examples directory (like index.md)
            for md_file in self.source_examples.rglob("*.md"):
                # Skip files using centralized check
                if self._should_skip_file(md_file):
                    continue

                # Preserve directory structure
                relative_path = md_file.relative_to(self.source_examples)
                dest_file = self.examples_dir / relative_path

                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(md_file, dest_file)

                # Add autogeneration comment
                self.add_autogeneration_comment(dest_file)

                print(f"   📄 Copied examples/{relative_path}")

            # Copy image assets (PNG, SVG, JPG, JPEG, GIF, WebP)
            image_extensions = [
                "*.png",
                "*.svg",
                "*.jpg",
                "*.jpeg",
                "*.gif",
                "*.webp",
                "*.PNG",
                "*.SVG",
                "*.JPG",
                "*.JPEG",
                "*.GIF",
                "*.WEBP",
            ]
            for pattern in image_extensions:
                for image_file in self.source_examples.rglob(pattern):
                    # Skip files using centralized check
                    if self._should_skip_file(image_file):
                        continue

                    # Preserve directory structure
                    relative_path = image_file.relative_to(self.source_examples)
                    dest_file = self.examples_dir / relative_path

                    # Create destination directory if needed
                    dest_file.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(image_file, dest_file)
                    print(f"   🖼️  Copied examples/{relative_path}")

            # Also copy any additional JSON files except sidebar.json
            for json_file in self.source_examples.rglob("*.json"):
                # Skip files using centralized check (includes sidebar.json)
                if self._should_skip_file(json_file):
                    print(f"   ⚠️  Skipping file: {json_file.name}")
                    continue

                # Preserve directory structure
                relative_path = json_file.relative_to(self.source_examples)
                dest_file = self.examples_dir / relative_path

                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(json_file, dest_file)
                print(f"   📄 Copied examples/{relative_path}")

            # Generate documentation for each example subdirectory
            examples_root = self.project_root / "examples"
            if examples_root.exists():
                # Get current git commit hash for GitHub links
                git_hash = self._get_git_commit_hash()
                sidebar_position = 2  # Start after index.md

                for subdir in sorted(examples_root.iterdir()):
                    if (
                        subdir.is_dir()
                        and not subdir.name.startswith(".")
                        and not subdir.name.startswith("__")
                    ):
                        readme_file = subdir / "README.md"

                        if readme_file.exists() and readme_file.stat().st_size > 0:
                            # Read the README content
                            with open(readme_file, encoding="utf-8") as f:
                                readme_content = f.read()

                            # Remove any existing frontmatter from README
                            frontmatter_pattern = r"^---\n.*?\n---\n\n?"
                            clean_content = re.sub(
                                frontmatter_pattern, "", readme_content, flags=re.DOTALL
                            )

                            # Add GitHub link after the first heading
                            github_link = f"**📂 [View Source Code](https://github.com/{GITHUB_ORG}/{GITHUB_REPO}/tree/{git_hash}/examples/{subdir.name})**\n\n"

                            # Insert the GitHub link after the first heading
                            lines = clean_content.split("\n")
                            if lines and lines[0].startswith("#"):
                                # Find the end of the first heading section
                                insert_position = 1
                                # Skip any empty lines after the heading
                                while (
                                    insert_position < len(lines)
                                    and lines[insert_position].strip() == ""
                                ):
                                    insert_position += 1

                                # Insert the GitHub link
                                lines.insert(insert_position, github_link.rstrip())
                                clean_content = "\n".join(lines)

                            # Create frontmatter for the documentation
                            frontmatter = f"""---
sidebar_position: {sidebar_position}
# This file was auto-generated and should not be edited manually
---

"""

                            # Create the final content
                            final_content = frontmatter + clean_content

                            # Create the destination file
                            dest_filename = f"{subdir.name}.md"
                            dest_file = self.examples_dir / dest_filename

                            # Write the file
                            with open(dest_file, "w", encoding="utf-8") as f:
                                f.write(final_content)

                            print(
                                f"   📄 Generated examples/{dest_filename} from {subdir.name}/README.md"
                            )
                            sidebar_position += 1

                        else:
                            print(
                                f"   ⚠️  Skipping {subdir.name} - no README.md or empty file"
                            )

            print("✅ Examples documentation synchronized successfully!")
            return True

        except Exception as e:
            print(f"❌ Error synchronizing examples documentation: {e}")
            return False

    def rename_init_files_to_index(self) -> bool:
        """Rename __init__.md files to index.md in the reference section for better navigation."""
        print("📝 Renaming __init__.md files to index.md in reference section...")

        try:
            # Find all __init__.md files in the reference directory
            for init_file in self.reference_dir.rglob("__init__.md"):
                # Calculate the new index.md path
                index_file = init_file.parent / "index.md"

                # Rename the file
                init_file.rename(index_file)

                # Calculate relative path for logging
                rel_path = index_file.relative_to(self.reference_dir)
                print(f"   📄 Renamed __init__.md → {rel_path}")

            print("✅ Reference __init__.md files renamed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error renaming __init__.md files: {e}")
            return False

    def add_frontmatter_to_reference_files(self) -> bool:
        """Add frontmatter to reference markdown files with simple sequential positioning."""
        print("📝 Adding frontmatter to reference files...")

        try:
            # Process only auto-generated markdown files in the mcp_kit subdirectory
            mcp_kit_dir = self.reference_dir / "mcp_kit"
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
                # Note: We don't add sidebar_position as Docusaurus autosidebar handles ordering

                # Add autogeneration comment as YAML comment
                fm_lines.append(
                    "# This file was auto-generated and should not be edited manually"
                )

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

    def generate_api_reference(self) -> bool:
        """Generate API reference documentation using pydoc-markdown with DocusaurusRenderer."""
        print("📚 Generating API reference documentation...")

        # Change to .docs-syncer directory for pydoc-markdown
        original_dir = os.getcwd()
        try:
            os.chdir(self.syncer_dir)

            # Run pydoc-markdown with verbose output
            _ = subprocess.run(
                ["pydoc-markdown", "--verbose", "pydoc-markdown.yml"],
                check=True,
                capture_output=True,
                text=True,
            )
            print("✅ API reference generated successfully!")

            # Remove any sidebar.json files that pydoc-markdown might have created
            print("🗑️  Cleaning up any sidebar.json files created by pydoc-markdown...")
            for sidebar_file in self.website_dir.rglob("sidebar.json"):
                try:
                    sidebar_file.unlink()
                    rel_path = sidebar_file.relative_to(self.website_dir)
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

    def list_created_files(self) -> dict[str, list[Path]]:
        """List all documentation files that were created."""
        files = {
            "user_guide": [],
            "examples": [],
            "api_reference": [],
            "categories": [],
        }

        # User guide files
        if self.user_guide_dir.exists():
            files["user_guide"] = list(self.user_guide_dir.rglob("*.md"))

        # Examples files
        if self.examples_dir.exists():
            files["examples"] = list(self.examples_dir.rglob("*.md"))

        # API reference files
        if self.reference_dir.exists():
            files["api_reference"] = list(self.reference_dir.rglob("*.md"))

        # Category files (both main and subdirectories)
        sdk_dir = self.website_dir / "docs" / "python-sdk"
        if sdk_dir.exists():
            files["categories"] = list(sdk_dir.rglob("_category_.json"))

        return files

    def run(self) -> bool:
        """Run the complete documentation generation process."""
        print("🚀 Starting comprehensive documentation generation...")

        # Step 1: Clean directories
        self.clean_documentation_dirs()

        # Step 2: Copy category files
        if not self.copy_category_files():
            print("⚠️  Category file copying failed, continuing...")

        # Step 3: Sync user documentation with comments
        if not self.sync_user_documentation():
            print("⚠️  User documentation sync failed, continuing with API reference...")

        # Step 4: Sync examples documentation
        if not self.sync_examples_documentation():
            print("⚠️  Examples documentation sync failed, continuing...")

        # Step 5: Generate API reference
        if not self.generate_api_reference():
            print("❌ API reference generation failed")
            return False
        # Step 6: Rename __init__.md files to index.md in reference section
        if not self.rename_init_files_to_index():
            print("⚠️  Renaming __init__.md files failed, continuing...")

        # Step 7: Sync manual reference documentation
        if not self.sync_reference_documentation():
            print("⚠️  Manual reference documentation sync failed, continuing...")

        # Step 8: Add frontmatter to reference files
        if not self.add_frontmatter_to_reference_files():
            print("⚠️  Adding frontmatter to reference files failed, continuing...")

        # Step 9: Remove empty headings from reference files (moved to end)
        if not self.remove_empty_headings():
            print("⚠️  Removing empty headings failed, continuing...")

        # Step 10: Show summary
        created_files = self.list_created_files()

        total_files = sum(len(files) for files in created_files.values())

        if total_files > 0:
            print(f"\n📄 Successfully created {total_files} documentation files:")

            if created_files["user_guide"]:
                print(f"\n📖 User Guide ({len(created_files['user_guide'])} files):")
                for file_path in sorted(created_files["user_guide"]):
                    rel_path = file_path.relative_to(self.user_guide_dir)
                    print(f"   - user-guide/{rel_path}")

            if created_files["examples"]:
                print(f"\n📚 Examples ({len(created_files['examples'])} files):")
                for file_path in sorted(created_files["examples"]):
                    rel_path = file_path.relative_to(self.examples_dir)
                    print(f"   - examples/{rel_path}")

            if created_files["api_reference"]:
                print(
                    f"\n🔧 API Reference ({len(created_files['api_reference'])} files):"
                )
                for file_path in sorted(created_files["api_reference"]):
                    rel_path = file_path.relative_to(self.reference_dir)
                    print(f"   - reference/{rel_path}")

            if created_files["categories"]:
                print(
                    f"\n📁 Category Files ({len(created_files['categories'])} files):"
                )
                for file_path in created_files["categories"]:
                    rel_path = file_path.relative_to(self.website_dir / "docs")
                    print(f"   - {rel_path}")

        else:
            print("⚠️  No documentation files were created")

        print("\n✅ Documentation generation completed!")
        return True

    def remove_empty_headings(self) -> bool:
        """Remove empty headings (levels 1-4) that have no content before the next heading or EOF."""
        print("🧹 Removing empty headings from reference files...")

        try:
            # Process only auto-generated markdown files in the mcp_kit subdirectory
            mcp_kit_dir = self.reference_dir / "mcp_kit"
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
                        heading_level = self._get_heading_level(line)
                        if heading_level > 0:
                            # Look ahead to see if this heading is empty
                            j = i + 1
                            has_content = False

                            # Check all lines until we find another heading or EOF
                            while j < len(lines):
                                next_line = lines[j]

                                # Get the level of the next line if it's a heading
                                next_heading_level = self._get_heading_level(next_line)

                                # If we hit another heading of same or higher level, stop looking
                                if (
                                    next_heading_level > 0
                                    and next_heading_level <= heading_level
                                ):
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
                            print(
                                f"   🗑️  Removed empty heading: {heading} from {md_file.name}"
                            )

                # Write the final content back to the file if changes were made
                if content != original_content:
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.write(content)

            print("✅ Empty headings removed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error removing empty headings: {e}")
            return False

    def _get_heading_level(self, line: str) -> int:
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


def main():
    """CLI entry point for documentation generation."""
    generator = DocGenerator()
    success = generator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
