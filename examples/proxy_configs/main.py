#!/usr/bin/env python3
"""Example usage of ProxyMCP.from_config() factory method.

This script demonstrates how to create ProxyMCP instances from configuration files
supporting all target types: MCP, OAS, Mocked, and Multiplex.
"""

import asyncio
from pathlib import Path

from mcp_kit import ProxyMCP


async def main() -> None:
    """Demonstrate ProxyMCP.from_config() usage with all configuration files in the directory."""

    # Find all configuration files in the proxy_configs directory
    config_dir = Path(".")
    config_files: list[Path] = []

    # Look for YAML and JSON files
    for pattern in ["*.yaml", "*.yml", "*.json"]:
        config_files.extend(config_dir.glob(pattern))

    # Sort for consistent output
    config_files.sort()

    if not config_files:
        print("❌ No configuration files found in examples/proxy_configs/")
        raise SystemExit(1)

    print(f"Found {len(config_files)} configuration file(s):")
    for config_file in config_files:
        print(f"  - {config_file.name}")
    print()

    # Test each configuration file
    for i, config_file in enumerate(config_files, 1):
        print(f"=== Configuration {i}/{len(config_files)}: {config_file.name} ===")

        proxy = ProxyMCP.from_config(config_file)
        print(f"Created proxy with target: {proxy.target.name}")
        print(f"Target type: {type(proxy.target).__name__}")

        # Show additional details for specific target types
        if hasattr(proxy.target, "target"):  # Mocked targets
            print(f"Base target type: {type(proxy.target.target).__name__}")
            if hasattr(proxy.target, "mock_config"):
                print(f"Generator type: {type(proxy.target.mock_config.response_generator).__name__}")

        if hasattr(proxy.target, "_targets_dict"):  # Multiplex targets
            print(f"Number of sub-targets: {len(proxy.target._targets_dict)}")
            for j, (name, target) in enumerate(proxy.target._targets_dict.items()):
                print(f"  Sub-target {j + 1}: {name} -> {target.name} ({type(target).__name__})")

        print()

    print(f"✅ All {len(config_files)} configuration(s) parsed successfully!")
    print("All proxy configurations are valid!")


if __name__ == "__main__":
    asyncio.run(main())
