# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) example project demonstrating a client-server architecture where:
- **MCP Servers** (`core/server/`) expose tools via FastMCP
- **MCP Client** (`core/client/`) is a FastAPI application that aggregates multiple MCP servers and invokes their tools through OpenAI's function calling

## Development Commands

### Running MCP Servers

MCP servers expose tools that can be called by the client. Run them on separate ports:

```bash
# From core/server/ directory
fastmcp run alpha.py --transport http --port 9011
fastmcp run beta.py --transport http --port 9012
```

**Alpha server** provides user information tools (`get_user_name`, `get_user_address`)
**Beta server** provides price calculation tools (`get_final_price`)

### Running the MCP Client

The client is a FastAPI application that must be run from the `core/client/` directory:

```bash
# From core/client/ directory
uvicorn client:main --reload
```

Client endpoints:
- `GET /ping` - Health check
- `GET /tool/list` - List all available tools from connected MCP servers
- `POST /chat/main` - Send a chat message that can invoke MCP tools (non-streaming)
- `POST /chat/main/stream` - Send a chat message with streaming response

### Environment Setup

Requires `OPENAI_API_KEY` environment variable for LLM provider functionality.

## Architecture

### MCP Server Layer (`core/server/`)

FastMCP servers define tools using the `@mcp.tool()` decorator. Each tool:
- Must have `async` signature
- Accepts `Context` as last parameter for logging
- Returns `ToolResult` with `TextContent` and `structured_content`
- Can be tagged and have metadata for filtering

### MCP Client Layer (`core/client/`)

**Entry point**: `client.py` creates FastAPI app with two routers:
- `route/chat.py` - Chat endpoint
- `route/tool.py` - Tool listing endpoint

**Service layer** (`service/`):
- `ChatService` - Orchestrates LLM + MCP tool invocation workflow
- `ToolListService` - Retrieves available tools from all connected servers

**Key workflows**:

*Complete mode* (`service/chat.py:ChatService.complete()`):
1. Get available tools from all connected MCP servers (with optional tag filtering)
2. Call `OpenAIProvider.invoke_tools()` to let LLM decide which tools to invoke
3. Execute invoked tools in parallel using `asyncio.gather()` with `McpTool.call()`
4. Send tool results back to LLM via `OpenAIProvider.chat_complete()` for final response

*Stream mode* (`service/chat.py:ChatService.stream()`):
1. Same tool discovery and invocation as complete mode
2. Uses `OpenAIProvider.chat_stream()` to yield response chunks asynchronously
3. Returns `AsyncIterable[str]` for server-sent events (SSE) via `StreamingResponse`

**MCP server configuration**: Defined in `common/service.py:CommonService.config` as a dictionary mapping server names to HTTP URLs. The `fastmcp.Client` aggregates multiple MCP servers.

**LLM integration** (`common/llm/`):
- `OpenAIProvider` - Wraps OpenAI API, converts MCP tool schemas to OpenAI function format using `_parsing_tool_schema()`
- `model.py:AvailableTool` - Represents an available MCP tool with tag filtering support
- `model.py:McpTool` - Represents an invoked tool with `call()` method to execute via MCP client using `client.call_tool_mcp()`
- Uses OpenAI's `responses.create()` API with function calling (model: `gpt-5-mini`)

**Prompt management**: `PromptManager` (singleton) loads prompts from `resource/prompt.yaml`

### Data Models

- `models/request.py` - `ChattingRequest` with text and roomId
- `models/response.py` - `ChatResponse`, `ToolListResponse`

## Key Files

- `core/client/common/service.py:10` - MCP server URL configuration in `CommonService.config`
- `core/client/service/chat.py:27` - Main chat workflow orchestration in `ChatService.run()`
- `core/client/service/chat.py:18` - Available tool retrieval with tag filtering
- `core/client/common/llm/open_ai_provider.py:61` - LLM tool invocation logic in `invoke_tools()`
- `core/client/common/llm/open_ai_provider.py:92` - Chat response generation in `chat()`
- `core/client/common/llm/model.py:41` - `McpTool` class definition
- `core/client/common/llm/model.py:47` - MCP tool execution via `McpTool.call()`
- `core/server/alpha.py`, `core/server/beta.py` - Example MCP tool servers

## Dependencies

Core dependencies (in `pyproject.toml`):
- `fastapi[standard]` - Client web framework
- `fastmcp` - MCP protocol implementation
- `openai` - LLM provider
- `numpy` - Data processing

## Instruction
- update CLAUDE.md after modify code