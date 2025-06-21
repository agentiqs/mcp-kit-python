# MCP Kit Python

**MCP tooling for developing and optimizing multi-agent AI systems**

[![Python](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-mcp--kit-orange.svg)](https://pypi.org/project/mcp-kit/)
=============================
A comprehensive toolkit for working with the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), providing seamless integration between AI agents and various data sources, APIs, and services. Whether you're building, testing, or deploying multi-agent systems, MCP Kit simplifies the complexity of tool orchestration and provides powerful mocking capabilities for development.

## Features

### **Flexible Target System**
- **MCP Servers**: Connect to existing MCP servers (hosted or from specifications)
- **OpenAPI Integration**: Automatically convert REST APIs to MCP tools using OpenAPI/Swagger specs
- **Mock Responses**: Generate realistic test data using LLM or random generators
- **Multiplexing**: Combine multiple targets into a unified interface

### **Framework Adapters**
- **OpenAI Agents SDK**: Native integration with OpenAI's agent framework
- **LangGraph**: Seamless tool integration for LangGraph workflows
- **Generic Client Sessions**: Direct MCP protocol communication
- **Official MCP Server**: Standard MCP server wrapper

### **Configuration-Driven Architecture**
- **YAML/JSON Configuration**: Declarative setup for complex workflows
- **Factory Pattern**: Clean, testable component creation
- **Environment Variables**: Secure credential management

### **Advanced Response Generation**
- **LLM-Powered Mocking**: Generate contextually appropriate responses using LLMs
- **Random Data Generation**: Create test data for development and testing
- **Custom Generators**: Implement your own response generation logic

---

## Quick Start

### Installation

```bash
uv add mcp-kit
```

### Basic Usage

#### First you write the Proxy config:

```yaml
# proxy_config.yaml
""" A mocked REST API target given the OpenAPI spec using LLM-generated responses
"""
target:
  type: mocked
  base_target:
    type: oas
    name: base-oas-server
    spec_url: https://petstore3.swagger.io/api/v3/openapi.json
  response_generator:
    type: llm
    model: openai/gpt-4.1-nano
```

#### Don't forget to setup the LLM API KEY:

```bash
# .env
OPENAI_API_KEY="your_openai_key"
```

#### Then we can use it as any other MCP:


```python
# main.py
from mcp_kit import ProxyMCP


async def main():
    # Create proxy from configuration
    proxy = ProxyMCP.from_config("proxy_config.yaml")

    # Use with MCP client session adapter
    async with proxy.client_session_adapter() as session:
        tools = await session.list_tools()
        result = await session.call_tool("get_pet", {"pet_id": "777"})
        print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

---

## Core Concepts

### Targets

**Targets** are the core abstraction in MCP Kit, representing different types of tool providers:

#### MCP Target
Connect to existing MCP servers:
```yaml
target:
  type: mcp
  name: my-mcp-server
  url: http://localhost:8080/mcp
  headers:
    Authorization: Bearer token123
```

#### OpenAPI Target
Convert REST APIs to MCP tools:
```yaml
target:
  type: oas
  name: petstore-api
  spec_url: https://petstore3.swagger.io/api/v3/openapi.json
```

#### Mocked Target
Generate fake responses for testing:
```yaml
target:
  type: mocked
  base_target:
    type: mcp
    name: test-server
    url: http://localhost:9000/mcp
  response_generator:
    type: llm
    model: openai/gpt-4.1-nano
```

#### Multiplex Target
Combine multiple targets:
```yaml
target:
  type: multiplex
  name: combined-services
  targets:
    - type: mcp
      name: weather-service
      url: http://localhost:8080/mcp
    - type: oas
      name: petstore
      spec_url: https://petstore3.swagger.io/api/v3/openapi.json
```

### Adapters

**Adapters** provide framework-specific interfaces for your targets:

- **Client Session Adapter**: Direct MCP protocol communication
- **OpenAI Agents Adapter**: Integration with OpenAI's agent framework
- **LangGraph Adapter**: Tools for LangGraph workflows
- **Official MCP Server**: Standard MCP server wrapper

### Response Generators

**Response Generators** create mock responses for testing and development:

- **LLM Generator**: Uses language models to generate contextually appropriate responses
- **Random Generator**: Creates random test data
- **Custom Generators**: Implement your own logic

---

## Examples

### OpenAI Agents SDK Integration

```python
from mcp_kit import ProxyMCP
from agents import Agent, Runner, trace
import asyncio

async def openai_example():
    proxy = ProxyMCP.from_config("proxy_config.yaml")

    async with proxy.openai_agents_mcp_server() as mcp_server:
        # Use with OpenAI Agents SDK
        agent = Agent(
            name="research_agent",
            instructions="You are a research assistant with access to various tools.",
            model="gpt-4.1-nano",
            mcp_servers=[mcp_server]
        )

        response = await Runner.run(
            agent,
            "What's the weather like in San Francisco?"
        )
        print(response.final_output)

if __name__ == "__main__":
    asyncio.run(openai_example())
```

### LangGraph Workflow Integration

```python
from mcp_kit import ProxyMCP
from langgraph.prebuilt import create_react_agent
import asyncio

