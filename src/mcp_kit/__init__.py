"""MCP Kit: A comprehensive toolkit for working with Model Context Protocol (MCP) servers.

This package provides a flexible framework for mocking, testing and optimizing
agent interactions with the world by converting any target to the widely adopted Model Context Protocol
and proxying tool calls where we can choose to mock or pass through.
It includes support for various target interaction types, mock response generators, and adapter patterns to integrate
with different AI frameworks and tools.

Key Components:
- **Targets**: Different types of interaction endpoints (MCP servers (hosted or spec), REST APIs (hosted or spec) and in
the near future file systems, computer use, code interpreter, etc.)
- **Adapters**: Integration patterns for various frameworks (OpenAI Agents, LangGraph, Official MCP Client and Server)
- **Generators**: Response generation strategies for testing and mocking (random text or LLM-based responses)
- **Proxy**: Central interface providing multiple adapter patterns for a single target

Example:
    ```python
    from mcp_kit import ProxyMCP

    # Create a proxy from configuration that contains a target definition and a mock strategy
    proxy = ProxyMCP.from_config("proxy_config.yaml")

    # Use as MCP Client Session
    async with proxy.client_session_adapter() as session:
        tools = await session.list_tools()

        # Add tools to an LLM and catch tool calls
        ...

        # Execute a tool call
        await session.call_tool(
            name="example_tool",
            arguments={"param1": "value1", "param2": "value2"},
        )

    # Use as OpenAI Agent
    async with proxy.openai_agents_mcp_server() as mcp_server:
        agent = Agent(
            name="example_agent",
            instructions="This agent can call tools.",
            tools=tools,
            mcp_servers=[mcp_server],
        )

        response = await Runner.run(agent, "some input")

    #  Use as LangGraph Multi-Server MCP Client
    async with proxy.langgraph_multi_server_mcp_client() as client:
        # Get the MCP tools as LangChain tools
        tools = await client.get_tools(server_name="odoo_mcp_mocked")

        # Create the ReAct agent with the tools
        agent = create_react_agent(model="provider:model", tools=tools)

        # Run the agent
        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "some input"}]},
        )
    ```
"""

from mcp_kit.proxy import ProxyMCP

__all__ = ["ProxyMCP"]
