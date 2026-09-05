# GenAI/AI-ML Principles — Topic 10: MCP (Model Context Protocol)

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Everything below is genuinely running MCP protocol traffic — real server process, real subprocess/HTTP communication, real tool calls with correct results. This uses the official `mcp` Python SDK (`pip install "mcp==1.9.4"` — pinned since the newer 2.x SDK renamed `FastMCP` to `MCPServer` and changed several APIs; note this if your environment has a newer version installed).

---

## 1. What Is MCP?

**Model Context Protocol** is a standardized protocol (created by Anthropic, now widely adopted) for connecting LLMs/agents to external tools, data sources, and services — without every AI application needing a custom integration for every tool. It defines a client-server architecture:

- **MCP Server** — exposes **tools** (callable functions), **resources** (readable data), and **prompts** (reusable templates) to any compatible client.
- **MCP Client** — connects to one or more servers, discovers what they offer, and calls their tools/reads their resources on behalf of an LLM/agent.
- **Transport** — the communication channel between client and server: `stdio` (local subprocess), or HTTP-based (`streamable-http` or the older `sse`) for remote/hosted servers.

This directly relates to your existing n8n automation and agentic AI work — MCP is essentially a standardized alternative to building custom tool-calling integrations for every agent framework separately.

---

## 2. How to Create an MCP Server — Real, Verified Code

```python
from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP("DemoToolsServer")

@mcp_server.tool()
def add_numbers(a: int, b: int) -> int:
    """Adds two numbers together."""
    return a + b

@mcp_server.tool()
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)

@mcp_server.resource("config://greeting")
def get_greeting() -> str:
    """A simple static resource."""
    return "Hello from the DemoToolsServer MCP resource!"

if __name__ == "__main__":
    import sys
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if transport == "stdio":
        mcp_server.run(transport="stdio")
    elif transport == "sse":
        mcp_server.run(transport="sse")
    elif transport == "streamable-http":
        mcp_server.run(transport="streamable-http")
```
**Key points, directly relevant to MCQ questions:**
- `@mcp_server.tool()` — the decorator that registers a function as a callable tool, same pattern as LangChain's `@tool` from Topic 6, but this is a separate, transport-agnostic protocol, not tied to any one agent framework.
- The docstring becomes the tool's description exposed to clients — same principle as Topic 6's `@tool` decorator.
- `@mcp_server.resource("config://greeting")` — resources use a URI scheme, distinguishing them from tools (which are actions) — resources are meant for readable data/context.
- The same server object (`mcp_server`) can run under any transport — the tool/resource definitions don't change based on how it's hosted.

---

## 3. How to Host the MCP — stdio (Local Subprocess) — Real, Verified

The simplest hosting pattern: the client spawns the server as a subprocess and communicates over stdin/stdout. No network involved at all — genuinely local process-to-process communication.

**Client code (real, executed):**
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_demo_server.py", "stdio"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            result = await session.call_tool("add_numbers", {"a": 5, "b": 7})
            print("add_numbers(5, 7) =", result.content[0].text)

            result2 = await session.call_tool("get_word_length", {"word": "hallucination"})
            print("get_word_length('hallucination') =", result2.content[0].text)

asyncio.run(main())
```
Actual output when run:
```
Available tools: ['add_numbers', 'get_word_length']
add_numbers(5, 7) = 12
get_word_length('hallucination') = 13
```
The client literally launched the server script as a child process, spoke the MCP protocol over its stdin/stdout, listed the real registered tools, and got correct computed results back — genuine end-to-end protocol traffic, not a simulation.

---

## 4. How to Host the MCP — HTTP (Real Remote/Network Pattern) — Real, Verified

This is what "hosting" actually means in production — the server runs independently (e.g., on a cloud VM, container, or serverless endpoint) and clients connect over the network, potentially from anywhere, not just as a spawned local subprocess.

**Starting the server with HTTP transport:**
```bash
python3 mcp_demo_server.py streamable-http
```
Real server startup log:
```
INFO:     Started server process [622]
INFO:     Waiting for application startup.
INFO     StreamableHTTP session manager started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
It's running on `uvicorn` under the hood — the same production ASGI server your FastAPI projects already use.

