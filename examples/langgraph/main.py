import logging

from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent

from mcp_kit import ProxyMCP

logging.basicConfig(level=logging.INFO)
# Suppress INFO logging from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()


async def run_workflow(client, initial_prompt: str):
    """Main function to run the LangGraph ReAct agent with MCP tools."""
    logger.info(f"Starting LangGraph ReAct agent workflow for query: {initial_prompt}")

    # Get the MCP tools as LangChain tools
    tools = await client.get_tools(server_name="odoo_mcp_mocked")
    logger.info(f"Loaded {len(tools)} tools: {[tool.name for tool in tools]}")

    # Create the ReAct agent with the tools
    agent = create_react_agent(model="google_genai:gemini-2.0-flash", tools=tools)

    # Run the agent
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": initial_prompt}]},
    )

    # Extract the final response
    final_message = response["messages"][-1]
    result = final_message.content

    print("\n" + "=" * 60)
    print("LANGGRAPH REACT AGENT RESULT")
    print("=" * 60)
    print(result)
    print("=" * 60)


async def main():
    # Create ProxyMCP and get tools compatible with LangGraph
    client = ProxyMCP.from_config(
        "proxy_config.yaml",
    ).langgraph_multi_server_mcp_client()
    async with client.session("odoo_mcp_mocked") as _:
        logger.info("Accounting agent workflow started...")

        await run_workflow(
            client,
            initial_prompt="What are the expenses and revenues of May 2025?",
        )

        logger.info("Workflow completed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