async def langgraph_example():
    proxy = ProxyMCP.from_config("proxy_config.yaml")

    # Get LangChain-compatible tools
    client = proxy.langgraph_multi_server_mcp_client()

    async with client.session("your_server_name") as _:
        # Get the MCP tools as LangChain tools
        tools = await client.get_tools(server_name="your_server_name")

        # Create ReAct agent
        agent = create_react_agent(model="google_genai:gemini-2.0-flash", tools=tools)

        # Run workflow
        response = await agent.ainvoke({
            "messages": [{"role": "user", "content": "Analyze Q1 expenses"}]
        })

        # Extract result
        final_message = response["messages"][-1]
        print(final_message.content)

if __name__ == "__main__":
    asyncio.run(langgraph_example())
```

### Testing with Mocked Responses

```python
from mcp_kit import ProxyMCP
import asyncio

async def testing_example():
    # Configuration with LLM-powered mocking
    proxy = ProxyMCP.from_config("proxy_config.yaml")

    async with proxy.client_session_adapter() as session:
        # These calls will return realistic mock data
        tools = await session.list_tools()
        expenses = await session.call_tool("get_expenses", {"period": "Q1"})
        revenues = await session.call_tool("get_revenues", {"period": "Q1"})

        print(f"Available tools: {[tool.name for tool in tools.tools]}")
        print(f"Mock expenses: {expenses}")
        print(f"Mock revenues: {revenues}")

if __name__ == "__main__":
    asyncio.run(testing_example())
```

### Configuration Examples

#### Development with Mocking
```yaml
# dev_proxy_config.yaml
target:
  type: mocked
  base_target:
    type: oas
    name: accounting-api
    spec_url: https://api.company.com/accounting/openapi.json
  response_generator:
    type: llm
    model: openai/gpt-4.1-nano
```

#### Production MCP Server
```yaml
# prod_proxy_config.yaml
target:
  type: mcp
  name: production-accounting
  url: https://mcp.company.com/accounting
  headers:
    Authorization: Bearer ${PROD_API_KEY}
    X-Client-Version: "1.0.0"
```

#### Multi-Service Architecture
```yaml
# multi_proxy_config.yaml
target:
  type: multiplex
  name: enterprise-tools
  targets:
    - type: mcp
      name: crm-service
      url: https://mcp.company.com/crm
    - type: oas
      name: analytics-api
      spec_url: https://api.company.com/analytics/openapi.json
    - type: mocked
      base_target:
        type: mcp
        name: experimental-service
        url: https://beta.company.com/mcp
      response_generator:
        type: random
```

---

## Advanced Configuration

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=your-openai-key
WEATHER_API_KEY=your-weather-key
```

### Custom Response Generators

```python
from mcp_kit.generators import ResponseGenerator
from mcp_kit import ProxyMCP

class CustomGenerator(ResponseGenerator):
    async def generate(self, target_name: str, tool: Tool, arguments: dict[str, Any] | None = None) -> list[Content]:
        # Your custom logic here
        return [TextContent(type="text", text=f"Custom response for {tool.name} on {target_name}")]

# Use in configuration
proxy = ProxyMCP(
    target=MockedTarget(
        base_target=McpTarget("test", "http://localhost:8080"),
        mock_config=MockConfig(response_generator=CustomGenerator())
    )
)
```

---

## Project Structure

```
mcp-kit-python/
├── src/mcp_kit/
│   ├── adapters/          # Framework adapters
│   │   ├── client_session.py
│   │   ├── openai.py
│   │   └── langgraph.py
│   ├── generators/        # Response generators
│   │   ├── llm.py
│   │   └── random.py
│   ├── targets/          # Target implementations
│   │   ├── mcp.py
│   │   ├── oas.py
│   │   ├── mocked.py
│   │   └── multiplex.py
│   ├── factory.py        # Factory pattern implementation
│   └── proxy.py          # Main ProxyMCP class
├── examples/             # Usage examples
│   ├── openai_agents_sdk/
│   ├── langgraph/
│   ├── mcp_client_session/
│   └── proxy_configs/
└── tests/               # Test suite
```

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/agentiqs/mcp-kit-python/blob/main/CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/agentiqs/mcp-kit-python.git
cd mcp-kit-python
uv sync --dev
pre-commit install
```

### Running Tests

```bash
uv run pytest tests/ -v
```

---

## Documentation

- [Installation Guide](https://github.com/agentiqs/mcp-kit-python/blob/main/docs/user-guide/installation.md)
- [Configuration Reference](https://github.com/agentiqs/mcp-kit-python/blob/main/docs/user-guide/configuration.md)
- [Framework Adapters](https://github.com/agentiqs/mcp-kit-python/blob/main/docs/user-guide/adapters.md)
- [API Reference](https://github.com/agentiqs/mcp-kit-python/blob/main/docs/reference/)
- [Examples](https://github.com/agentiqs/mcp-kit-python/blob/main/docs/examples/)

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/agentiqs/mcp-kit-python/blob/main/LICENSE) file for details.

---

## Support

- [GitHub Issues](https://github.com/agentiqs/mcp-kit-python/issues)
- [Documentation](https://agentiqs.ai/docs/category/python-sdk)
- [Examples](https://github.com/agentiqs/mcp-kit-python/blob/main/examples/)

---

**Built with ❤️ by [Agentiqs](https://agentiqs.ai)**