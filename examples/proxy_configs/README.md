# Proxy Configuration Examples

This directory contains various proxy configuration examples demonstrating different target types and routing strategies supported by mcp-kit.

## Configuration Files

### Target Types

- **`mcp_target.yaml`** & **`mcp_target.json`** - Connect to real MCP servers
- **`oas_target.yaml`** - Connect to OpenAPI/Swagger endpoints
- **`mocked_llm_target.yaml`** - Generate responses using LLM (OpenAI GPT)
- **`mocked_random_target.yaml`** - Generate random/fake data responses  
- **`multiplex_target.yaml`** - Route requests to multiple targets

### Features Demonstrated

- **Multiple target types**: MCP, OpenAPI, and mocked targets
- **Response generation**: LLM-powered and random data generation
- **Load balancing**: Multiplex target with round-robin strategy
- **Environment variables**: Configuration templating support
- **Tool definitions**: Complete schema definitions for accounting tools

## Usage

Use the `proxy_config_usage.py` script to test different configurations:

```bash
python proxy_config_usage.py
```

Each configuration file can be used independently with the mcp-kit proxy system to demonstrate different integration patterns and response generation strategies.