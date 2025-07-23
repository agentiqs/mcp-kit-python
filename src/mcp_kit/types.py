from collections.abc import Awaitable, Callable
from typing import Any

from mcp.types import Content

CallToolHandler = Callable[[str, dict[str, Any] | None], Awaitable[list[Content]]]

CallToolDispatch = Callable[[str, dict[str, Any] | None, CallToolHandler], Awaitable[list[Content]]]
