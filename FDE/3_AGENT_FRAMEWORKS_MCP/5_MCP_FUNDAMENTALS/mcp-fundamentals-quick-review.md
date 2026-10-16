# MCP Fundamentals: Quick Review (Lesson 5.5)

**One-line summary:** MCP (Model Context Protocol) is an open, vendor-neutral standard for how an AI app connects to tools and data. Think of it as **"USB-C for AI assistants."**

**Memory hook:** 3 roles, 3 primitives, 3 transports, 3 auth patterns, 4 threats.

---

## 1. Big Picture

- **Problem before MCP:** every host (ChatGPT, Claude, Cursor) had its own tool format, so N hosts x M tools meant N x M work.
- **With MCP:** one server speaks MCP and every compliant host can use it, so the work is N + M.
- **Where the USB-C analogy breaks:**
  - MCP is a protocol on top of stdio or HTTP, not a physical spec.
  - Servers advertise their catalog on connect.
  - MCP has 3 transports, not one.
- **Governance:** reportedly donated to the Linux Foundation's Agentic AI Foundation in Dec 2025. It is vendor-neutral, not "Anthropic's protocol."
- **Wire format:** JSON-RPC 2.0, the same stable format used since 2010. MCP only adds a new vocabulary on top.
- **LSP link:** MCP is "LSP for AI assistants." Editor : LSP server :: Claude Desktop : MCP server.

---

## 2. The Three Roles (Host / Client / Server)

| Role | What it is | Examples |
|---|---|---|
| **Host** | The LLM app the human uses. Owns UI, conversation and permissions. | Claude Desktop, Cursor, VS Code Copilot, ChatGPT desktop |
| **Client** | A per-server connection manager inside the host (1 client per server). | 5 servers = 5 clients |
| **Server** | An out-of-process program that exposes tools, resources and prompts. | AcmeCorp CRM, filesystem server, GitHub MCP server |

- **Why a separate client?** It is the policy boundary. It decides whether to forward a call, handles auth and multiplexes many servers.
- **MCP is a process boundary, not a function-call boundary.** Servers can be written in any language and swapped freely.

### Common mistake: function calling is not MCP
- Hard-coding one tool into `client.messages.create(..., tools=[...])` is **function calling**.
- Real MCP needs all of these:
  - JSON-RPC wire protocol
  - Capability discovery
  - Out-of-process server
  - Host / client / server separation

### Why MCP and not function calling or REST?

| Dimension | Function calling | OpenAPI / REST | MCP |
|---|---|---|---|
| Dynamic discovery | No (hard-coded) | Only if you parse the doc | **Yes** |
| Server-to-client calls | No | No | **Yes** (sampling, elicitation) |
| Portable catalog | Differs per vendor | Per API | **One neutral catalog** |
| Transport standard | Vendor SDK | HTTP only | **stdio + streamable HTTP** |

**Takeaway:** OpenAPI is a fine way to *implement* a tool. MCP is how a host *discovers and negotiates* it.

### Config example (Claude Desktop)
`claude_desktop_config.json` tells the host which servers to spawn:
```json
{
  "mcpServers": {
    "acmecorp-crm": { "command": "python", "args": ["-m", "acmecorp_crm"] },
    "filesystem": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/projects"] }
  }
}
```
On launch the host forks each subprocess, opens a stdio client per server and discovers each catalog.

---

## 3. Stateless Core and Spec History (2026-07-28)

- **Old way (2024-11 to 2025-03):** a stateful `initialize` handshake came first, then you could list anything.
- **New way (2026-07-28):** the handshake is removed. MCP is **stateless**, so any request can hit any server instance, which means easy horizontal scaling behind a load balancer.
- **Still exists:** per-request version and capability negotiation. It now rides on each request (in `_meta`, or via a stateless `server/discover` call). The SDK hides this, so your code still looks like it "connects once."

### Key JSON-RPC methods

| Method | Purpose |
|---|---|
| `server/discover` | Stateless discovery and version/capability negotiation (replaces `initialize`) |
| `tools/list` | Get the tool catalog |
| `tools/call` | Run a tool |
| `resources/list` | Get the resource catalog |
| `resources/read` | Read a resource by URI |
| `prompts/list` | Get the prompt catalog |
| `subscriptions/listen` | Client opens a stream that carries catalog-change notifications |

