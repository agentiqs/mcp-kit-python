"""
Documentation generator module for mcp-kit-python.

This module provides a modular documentation generation system with separated concerns:

Core Components:
- DocGenerator: Main orchestrator that coordinates all documentation generation steps
- ConfigManager: Handles all path configuration and project structure setup

Services:
- CleanupService: Handles cleaning and preparation of documentation directories
- DocumentationSyncer: Handles synchronization of different documentation sections
- ExamplesGenerator: Generates documentation for example projects from README files
- ApiGenerator: Handles API reference documentation generation using pydoc-markdown
- CategoryManager: Manages _category_.json files for Docusaurus
- ReportingService: Generates summary reports of created documentation files

Utilities:
- FileOperations: Common file operations with pattern matching and directory management
- ContentProcessor: Content manipulation (frontmatter, links, heading cleanup)
- GitService: Git operations like getting commit hashes

Usage:
    from generator import DocGenerator

    generator = DocGenerator()
    success = generator.run()
"""

__version__ = "0.1.0"

from .generator import DocGenerator

__all__ = ["DocGenerator"]
