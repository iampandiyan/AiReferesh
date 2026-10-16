"""Exercise 1: identify the MCP host, client, and server roles."""

ROLES = {
    "Claude Desktop": (
        "host",
        "Owns the UI and conversation and embeds MCP clients.",
    ),
    "Filesystem reference server": (
        "server",
        "Advertises filesystem tools and resources to clients.",
    ),
    "Cursor MCP integration": (
        "host",
        "The IDE host manages clients for its connected MCP servers.",
    ),
    "AcmeCorp CRM service": (
        "server",
        "Advertises CRM operations such as lookup_customer.",
    ),
    "Python script using ClientSession": (
        "client",
        "Manages a connection to a server; it can run without a host UI.",
    ),
    "GitHub official MCP server": (
        "server",
        "Exposes GitHub capabilities to connected clients.",
    ),
}


def main() -> None:
    for system, (role, reason) in ROLES.items():
        print(f"{role:7} | {system}: {reason}")


if __name__ == "__main__":
    main()

"""
host    | Claude Desktop: Owns the UI and conversation and embeds MCP clients.
server  | Filesystem reference server: Advertises filesystem tools and resources to clients.
host    | Cursor MCP integration: The IDE host manages clients for its connected MCP servers.
server  | AcmeCorp CRM service: Advertises CRM operations such as lookup_customer.
client  | Python script using ClientSession: Manages a connection to a server; it can run without a host UI.
server  | GitHub official MCP server: Exposes GitHub capabilities to connected clients.

"""
