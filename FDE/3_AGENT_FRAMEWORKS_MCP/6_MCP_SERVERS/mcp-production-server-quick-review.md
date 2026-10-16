# Building Production MCP Servers in Python: Quick Review (Lesson 5.6)

**One-line summary:** Build an MCP server with **FastMCP 3.x** that exposes tools, a resource and a prompt, **returns structured errors instead of raising**, is tested with an **in-memory client**, and ships over **stdio (local)** and **streamable HTTP (remote)**.

**Memory hook:** FastMCP by default → good schemas → never raise → version it → package once, run anywhere.

---

## 1. Why MCP Servers Matter (the FDE-defining artifact)

- **Before:** agent tools lived inside the agent's process (Agents SDK, LangGraph, etc.).
- **Now:** an MCP server is a **separate process or HTTP service**. Any MCP host can use it with zero changes (Claude Desktop, Cursor, Cody, Goose, Agents SDK, Continue, Zed).
- **Why it's the "climax":** an FDE ships the customer's existing CRM, ticketing and billing stack, addressable by whichever agent the customer picks. You are not locked to one framework or model vendor.
- **This lesson builds:** the AcmeCorp CRM server, which is deliverable #1 of the M5 mini-capstone (a GitHub repo).
- **Analogy:** MCP is USB-C for agents. It carries only data (not power) and is governed by the Linux Foundation's Agentic AI Foundation.
- **Lesson ties:**
  - Pydantic v2 (L2.3) → tool schemas
  - pytest (L2.4) → in-memory client tests
  - Packaging (L2.6) → console_scripts wheel
  - Extended later in M7 (OAuth SaaS) and M11 (capstone)

---

## 2. FastMCP 3.x vs Raw MCP SDK

| Dimension | FastMCP 3.x | Raw MCP SDK |
|---|---|---|
| Tool definition | `@mcp.tool()` + type hints | Register handler + write JSON Schema |
| Schema generation | Auto (Pydantic + docstring) | Hand-written |
| Streamable HTTP | Built-in, default for remote | Manual wiring |
| OAuth | FastAPI-middleware compatible | DIY |
| In-memory test client | `Client(server)`, no socket | Subprocess + stdio |
| Customisation ceiling | High but bounded | **Full protocol surface** |
| Dependencies | Heavier | **Minimal** |

- **Rule:** use FastMCP ~95% of the time. Drop to the raw SDK only for custom transports or deep JSON-RPC customisation, or when the dependency tree is too heavy.
- **Analogy:** FastMCP : MCP :: FastAPI : ASGI, and raw SDK : MCP :: Starlette : ASGI.
- **Heuristic:** if escaping the decorators takes more than ~30 lines, the server is probably designed wrong.
- **Q1 answer:** FastMCP. It has streamable HTTP by default and OAuth middleware compatibility.

---

## 3. Tool Decorators and Schemas (the LLM must pick right the first time)

FastMCP reads **3 things** to build the schema the LLM sees:

| Source | Becomes |
|---|---|
| **Function name** | Tool name |
| **Docstring** | Tool description (**this is the prompt the LLM reads to choose the tool**) |
| **Type hints** | `inputSchema` |

- **No docstring and no hints** means an empty description and a wide-open schema, so the LLM mis-picks tools.
- **Fix mis-routing** by improving docstrings ("use this when X, not when Y"), not by changing the model. This fixes about 80% of cases.
- Use `str, Enum` types (e.g. `OrderStatus`) so the LLM sees the allowed values.
- Use `Annotated[int, Field(ge=1, le=100)]` to put bounds into the schema.

```python
mcp = FastMCP(name="acmecorp-crm")

@mcp.tool()
def get_customer(customer_id: str) -> dict:
    """Look up a customer by ID."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return {"error": True, "code": "CUSTOMER_NOT_FOUND", "customer_id": customer_id}
    return customer.model_dump(mode="json")

if __name__ == "__main__":
    mcp.run()   # stdio is the default
```

### The three primitives in this server

| Primitive | Decorator | Shape | AcmeCorp example |
|---|---|---|---|
| **Tool** | `@mcp.tool()` | Imperative, may have side effects | `check_refund_eligibility` |
| **Resource** | `@mcp.resource("customer-context://customers/{customer_id}")` | GET-shaped, read-only | Compact context blob (tier, LTV, open tickets, churn risk) |
| **Prompt** | `@mcp.prompt()` | Host-injected template (slash command, e.g. `/escalate`) | `escalation_template(customer_id, issue_summary)` |

- Resources and prompts are why MCP is more than "function calling over a wire."

### The Context object (`ctx: Context`)
Use it when a tool is slow, needs logging, or needs the host's help. It is **opt-in** and does **not** appear in the public schema.

