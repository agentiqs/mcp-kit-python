---
sidebar_position: 2
# This file was auto-generated and should not be edited manually
---

# ProxyMCP Configuration System

This document describes how to use the `ProxyMCP.from_config()` factory method to create ProxyMCP instances from configuration files.

## Overview

The configuration system uses a clean, modular architecture where each object type is responsible for creating itself from configuration. The factory method supports creating instances with any type currently supported in `src/mcp_kit/`:

## Architecture

This design follows the single responsibility principle, where each target is responsible for understanding its own configuration format.

## Configuration Format

Configuration files support both standard YAML or JSON formats.

### Using Target Factory Methods Directly

You can also create targets directly using their individual factory methods:

```python
from omegaconf import OmegaConf
from src.mcp_kit.factory import create_target_from_config

# Create targets directly
config = OmegaConf.load("config.yaml")

# Direct target creation
target = create_target_from_config(config.target)

# Then wrap in ProxyMCP
proxy = ProxyMCP(mcp_target)
```

## Example Configuration Files

Example configuration files are available in `examples/proxy_configs/`:

- `mcp_target.yaml` - Simple MCP target
- `oas_target.yaml` - OpenAPI specification target
- `mocked_random_target.yaml` - Mocked target with random responses
- `mocked_llm_target.yaml` - Mocked target with LLM responses
- `multiplex_target.yaml` - Multiplex target combining multiple servers
- `mcp_target.json` - JSON format example

## Error Handling

The factory method will raise `ValueError` for:
- Unknown target types
- Unknown response generator types
- Missing required configuration fields

## Testing

Unit tests are available for both the high-level ProxyMCP factory and individual target factories:

**ProxyMCP factory tests:**
```bash
uv run pytest tests/test_proxy_config.py::TestProxyMCPFromConfig -v
```

**Individual target factory tests:**
```bash
uv run pytest tests/test_target_from_config.py::TestTargetFromConfig -v
```

**Run all configuration tests:**
```bash
uv run pytest tests/test_proxy_config.py tests/test_target_from_config.py -v
```

The test suite covers:
- All target types and their factory methods
- Error handling for invalid configurations
- Nested target configurations (e.g., mocked targets with mocked base targets)
- Both YAML and JSON configuration formats
- Edge cases like minimal configurations and default values

## Future Enhancements

The configuration system is designed to be easily extensible for future features like:
- Multiple proxy instances from a single configuration file
- Environment variable substitution
- Configuration validation schemas
- Dynamic configuration reloading
