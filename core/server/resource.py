from fastmcp import FastMCP

mcp = FastMCP(
    name="MCP server Resource 🚀",
    instructions="""
        This server provides resource
    """,
)


@mcp.resource(
    uri="data://app-status",  # Explicit URI (required)
    name="ApplicationStatus",  # Custom name
    description="Provides the current status of the application.",  # Custom description
    mime_type="application/json",  # Explicit MIME type
    tags={"alpha", "beta"},  # Categorization tags
    meta={"version": "2.1", "team": "infrastructure"}  # Custom metadata
)
async def get_application_status() -> dict:
    """ Currently not in use anywhere """
    return {"status": "ok", "uptime": 12345, "name": mcp.name}  # Example usage