| Helper | Use |
|---|---|
| `await ctx.report_progress(progress, total)` | Drives the host's progress bar |
| `await ctx.info / warning / error(...)` | Structured logs the host can surface |
| `await ctx.sample(...)` | Ask the host to run an LLM completion |
| `await ctx.read_resource(...)` | Read another registered resource |

- **3.x gotcha:** all of these are coroutines, and `ctx.set_state` / `ctx.get_state` are now async too, so `await` them.
- **Q2 answer:** add a docstring and type hints. FastMCP introspects both.

---

## 4. Error Handling: Never Raise Across the Tool Boundary

**Golden rule:** return structured failures, don't raise exceptions.

| Approach | What the agent sees | Result |
|---|---|---|
| **Raise** an exception | JSON-RPC `-32000` **transport error** | Agent aborts: "I encountered an internal error." |
| **Return** a structured result | A normal tool result | Agent reads the reason, explains it, and the conversation continues |

- **The boundary** is tool ↔ agent, not function ↔ caller.
- **Standard shape:** `{"eligible": bool, "reason": str, "policy_version": str, "order_id": str, "error_code": str | None}`
- **Error codes in AcmeCorp:**
  - `CUSTOMER_NOT_FOUND`
  - `ORDER_NOT_FOUND`
  - `WRONG_STATUS`
  - `OUTSIDE_WINDOW` (older than 30 days)
- **Trade-off:** structured returns are more verbose, but continuity wins every time.

### The one exception: input validation
- Bounds like `Field(ge=1, le=100)` go into the JSON Schema, and the protocol layer rejects bad calls **before your handler runs**.
- This returns **`-32602 InvalidParams`**, which is the correct outcome because a malformed call is a contract violation.

| Situation | Correct handling |
|---|---|
| Known business outcome (order not found) | Structured result |
| Malformed request (limit=0) | `-32602` from the protocol layer |
| Uncaught exception in handler | `-32000` (**this is a bug**) |

### Testing the error path (pytest + in-memory client)
```python
async with Client(server) as client:
    result = await client.call_tool("check_refund_eligibility", {"order_id": "o_DOES_NOT_EXIST"})
    assert result.data["error_code"] == "ORDER_NOT_FOUND"
```
- The in-memory client has no subprocess and no socket, so a test takes ~0.05s. A 10-test suite takes ~0.4s, against ~8s for the subprocess equivalent.
- It is also fine on Windows, and fast enough to gate CI on every PR.
- **Q3 answer:** replace `raise` with a structured return that includes `error_code` and `reason`.

---

## 5. Versioning, Discovery and Registry

### Versioning
```python
mcp = FastMCP(name="acmecorp-crm", version="2.1.0", instructions="...")
```

| Change | Bump |
|---|---|
| Add a tool, resource, prompt or **optional** argument | **Minor** (2.0 → 2.1) |
| Remove or rename anything, or make an optional argument required | **Major** (2.x → 3.0) |
| Bug fix, no shape change | **Patch** |

- **Why it matters:** hosts **cache** the tool catalog (Claude Desktop at startup, Cursor per workspace, Agents SDK per session). Changing a shape silently means agents keep calling the old shape and hit `InvalidParams`.
- **Tight vs flexible schemas:** tight schemas give you the schema-as-contract benefit, and they win for customer engagements because compliance teams want explicit version bumps.
- **Q4 answer:** renaming `order_id` to `order_uuid` is a breaking change, so bump to **v2.0**.

### Where customers discover servers

| Registry | Best for |
|---|---|
| `modelcontextprotocol/servers` (GitHub) | Official and broad-utility reference servers (not customer-specific connectors) |
| **Smithery.ai** | Reusable community servers (~5,000, self-publish) |
| **Cloudflare MCP Server Cloud** | Hosted FastMCP with OAuth and auto-scaling (deploy via wrangler) |
| **Customer's internal registry** | Customer-specific servers (SharePoint, Confluence, JSON manifest) |

- **Decision rule:** if the server lives in the customer's repo and runs on their infra, use their internal registry. If it is a reusable connector, use Smithery.

---

## 6. Deployment: One Package, Two Transports

| | stdio | Streamable HTTP |
|---|---|---|
| Use for | Local hosts (Claude Desktop, Cursor, Goose) | Remote, containerized, behind a load balancer |
| Setup | Zero network config | TLS, OAuth, observability |
| Run | `mcp.run()` | `mcp.run(transport="http", host="0.0.0.0", port=8000)` |
| Scaling | One client, one process | Stateless, so any instance serves any request |

- **HTTP+SSE** is deprecated (12-month offramp, sunset ~mid-2027). Ignore SSE tutorials, and don't use `SseServerTransport`.
- **Local recipe:** package a wheel (`console_scripts`), `uv pip install`, then add it to the Claude Desktop config.
- **Remote recipe:** a Docker image with the wheel inside, run with `acmecorp-crm --http`, hosted on Cloudflare (lowest friction for a demo) or customer infra (K8s, ECS, Fly, Render), which wins enterprise procurement reviews.