### Spec revisions (dated, not semver)
`2024-11-05` (launch) → `2025-03-26` (streamable HTTP replaces HTTP+SSE) → `2025-06-18` (structured tool output, elicitation) → `2025-11-25` → `2026-07-28` (stateless core)

### New in 2026-07-28
- **Stateless core:** no `initialize`, and it scales like normal HTTP.
- **Extensions framework:**
  - *Tasks:* long-running async work.
  - *MCP Apps:* servers ship interactive UI into the host.
  - *Enterprise Managed Authorization:* org-admin control of server access.
- **Hardened auth:** adds RFC 9207 (issuer identification) and Client ID Metadata Documents, so no manual pre-registration is needed.
- **HTTP+SSE** is formally under the deprecation policy, with a removal window of at least 12 months.

---

## 4. The Three Primitives (What a Server Exposes)

| Primitive | Who triggers it | What it is | Example |
|---|---|---|---|
| **Tool** | The **model** decides | A function with a JSON Schema input and a result | `lookup_customer(customer_id)` |
| **Resource** | The **host/user** attaches it | Read-only, URI-addressed context | `acmecorp://customers/c_4823/history` |
| **Prompt** | The **user** picks it by name | A parameterized template (shows as a slash-command) | `/triage-template ticket_id=T9201` |

- **Tools:** use them when the model should choose when to call. The tradeoff is that they burn tokens (schema plus call plus response).
- **Resources:** use them for static or user-curated context. There is no tool-call round-trip, but the model cannot fetch one on its own.
- **Prompts:** use them for repeatable user workflows, so the *user* starts the workflow rather than the model.
- **Restaurant analogy:** tools are the chef's recommendations, resources are the printed menu, prompts are the prix-fixe specials.
- **Anti-pattern:** making history and triage into tools too. It works, but it wastes tokens and puts the decision in the wrong hands.

### FastMCP shape (all three in one server)
```python
from fastmcp import FastMCP
server = FastMCP("acmecorp-crm")

@server.tool()
def lookup_customer(customer_id: str) -> dict: ...

@server.resource("acmecorp://customers/{cid}/history")
def customer_history(cid: str) -> str: ...

@server.prompt()
def triage_template(ticket_id: str) -> str: ...
```
FastMCP 3.x (stable v3.4.7) is the ergonomic wrapper used in the course.

### The 3 client / interaction primitives (host to server direction)

| Primitive | What it does |
|---|---|
| **Sampling** | Server asks the host to run an LLM completion. The server needs no API key and the host controls cost. |
| **Roots** | Host declares which filesystem/URI areas the server may touch (a scoping boundary). |
| **Elicitation** | Server asks the host to prompt the user for structured input mid-call (added in 2025-06-18). |

These are why MCP is **bidirectional** while function calling is one-way.

---

## 5. The Three Transports

| Transport | Status | Use when | Tradeoffs |
|---|---|---|---|
| **stdio** | Stable, core | Local, same machine, trusted binary | Single-host. 50-200 ms cold start. Dies with the host. (Claude Desktop, Goose) |
| **HTTP+SSE** | **Deprecated** (since 2025-03-26) | Backward compatibility only | Two endpoints, no resumability, stateful streams break behind load balancers |
| **Streamable HTTP** | **Current remote default** | Remote SaaS, horizontal scale, CDN/gateway in front | Network latency and auth complexity |

### Streamable HTTP details
- It uses a **single endpoint**, with normal request/response for short calls and streaming for long ones.
- The 2026-07-28 revision removed protocol sessions: **no `Mcp-Session-Id`, no `Last-Event-ID` replay.**
- If a stream drops, the client **re-issues the request** with a new request id.
- Cross-call state must be explicit, as a server-minted handle passed as a normal tool argument (SEP-2567).
- Users include the Claude.ai registry, OpenAI Responses MCP, the Cloudflare MCP gateway and FastMCP 3.x.

**Decision rule:**
- Needs to scale beyond one host? Use **streamable HTTP**.
- Local only? Use **stdio**.
- SSE-only for a new server? **Wrong answer in 2026.**

---

## 6. Auth Patterns

