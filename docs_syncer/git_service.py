#!/usr/bin/env python3
"""
Git service module for documentation generator.

This module handles Git operations like getting commit hashes.
"""

import subprocess
from pathlib import Path


class GitService:
    """Handles Git operations for the documentation generator."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def get_commit_hash(self) -> str:
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
