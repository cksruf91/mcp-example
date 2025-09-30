# MCP Tool Servers

FastMCP-based tool servers that expose functions as MCP tools over HTTP. These servers provide tools that can be discovered and invoked by MCP clients.

## Overview

This directory contains example MCP servers demonstrating how to expose Python functions as MCP tools:
- **Alpha Server** (`alpha.py`) - User information tools
- **Beta Server** (`beta.py`) - Price calculation tools

## Prerequisites

- Python 3.12.3+
- `fastmcp` package installed

## Running the Servers

Each server must run on a separate port. Start them from the `core/server/` directory:

```bash
# Alpha server - User information tools
fastmcp run alpha.py --transport http --port 9011

# Beta server - Price calculation tools
fastmcp run beta.py --transport http --port 9012
```

The servers will expose their MCP endpoints at:
- Alpha: `http://localhost:9011/mcp`
- Beta: `http://localhost:9012/mcp`

## Available Tools

### Alpha Server (port 9011)

#### `get_user_name`
Retrieves a user's name by user ID.

**Parameters:**
- `user_id` (str): The ID of the user

**Example:**
```python
get_user_name(user_id="M4386")
# Returns: "kimi raikkonen"
```

#### `get_user_address`
Retrieves a user's address by user ID.

**Parameters:**
- `user_id` (str): The ID of the user

**Example:**
```python
get_user_address(user_id="M4386")
# Returns: "12 Av. des Spélugues, 98000 Monaco,"
```

### Beta Server (port 9012)

#### `get_final_price`
Calculates the final price including an 18% tip.

**Parameters:**
- `a` (float): The base price amount

**Example:**
```python
get_final_price(a=100.0)
# Returns: "118.0$"
```

## Creating New Tools

To add a new tool to a server:

```python
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult, TextContent

mcp = FastMCP(
    name="Your Server Name",
    instructions="Description of your server"
)

@mcp.tool(
    tags={'your_tag'},
    meta={'author': 'your_name'},
    enabled=True
)
async def your_tool_name(param1: str, ctx: Context = None) -> ToolResult:
    """
    Clear description of what your tool does.

    Args:
        param1 (str): Description of parameter
        ctx: internal use only, ignore this parameter

    Returns:
        ToolResult: Result object with content and structured data
    """
    # Log tool invocation
    await ctx.info('your_tool_name invoked')

    # Your tool logic here
    result = f"processed {param1}"

    # Return structured result
    return ToolResult(
        content=TextContent(type="text", text=result),
        structured_content={"result": result}
    )

if __name__ == "__main__":
    mcp.run()
```

## Tool Metadata

Each tool can include:
- **tags**: For categorizing and filtering tools (e.g., `{'alpha'}`, `{'beta'}`)
- **meta**: Additional metadata like author information
- **enabled**: Whether the tool is available (default: `True`)

## Context Logging

The `Context` parameter provides logging capabilities:
```python
await ctx.info('Information message')
await ctx.warn('Warning message')
await ctx.error('Error message')
```

Logs are visible in the server console when tools are invoked.

## Testing Tools

You can test tools locally before integrating with a client:

```bash
# Start the server
fastmcp run alpha.py --transport http --port 9011

# Use curl or your MCP client to invoke tools
curl http://localhost:9011/mcp
```

## Integration with Client

To connect these servers to the MCP client, update `core/client/common/service.py`:

```python
config = {
    "mcpServers": {
        "alpha": {
            "url": "http://localhost:9011/mcp"
        },
        "beta": {
            "url": "http://localhost:9012/mcp"
        }
    }
}
```