#!/usr/bin/env python3
"""Quick integration test to verify the refactored factory system works end-to-end."""

from omegaconf import OmegaConf

from mcp_kit.factory import (
    create_response_generator_from_config,
    create_target_from_config,
)


def test_integration():
    """Test that the factory system works end-to-end."""
    # Test target creation
    print("Testing target creation...")

    mcp_config = OmegaConf.create(
        {"type": "mcp", "name": "test-mcp", "url": "http://localhost:8080/mcp"},
    )
    mcp_target = create_target_from_config(mcp_config)
    print(f"✓ Created MCP target: {type(mcp_target).__name__}")

    # Test generator creation
    print("\nTesting generator creation...")

    random_config = OmegaConf.create({"type": "random"})
    random_generator = create_response_generator_from_config(random_config)
    print(f"✓ Created Random generator: {type(random_generator).__name__}")

    llm_config = OmegaConf.create({"type": "llm", "model": "gpt-4"})
    llm_generator = create_response_generator_from_config(llm_config)
    print(f"✓ Created LLM generator: {type(llm_generator).__name__}")

    # Test mocked target with generator
    print("\nTesting mocked target with generator...")

    mocked_config = OmegaConf.create(
        {
            "type": "mocked",
            "base_target": {
                "type": "mcp",
                "name": "base-mcp",
                "url": "http://localhost:8080/mcp",
            },
            "response_generator": {"type": "random"},
        },
    )
    mocked_target = create_target_from_config(mocked_config)
    print(f"✓ Created Mocked target: {type(mocked_target).__name__}")

    print("\n🎉 All integration tests passed!")


if __name__ == "__main__":
    test_integration()
