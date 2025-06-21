---
sidebar_position: 2
# This file was auto-generated and should not be edited manually
---

# LangGraph Accounting Agent Example

**📂 [View Source Code](https://github.com/agentiqs/mcp-kit-python/tree/0f830eddfdcc1ee5359a24197da3f2e67774f340/examples/langgraph)**
This example demonstrates how to use LangGraph's ReAct agent with MCP tools for accounting queries.

## Features

- **Framework**: LangGraph with `create_react_agent`
- **Tools**: MCP tools converted to LangChain tools via `langchain-mcp-adapters`
- **Agent Type**: ReAct (Reasoning and Acting) pattern
- **Model**: ChatOpenAI (GPT-4.1-nano)

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Set up your environment variables (create a `.env` file):
```bash
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=${GOOGLE_API_KEY}
```

## Usage

```bash
uv run main.py
```

## Configuration

The `proxy_config.yaml` file defines a mocked Odoo MCP target that provides accounting tools like:
- `get_expenses` - Retrieve expense records
- `get_revenues` - Retrieve revenue records
- `get_account_balance` - Get account balances

The configuration uses LLM-generated responses for realistic accounting data simulation.
