# MCP Client Server

FastAPI application that acts as an MCP client, aggregating multiple MCP tool servers and enabling LLM-powered tool invocation.

## Overview

This client connects to multiple MCP servers, retrieves their available tools, and orchestrates tool execution through OpenAI's function calling API. It provides a REST API for chatting with tool invocation capabilities.

## Prerequisites

- Python 3.12.3+
- OpenAI API key set as environment variable:
  ```bash
  export OPENAI_API_KEY="your-api-key-here"
  ```
- MCP servers running (see `core/server/README.md`)

## Running the Server

**Important**: Must be run from the `core/client/` directory:

```bash
cd core/client
uvicorn client:main --reload
```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/ping
```

### List Available Tools
```bash
curl http://localhost:8000/tool/list
```
Returns all tools available from connected MCP servers.

### Chat with Tool Invocation
```bash
curl -X POST http://localhost:8000/chat/main \
  -H "Content-Type: application/json" \
  -d '{
    "text": "tell me the name and address for userID M4386",
    "roomId": "optional-room-id"
  }'
```

The LLM will automatically invoke necessary tools to answer the query.

## Architecture

### Service Layer
- `service/chat.py` - Main chat orchestration with tool invocation workflow
- `service/tool.py` - Tool listing from MCP servers

### Routes
- `route/chat.py` - `/chat/main` endpoint
- `route/tool.py` - `/tool/list` endpoint

### Common Components
- `common/service.py` - Base `ServiceClient` with MCP server configuration
- `common/llm/open_ai_provider.py` - OpenAI integration and tool schema conversion
- `common/llm/model.py` - Data models for MCP tools and LLM outputs
- `common/prompt.py` - Prompt management from `resource/prompt.yaml`

### MCP Server Configuration

Modify `common/service.py` to add/remove MCP servers:

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

## How It Works

1. **Tool Discovery**: Client connects to all configured MCP servers and retrieves available tools
2. **LLM Planning**: User message + available tools sent to OpenAI to determine which tools to invoke
3. **Parallel Execution**: Invoked tools executed concurrently using `asyncio.gather()`
4. **Response Generation**: Tool results sent back to LLM for final natural language response

## Data Models

### Request
- `ChattingRequest`: `{ text: str, roomId: str }`

### Response
- `ChatResponse`: `{ chat_id: str, message: str }`
- `ToolListResponse`: `{ tools: list[Tool] }`