The spec is auth-agnostic. For stdio it is moot (the server runs as the user). For remote servers it matters.

| Pattern | When to use | Cost | Verdict |
|---|---|---|---|
| **OAuth 2.1 + PKCE** | SaaS with per-user accounts (Slack, GitHub, Salesforce) | High | **Spec-preferred; default for public-facing servers.** Per-user, revocable, no shared secret. PKCE blocks auth-code interception. |
| **API key (Bearer header)** | Internal / service-to-service | Low | Fine for v0, but plan for rotation. **Never put the key in the URL query string** (it leaks into logs and proxies). |
| **mTLS** | Zero-trust enterprise (Glean / Hebbia / Palantir-style) | Very high | Strongest option. Both sides present certificates and there are no long-lived shared secrets. Usually paired with Istio or Cloudflare Access. |

- **Hotel analogy:** an API key is one shared keycard, OAuth is a per-guest keycard, and mTLS is a biometric lock.
- **Gotcha:** a remote MCP server with **no auth** is the #1 rookie mistake. "It's internal" is not a security posture, so at minimum use a Bearer check before the JSON-RPC dispatcher.

---

## 7. Four MCP-Specific Threats

**Core idea:** in MCP the server is **untrusted content**, not just a function you called.

| Threat | What happens | Mitigation |
|---|---|---|
| **Confused deputy** | A server reuses a token minted for one client to act for another. | Bind tokens to one client/audience. Never share an upstream credential. Validate the audience on every call. |
| **Token passthrough** | A server forwards the caller's token downstream, making it an open relay. | Exchange the inbound token for the server's own scoped-down credential. |
| **Tool poisoning / prompt injection** | Malicious instructions are hidden in a tool description or result. | Treat descriptions and results as untrusted. Keep a human in the loop for destructive tools. Pin servers to vetted sources. |
| **Rug pull** | A server changes tool behavior after the user has approved it. | Pin versions/hashes. Re-prompt for consent when the catalog changes. Use registries that attest identity. |

---

## 8. Quick-Check Answers

| Q | Answer | Why |
|---|---|---|
| Q1: "I added MCP" with one hard-coded tool in `messages.create` | **No** | That is function calling. It has no server and no wire protocol. |
| Q2: Pre-attach the last 50 tickets, no model decision | **Resource** | The host attaches it up front, with no tool-call round-trip. |
| Q3: 200 employees via Claude.ai web | **Streamable HTTP** | Remote default; scales; CDN-fronted. SSE is deprecated and stdio is local-only. |
| Q4: Zero-trust, no shared secrets | **mTLS** | The TLS handshake authenticates the caller. |
| Q5: MCP : function calling :: ? | **LSP** | An open, vendor-neutral protocol generalizing a single-vendor capability. |

---

## 9. Practice Exercises (Overview)

- **Easy:** label host / client / server for 6 named systems; connect to a stdio server, then list, call and print.
- **Medium:**
  - Hand-trace the JSON-RPC envelopes.
  - Pick tool / resource / prompt for 5 AcmeCorp capabilities.
  - Match sampling / roots / elicitation to scenarios.
  - Extend the consumer with `list_open_tickets(customer_id)`.
- **Hard:**
  - Harden a remote server against the 4 threats.
  - Write a transport decision memo/matrix (stdio vs SSE vs streamable HTTP).
  - Build an auth decision matrix for 3 customer profiles.

---

## 10. 60-Second Cheat Sheet

- **MCP** = open JSON-RPC protocol between hosts and tool servers (N + M instead of N x M).
- **Roles:** Host (UI and permissions) → Client (1 per server, policy boundary) → Server (out-of-process).
- **Server primitives:** Tools (model-invoked), Resources (host-attached), Prompts (user-invoked).
- **Client primitives:** Sampling, Roots, Elicitation.
- **Transports:** stdio (local), streamable HTTP (remote default), HTTP+SSE (deprecated).
- **2026-07-28:** stateless core, with no `initialize` and no protocol sessions. It adds Tasks, MCP Apps and Enterprise Managed Authorization.
- **Auth:** OAuth 2.1 + PKCE (default), API key (internal), mTLS (zero-trust).
- **Threats:** confused deputy, token passthrough, tool poisoning, rug pull.