**Client code connecting over HTTP (real, executed):**
```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    url = "http://127.0.0.1:8000/mcp/"
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools (via HTTP):", [t.name for t in tools.tools])

            result = await session.call_tool("add_numbers", {"a": 20, "b": 22})
            print("add_numbers(20, 22) via HTTP =", result.content[0].text)

            result2 = await session.call_tool("get_word_length", {"word": "orchestration"})
            print("get_word_length('orchestration') via HTTP =", result2.content[0].text)

asyncio.run(main())
```
Actual output when run:
```
Available tools (via HTTP): ['add_numbers', 'get_word_length']
add_numbers(20, 22) via HTTP = 42
get_word_length('orchestration') via HTTP = 13
```
Real server access log confirming actual HTTP round-trips (not mocked):
```
INFO:     127.0.0.1:49762 - "POST /mcp/ HTTP/1.1" 200 OK
INFO:     127.0.0.1:49792 - "POST /mcp/ HTTP/1.1" 200 OK   <- initialize
INFO:     127.0.0.1:49794 - "POST /mcp/ HTTP/1.1" 200 OK   <- list_tools
INFO:     127.0.0.1:49800 - "POST /mcp/ HTTP/1.1" 200 OK   <- call_tool
INFO:     127.0.0.1:49804 - "DELETE /mcp/ HTTP/1.1" 200 OK <- session cleanup
```

