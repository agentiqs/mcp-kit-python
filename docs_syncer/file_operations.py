#!/usr/bin/env python3
"""
File operations module for the documentation generator.

This module handles common file operations with consistent patterns.
"""

import shutil
from collections.abc import Callable
from pathlib import Path


class FileOperations:
    """Handles common file operations with consistent patterns."""

    IMAGE_EXTENSIONS = [
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

    def __init__(self, should_skip_file_func: Callable[[Path], bool]) -> None:
        self.should_skip_file = should_skip_file_func

    def copy_files_recursive(
        self, source_dir: Path, dest_dir: Path, patterns: list[str], file_type: str = "file"
    ) -> int:
        """Copy files matching patterns from source to destination, preserving structure."""
        copied_count = 0

        for pattern in patterns:
            for file_path in source_dir.rglob(pattern):
                if self.should_skip_file(file_path):
                    continue

                # Preserve directory structure
                relative_path = file_path.relative_to(source_dir)
                dest_file = dest_dir / relative_path

                # Create destination directory if needed
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(file_path, dest_file)
                print(f"   📄 Copied {file_type}: {relative_path}")
                copied_count += 1

        return copied_count

    def clean_directory(self, directory: Path, description: str) -> None:
        """Clean a directory, creating it if it doesn't exist."""
        if directory.exists():
            for item in directory.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print(f"✅ Cleaned {description}")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {description}")
