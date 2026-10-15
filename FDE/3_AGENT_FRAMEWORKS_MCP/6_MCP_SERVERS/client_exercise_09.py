"""HTTP MCP client wrapper for Exercise 9."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import Client


SERVER_URL = "http://127.0.0.1:8000/mcp"


class Exercise09Client:
    """Application-facing methods that communicate with the MCP server."""

    def __init__(self, client: Client[Any]) -> None:
        self._client = client

    async def list_tools(self):
        """Return the tools advertised by the connected MCP server."""
        return await self._client.list_tools()

    async def get_customer(self, customer_id: str) -> Any:
        """Call the server's get_customer MCP tool and return its data."""
        result = await self._client.call_tool(
            "get_customer",
            {"customer_id": customer_id},
        )
        return result.data


@asynccontextmanager
async def connect_to_server() -> AsyncIterator[Exercise09Client]:
    """Connect to the Exercise 9 server over Streamable HTTP."""
    async with Client(SERVER_URL) as client:
        yield Exercise09Client(client)