**For actual production hosting** (deploying this so it's reachable from outside `127.0.0.1`), the pattern is exactly what you already use in your Media Studio deployment (Nginx reverse proxy + systemd service):
```bash
# systemd service running the server on 0.0.0.0 instead of localhost-only
# then Nginx reverse-proxies a public domain to it, same pattern as your VPS deployment runbook
uvicorn mcp_demo_server:mcp_server.streamable_http_app --host 0.0.0.0 --port 8000
```

---

## 5. How to Access a Hosted MCP — Client Access Patterns

**From Python (as shown above)** — use `mcp.client.stdio.stdio_client` for local subprocess servers, or `mcp.client.streamable_http.streamablehttp_client` for remote/hosted servers, both wrapped in `ClientSession`.

**From an agent framework (conceptual — connects to Topic 6's LangGraph work):** modern agent frameworks increasingly support MCP servers as a tool source directly, meaning a LangGraph agent could discover and call tools from any MCP server without you writing custom `@tool`-decorated wrapper functions for each one — the MCP server's tool definitions are used directly.

**Authentication for hosted servers (reference — not demonstrated here since the demo server has none):** production MCP servers exposed over the internet typically require auth — the SDK supports `TokenVerifier`/OAuth provider hooks (visible in the `MCPServer.__init__` signature) for validating bearer tokens or OAuth flows before allowing tool calls, the same concern as securing any REST API.

---

## 6. Traps & Misconceptions (MCQ-Relevant)

1. **"MCP is tied to a specific agent framework like LangChain"** — FALSE. MCP is a transport-and-protocol-level standard, independent of any specific agent framework — that's precisely its value proposition (write the tool once, any MCP-compatible client can use it).
2. **"stdio transport means the server runs somewhere remote"** — FALSE, backwards. `stdio` is specifically for local subprocess communication; HTTP-based transports (`streamable-http`, `sse`) are for remote/hosted access.
3. **"A tool's docstring is optional metadata"** — FALSE, same principle as Topic 6 — it's the actual description exposed to clients/LLMs deciding whether to call that tool.
4. **"Resources and tools are the same concept with different names"** — FALSE. Tools represent actions/callable functions; resources represent readable data, addressed by URI — a deliberate distinction in the protocol design.
5. **"You can't change how an MCP server is hosted after writing it"** — FALSE, as demonstrated above — the exact same `mcp_server` object with the exact same tool definitions ran under both `stdio` and `streamable-http` transports just by changing the `.run(transport=...)` argument.

---

## 7. Rapid-Fire Self-Check (MCQ Simulation)

1. What are the three main things an MCP server can expose to a client? *(Tools, resources, and prompts)*
2. What's the key difference between stdio and HTTP-based transports in MCP? *(stdio is for local subprocess communication; HTTP-based transports like streamable-http are for remote/networked, hosted access)*
3. Does changing an MCP server's transport require rewriting its tool definitions? *(No — the same server object and tool/resource definitions can run under different transports just by changing the run configuration)*
4. What server framework runs under the hood when hosting an MCP server via `streamable-http`? *(Uvicorn, an ASGI server — the same one used for FastAPI applications)*
5. Why does MCP's standardization matter for agentic AI systems? *(It decouples tool implementation from any specific agent framework — a tool written once as an MCP server can be used by any MCP-compatible client, avoiding framework-specific custom integrations)*

---

## 8. Official & Community MCP Server Directories

**The official reference repository:** `github.com/modelcontextprotocol/servers` — managed by Anthropic and built together with the community, it's the home of a small set of official reference implementations demonstrating MCP features: **Everything** (test server with prompts/resources/tools), **Fetch**, **Filesystem**, **Git**, **Memory** (knowledge-graph persistent memory), **Sequential Thinking**, and **Time**. This is the repo your bash server/client demo above matches in structure.

**The official MCP Registry — the actual current answer to "where do companies list their MCP servers":** `registry.modelcontextprotocol.io`. The `servers` repo's own README now points here as the authoritative place to browse published servers, rather than maintaining a giant company-by-company list directly in the repo itself — the ecosystem has grown large enough that a proper registry replaced a flat README list.

**Company-maintained servers that graduated out of the reference repo into their own official repos** (a good pattern to know about, since it shows how MCP servers evolve from reference examples into production integrations):
- Brave Search → now maintained directly by Brave at `github.com/brave/brave-search-mcp-server`
- Slack → now maintained by Zencoder at `github.com/zencoderai/slack-mcp-server`
- Several others (GitHub, GitLab, Google Drive, Google Maps, PostgreSQL, Puppeteer, Redis, Sentry, SQLite, AWS KB Retrieval, EverArt) were archived from the main repo and live on at `github.com/modelcontextprotocol/servers-archived` for historical reference.

**Official SDKs** (also under the `modelcontextprotocol` GitHub organization) exist for C#, Go, Java, Kotlin, PHP, Python, Ruby, Rust, Swift, and TypeScript — the Python SDK (`mcp` on PyPI) is what every example in this document uses.

**A popular community-curated (not official) directory worth knowing about:** `github.com/wong2/awesome-mcp-servers` — categorizes servers into Official, Reference, and Sponsor sections covering cloud infrastructure, databases, dev tools, and web automation from many different companies. Useful for discovery, but it's a community list, not an Anthropic-maintained one — worth distinguishing the two in conversation or an interview answer.

**Official documentation:** `modelcontextprotocol.io` — the canonical source for protocol specs, SDK guides, and the "Example Servers" page linking to all of the above.

---

## Status
Every server, client, and transport (stdio and streamable-http) in this document is real, executed code with genuine correct output and real protocol/network logs shown — not simulated. The one thing not demonstrated is public internet-facing hosting (deliberately, since exposing a port to the internet from this sandbox isn't appropriate), but the exact deployment pattern (systemd + Nginx reverse proxy) matches your already-documented Media Studio production deployment.

Ready for the companion **Cheatsheet — Topic 10**, or straight into **Topic 11: Transformers** whenever you want to continue.
