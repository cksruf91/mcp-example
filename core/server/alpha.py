from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult, TextContent

mcp = FastMCP(
    name="MCP server Alpha 🚀",
    instructions="""
        This server provide simple math functions
    """,
)


@mcp.tool(
    name='add',
    tags={'alpha'},
    meta={'author': 'anonymous'},
    enabled=True
)
async def add(a: float, b: float, ctx: Context = None) -> ToolResult:
    """
    Adds two numbers and returns the result.

    This function takes two numeric arguments (integers or floats) and calculates their sum.
    It handles both integer and float inputs and returns the sum along with a text representation
    of the calculation.

    Args:
        a (Union[int, float]): First number to add
        b (Union[int, float]): Second number to add
        ctx : internal use only, ignore this parameter

    Returns:
        ToolResult: Result object containing:
            - Text content showing the calculation
            - Structured content with the numeric result
    """
    await ctx.info('get_user_name tool invoked')
    return ToolResult(
        content=TextContent(type="text", text=f"{a} + {b} = {a + b}"),
        structured_content={"result": a + b}
    )


@mcp.tool(
    tags={'alpha'},
    meta={'author': 'anonymous'},
    enabled=True
)
async def get_user_name(user_id: str, ctx: Context = None) -> ToolResult:
    """
    Retrieves a user's name based on their user ID.

    This function takes a user ID string and returns the corresponding user name
    from a predefined mapping. If the user ID is not found, returns None.

    Args:
        user_id (str): The ID of the user to look up
        ctx : internal use only, ignore this parameter

    Returns:
        ToolResult: Result object containing:
            - Text content with the user's name
            - Structured content with the name result
    """
    await ctx.info(f'{__name__} tool invoked')
    nams_space = {
        'M4386': 'kimi raikkonen'
    }
    user_name = nams_space.get(user_id)
    await ctx.info(f'{__name__} return value [{user_name}]')
    return ToolResult(
        content=TextContent(type="text", text=user_name),
        structured_content={"result": user_name}
    )


@mcp.tool(
    tags={'alpha'},
    meta={'author': 'anonymous'},
    enabled=True
)
async def get_user_address(user_id: str, ctx: Context = None) -> ToolResult:
    """
    Retrieves a user's address based on their user ID.

    This function takes a user ID string and returns the corresponding address
    from a predefined mapping. If the user ID is not found, returns None.

    Args:
        user_id (str): The ID of the user to look up
        ctx : internal use only, ignore this parameter

    Returns:
        ToolResult: Result object containing:
            - Text content with the user's address
            - Structured content with the address result
    """
    await ctx.info(f'{__name__} tool invoked')
    nams_space = {
        'M33': '12 Av. des Spélugues, 98000 Monaco,'
    }
    user_address = nams_space.get(user_id)
    await ctx.info(f'{__name__} return value [{user_address}]')
    return ToolResult(
        content=TextContent(type="text", text=user_address),
        structured_content={"result": user_address}
    )


if __name__ == "__main__":
    mcp.run()
