from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult, TextContent

mcp = FastMCP(
    name="MCP server Beta 🚀",
    instructions="""
        This server provides price calculation services with tips included.
    """,
)

@mcp.tool(
    tags={'beta'},
    meta={'author': 'anonymous'},
    enabled=True
)
async def get_final_price(a: float, ctx: Context = None) -> ToolResult:
    """
    Calculates the final price including tips.

    This function takes a base price and applies a 18% tip ratio to
    calculate the final price including tips.

    Args:
        a (float): The base price amount
        ctx: internal use only, ignore this parameter

    Returns:
        ToolResult: Result object containing:
            - Text content with the final price amount
            - Structured content with the final price result
    """
    tip_ratio = 1.18
    a *= tip_ratio
    await ctx.info('get_final_price tool invoked')
    return ToolResult(
        content=TextContent(type="text", text=f"{a}$"),
        structured_content={"result": a}
    )

if __name__ == "__main__":
    mcp.run()
