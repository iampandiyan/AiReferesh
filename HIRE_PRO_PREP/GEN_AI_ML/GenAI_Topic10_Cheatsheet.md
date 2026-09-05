# GenAI/AI-ML Cheatsheet — Topic 10 (MCP Server & Client Libraries)

**Companion to:** GenAI_Topic10_MCP.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry
**Package used:** `pip install "mcp==1.9.4"` — pinned since mcp 2.x renamed `FastMCP` to `MCPServer` with API changes.

---

## `mcp.server.fastmcp.FastMCP` (Server)

**Initialization:**
```python
from mcp.server.fastmcp import FastMCP
mcp_server = FastMCP("Demo")
```

**Top methods/decorators:**
| Method/Decorator | Explanation |
|---|---|
| `@mcp_server.tool()` | Registers a function as a callable tool — docstring becomes the description exposed to clients |
| `@mcp_server.resource("uri://path")` | Registers a function as a readable resource, addressed by URI |
| `@mcp_server.prompt()` | Registers a reusable prompt template |
| `.run(transport="stdio"\|"sse"\|"streamable-http")` | Starts the server under the chosen transport — same tool/resource definitions work under any transport |

**Verified example:**
```python
mcp_server = FastMCP("Demo")

@mcp_server.tool()
def echo(msg: str) -> str:
    """Echoes the message back."""
    return msg

print(mcp_server.name)   # Demo
```

---

## `mcp.client.stdio.stdio_client` + `ClientSession` (Local Subprocess Access)

**Initialization:**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(command="python3", args=["server.py", "stdio"])
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `async with stdio_client(params) as (read, write):` | Spawns the server as a subprocess, opens stdin/stdout communication channels |
| `async with ClientSession(read, write) as session:` | Wraps the raw channels in the actual MCP protocol session |
| `await session.initialize()` | Required handshake before any other calls |
| `await session.list_tools()` | Discover available tools |
| `await session.call_tool(name, args_dict)` | Invoke a tool, returns a result with `.content[0].text` |
| `await session.read_resource(uri)` | Read a resource's content |

**Verified example (real output):**
```python
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("add_numbers", {"a": 5, "b": 7})
        print(result.content[0].text)   # 12
```

---

## `mcp.client.streamable_http.streamablehttp_client` (Hosted/Remote Access)

**Initialization:**
```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

url = "http://127.0.0.1:8000/mcp/"
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `async with streamablehttp_client(url) as (read, write, _):` | Connects to a REMOTE/hosted server over HTTP instead of spawning a subprocess |
| Everything else | Identical `ClientSession` API to the stdio version — same `.initialize()`, `.list_tools()`, `.call_tool()` calls, only the transport differs |

**Verified example (real output, real HTTP round-trip):**
```python
async with streamablehttp_client(url) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("add_numbers", {"a": 20, "b": 22})
        print(result.content[0].text)   # 42
```

---

## Status
3 entries verified with real executed output over both stdio (subprocess) and streamable-http (real network) transports.
