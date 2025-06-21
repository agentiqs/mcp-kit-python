import logging
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from mcp_kit import ProxyMCP

# Suppress INFO logging from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()


async def run_workflow(session, initial_prompt: str) -> None:  # type: ignore[no-untyped-def]
    """Main function to run Claude with MCP tools."""
    model = "claude-3-5-haiku-20241022"
    messages: list[dict[str, Any]] = [{"role": "user", "content": initial_prompt}]

    response = await session.list_tools()
    available_tools = [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
        }
        for tool in response.tools
    ]

    anthropic = Anthropic()

    # Initial Claude API call
    response = anthropic.messages.create(model=model, max_tokens=1000, messages=messages, tools=available_tools)

    # Process response and handle tool calls
    final_text = []

    while True:
        assistant_message_content = []
        tool_results = []

        for content in response.content:
            if content.type == "text":
                final_text.append(content.text)
                assistant_message_content.append(content)
            elif content.type == "tool_use":
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                assistant_message_content.append(content)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result.content,
                    }
                )

        # If there were tool calls, add them to conversation and get next response
        if tool_results:
            messages.append({"role": "assistant", "content": assistant_message_content})
            messages.append({"role": "user", "content": tool_results})

            response = anthropic.messages.create(model=model, max_tokens=1000, messages=messages, tools=available_tools)
        else:
            # No more tool calls, we're done
            break

    result = "\n".join(final_text)

    logger.info(f"Task completed:\n{result}")


async def main() -> None:
    # Create ProxyMCP and get tools compatible with the official MCP Client Session
    async with ProxyMCP.from_config(
        "proxy_config.yaml",
    ).client_session_adapter() as session:
        logger.info("Accounting agent workflow started...")

        await run_workflow(
            session,
            initial_prompt="What are the expenses and revenues of May 2025?",
        )

        logger.info("Workflow completed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
