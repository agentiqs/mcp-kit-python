---
sidebar_position: 2
# This file was auto-generated and should not be edited manually
---

# Installation

## Requirements

- Python 3.10 or higher
- uv

## Install from PyPI

```bash
uv add mcp-kit
```


## Install from Source

```bash
git clone https://github.com/agentiqs/mcp-kit-python.git
cd mcp-kit-python
pip install -e .
```

## Verify Installation

```python
import mcp_kit
print(mcp_kit.__version__)
```

## Optional Dependencies

### Framework Adapters

For LangGraph integration:
```bash
uv add mcp-kit[langgraph]
```

### Development Setup

For contributing to MCP Kit:

```bash
git clone https://github.com/agentiqs/mcp-kit-python.git
cd mcp-kit-python
uv add --with dev
```

## Environment Setup

### Configuration Directory

MCP Kit looks for .env configuration files and loads each LLM provider specific variables

### Environment Variables

Common environment variables:

```bash
<PROVIDER>_API_KEY="your_api_key"
```

## Next Steps

- [Configuration Guide](./configuration.md) - Set up your first proxy
- [Examples](../examples) - Real-world usage examples
