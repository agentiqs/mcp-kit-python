# Proxy Configuration Examples

This directory contains various proxy configuration examples demonstrating different target types and routing strategies supported by mcp-kit.

## Configuration Files

### Target Types

- **`mcp_target.yaml`** & **`mcp_target.json`** - Connect to real MCP servers
- **`oas_target.yaml`** - Connect to OpenAPI/Swagger endpoints
- **`multiplex_target.yaml`** - Route requests to multiple targets

### Mocked Target Examples

- **`mocked_random_target.yaml`** - Generate random/fake data responses for tools
- **`mocked_oas_target.yaml`** - Mock OpenAPI endpoints with LLM-generated responses
- **`mocked_tools_target.yaml`** - Mock tool calls only (delegates prompts to base target)
- **`mocked_prompts.yaml`** - Mock prompts only (delegates tools to base target)
- **`mocked_prompts_and_tools_target.yaml`** - Mock both prompts and tools with different generators

### Features Demonstrated

- **Multiple target types**: MCP, OpenAPI, and mocked targets
- **Response generation**: LLM-powered and random data generation
- **Selective mocking**: Mock only tools, only prompts, or both
- **Prompt templates**: Concise LLM prompt examples (summarization, code review, translation)
- **Load balancing**: Multiplex target with round-robin strategy
- **Environment variables**: Configuration templating support

## Usage

Use the `main.py` script to test different configurations:

```bash
python main.py
```

Each configuration file can be used independently with the mcp-kit proxy system to demonstrate different integration patterns and response generation strategies.