```toml
[project.scripts]
acmecorp-crm = "acmecorp_crm.server:main"
```
```json
{ "mcpServers": { "acmecorp-crm": { "command": "acmecorp-crm", "args": [] } } }
```
- The same JSON shape works in Cursor (`.cursor/mcp.json`) and Goose. That's **one server, four hosts, zero code changes**.
- **Q5 answer:** one wheel. Engineers use stdio in Claude Desktop, and Kubernetes runs `acmecorp-crm --http` behind a service.

### Remote auth (OAuth 2.1 resource server)
```python
verifier = JWTVerifier(jwks_uri="...", issuer="...", audience="acmecorp-crm-mcp")
secure_mcp = FastMCP(name="acmecorp-crm", auth=verifier)
```
- The auth provider is attached at construction, and the HTTP transport enforces it on **every request**.
- A bad or missing token gets `401` at the transport and never reaches a tool.
- **Tokens are per user**, so the server can scope what each caller sees.
- **No token passthrough:** the server validates the caller's token and uses its **own** downstream credential.
- For a full auth-code + PKCE flow, swap in an OAuth provider (deep dive in M7.6).

### Observability: 4 signals to wire from day one

| Signal | A bad value tells you |
|---|---|
| Per-tool latency (p50 / p95) | A tool past ~1s needs a resource or pagination |
| `error_code` counts by tool | A spike in `ORDER_NOT_FOUND` means the model is guessing IDs, so fix the docstring |
| JSON-RPC `-32000` rate | Any sustained `-32000` is a handler raising, which is a bug |
| `tools/call` volume by tool | A tool never called is dead weight; one that dominates may need splitting |

- **How:** log via `ctx.info/warning/error` (tool name, args, outcome, elapsed time) and export to OpenTelemetry or Langfuse. Module 6 covers the full pipeline.

---

## 7. Production Gotchas

| Gotcha | Fix |
|---|---|
| Mixing SSE tutorials with FastMCP 3.x | Use streamable HTTP only |
| stdio behind a load balancer | stdio is 1:1, so use streamable HTTP for remote |
| OAuth round-trip on every tool call | Keep token caching at session level (10x latency otherwise) |
| Treating the server as a database (`list_all_customers()` with 50k rows) | Use pagination (`limit`/`offset`) or parameterized resource URIs |
| LLM keeps picking the wrong tool | Improve the docstring ("use when X, not Y"), not the model |

---

## 8. Quick-Check Answers

| Q | Answer |
|---|---|
| Q1: Cloudflare Workers + customer OAuth | **FastMCP 3.x** (streamable HTTP default, OAuth-compatible) |
| Q2: No hints or docstring, wrong tool picked | **Add a docstring and type hints** |
| Q3: Agent says "internal error", `-32000` | **Return a structured error instead of raising** |
| Q4: Rename a required parameter | **Major bump (v2.0)** |
| Q5: Local and Kubernetes deployment | **One wheel, stdio locally and `--http` on K8s** |

---

## 9. Practice Exercises (Overview)

- **Easy:** a 30-line baseline `get_customer` server; add `list_orders` with an Enum filter and `limit`.
- **Medium:**
  - `check_refund_eligibility` with structured errors (policy v2.3).
  - A batch tool using `Context` for progress and logs.
  - Add the resource and the prompt.
- **Hard:**
  - Versioning with an additive `tier` filter.
  - Observability middleware that times every `tools/call`.
  - A pytest in-memory suite as a CI gate (8+ tests, under 1s).
  - Package as a wheel + Docker + Claude Desktop config.

---

## 10. 60-Second Cheat Sheet

- **FastMCP 3.x** by default; the raw SDK only for custom transports or protocol-level control.
- **Schema = name + docstring + type hints.** The docstring is the prompt.
- **Three primitives:** tool (action), resource (read state), prompt (user template).
- **Context object** for progress, logs, sampling and resource reads. It is opt-in and async.
- **Never raise across the tool boundary.** Return `{error_code, reason}`. Bad input gets `-32602`, and `-32000` means a bug.
- **Versioning:** additive = minor, breaking = major (rename = major). Hosts cache catalogs.
- **Registries:** GitHub servers repo, Smithery, Cloudflare, or the customer's internal one.
- **Deploy:** one wheel, stdio locally, streamable HTTP remotely, SSE deprecated.
- **Remote auth:** JWT/OAuth 2.1 resource server, per-user tokens, no token passthrough.
- **Observe:** latency, `error_code` counts, `-32000` rate, call volume.
- **Test:** pytest with the in-memory `Client(server)`, ~0.05s per test.
