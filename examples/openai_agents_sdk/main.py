import logging

from agents import Agent, Runner, trace
from dotenv import load_dotenv

from mcp_kit import ProxyMCP

logging.basicConfig(level=logging.INFO)
# Suppress INFO logging from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()


async def run_workflow(odoo_mcp_server, initial_prompt: str):
    """Execute the multi-agent workflow with proper handoffs."""
    # Accounting Agent
    accounting_agent = Agent(
        name="AccountingAgent",
        instructions="""
You are an Accounting Agent, you have access to accounting tools and can answer accounting questions accurately.
""",
        model="gpt-4.1-nano",
        mcp_servers=[odoo_mcp_server],
    )

    response = await Runner.run(accounting_agent, initial_prompt)

    logger.info(f"Task completed: {response.final_output}")


async def main():
    async with ProxyMCP.from_config(
        "proxy_config.yaml",
    ).openai_agents_mcp_server() as odoo_mock_mcp:
        # Start trace for monitoring
        with trace("mcp-kit: Example Accounting Agent Workflow") as trace_context:
            logger.info("Accounting agent workflow started...")

            await run_workflow(
                odoo_mock_mcp,
                initial_prompt="What are the expenses and revenues of May 2025?",
            )

            logger.info("Workflow completed!")
            logger.info(
                f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_context.trace_id}",
            )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
