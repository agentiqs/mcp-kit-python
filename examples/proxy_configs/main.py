#!/usr/bin/env python3
"""Example usage of ProxyMCP.from_config() factory method.

This script demonstrates how to create ProxyMCP instances from configuration files
supporting all target types: MCP, OAS, Mocked, and Multiplex.
"""

import asyncio
from pathlib import Path

from mcp_kit import ProxyMCP


async def main():
    """Demonstrate ProxyMCP.from_config() usage with different target types."""
    # Example 1: MCP Target
    print("=== MCP Target Example ===")
    try:
        mcp_proxy = ProxyMCP.from_config("examples/proxy_configs/mcp_target.yaml")
        print(f"Created MCP proxy with target: {mcp_proxy.target.name}")
        print(f"Target type: {type(mcp_proxy.target).__name__}")
    except Exception as e:
        print(f"Error creating MCP proxy: {e}")

    # Example 2: OAS Target
    print("\n=== OAS Target Example ===")
    try:
        oas_proxy = ProxyMCP.from_config("examples/proxy_configs/oas_target.yaml")
        print(f"Created OAS proxy with target: {oas_proxy.target.name}")
        print(f"Target type: {type(oas_proxy.target).__name__}")
    except Exception as e:
        print(f"Error creating OAS proxy: {e}")

    # Example 3: Mocked Target with Random Generator
    print("\n=== Mocked Target (Random) Example ===")
    try:
        mocked_proxy = ProxyMCP.from_config(
            "examples/proxy_configs/mocked_random_target.yaml",
        )
        print(f"Created Mocked proxy with target: {mocked_proxy.target.name}")
        print(f"Target type: {type(mocked_proxy.target).__name__}")
        print(f"Base target type: {type(mocked_proxy.target.target).__name__}")  # type: ignore
        print(
            f"Generator type: {type(mocked_proxy.target.mock_config.response_generator).__name__}",
        )  # type: ignore
    except Exception as e:
        print(f"Error creating Mocked proxy: {e}")

    # Example 4: Mocked Target with LLM Generator
    print("\n=== Mocked Target (LLM) Example ===")
    try:
        mocked_llm_proxy = ProxyMCP.from_config(
            "examples/proxy_configs/mocked_llm_target.yaml",
        )
        print(f"Created Mocked LLM proxy with target: {mocked_llm_proxy.target.name}")
        print(f"Target type: {type(mocked_llm_proxy.target).__name__}")
        print(f"Base target type: {type(mocked_llm_proxy.target.target).__name__}")  # type: ignore
        print(
            f"Generator type: {type(mocked_llm_proxy.target.mock_config.response_generator).__name__}",
        )  # type: ignore
    except Exception as e:
        print(f"Error creating Mocked LLM proxy: {e}")

    # Example 5: Multiplex Target
    print("\n=== Multiplex Target Example ===")
    try:
        multiplex_proxy = ProxyMCP.from_config(
            "examples/proxy_configs/multiplex_target.yaml",
        )
        print(f"Created Multiplex proxy with target: {multiplex_proxy.target.name}")
        print(f"Target type: {type(multiplex_proxy.target).__name__}")
        print(f"Number of sub-targets: {len(multiplex_proxy.target._targets_dict)}")  # type: ignore
        for i, (name, target) in enumerate(
            multiplex_proxy.target._targets_dict.items(),
        ):  # type: ignore
            print(
                f"  Sub-target {i + 1}: {name} -> {target.name} ({type(target).__name__})",
            )
    except Exception as e:
        print(f"Error creating Multiplex proxy: {e}")

    # Example 6: JSON Configuration
    print("\n=== JSON Configuration Example ===")
    try:
        json_proxy = ProxyMCP.from_config("examples/proxy_configs/mcp_target.json")
        print(f"Created JSON proxy with target: {json_proxy.target.name}")
        print(f"Target type: {type(json_proxy.target).__name__}")
    except Exception as e:
        print(f"Error creating JSON proxy: {e}")

    # Example 7: Using pathlib.Path
    print("\n=== Pathlib.Path Example ===")
    try:
        config_path = Path("examples/proxy_configs/mcp_target.yaml")
        path_proxy = ProxyMCP.from_config(config_path)
        print(f"Created proxy from Path with target: {path_proxy.target.name}")
        print(f"Target type: {type(path_proxy.target).__name__}")
    except Exception as e:
        print(f"Error creating proxy from Path: {e}")


if __name__ == "__main__":
    asyncio.run(main())
