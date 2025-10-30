# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) example project demonstrating a client-server architecture where:
- **MCP Servers** (`core/server/`) expose tools via FastMCP
- **MCP Client** (`core/client/`) is a FastAPI application that aggregates multiple MCP servers and invokes their tools through OpenAI's function calling
- **Frontend App** (`core/client/resource/app/`) is a simple web interface for testing the MCP client functionality

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

The FastAPI server runs on `http://localhost:8000` and serves both the API and frontend application.

Client endpoints:
- `GET /` - Serves the frontend web interface (index.html)
- `GET /ping` - Health check
- `GET /tool/list` - List all available tools from connected MCP servers
- `POST /chat/main/complete` - Send a chat message that can invoke MCP tools (non-streaming)
- `POST /chat/main/stream` - Send a chat message with streaming response
- `POST /pne/complete` - Plan-and-execute workflow for complex multi-step tasks (non-streaming)
- `POST /pne/stream` - Plan-and-execute workflow with streaming response
- `/static/*` - Serves static files from the `core/client/resource/app/` directory (app.js, etc.)

### Accessing the Frontend App

Once the FastAPI client is running, simply open your browser and navigate to:

```
http://localhost:8000
```

Features:
- **Chat Interface**: Send messages to MCP assistant
- **Normal/Stream Mode**: Toggle between non-streaming and streaming responses
- **Tool Discovery**: View all available MCP tools
- **Session Management**: Save and restore chat sessions
- **Message Deletion**: Delete individual messages or entire chat sessions

### Environment Setup

Requires `OPENAI_API_KEY` environment variable for LLM provider functionality.

### Testing Plan-and-Execute Workflow

The Plan-and-Execute (PNE) feature breaks down complex multi-step queries into structured plans and executes them sequentially:

```bash
# Example: Using curl to test PNE endpoint
curl -X POST http://localhost:8000/pne/complete \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tell me the name of user M4386, their reserved product list, and the total sum of the prices",
    "roomId": "test-room-123"
  }'
```

**How it works**:
1. LLM creates a structured plan with multiple steps
2. Each step is executed in order (tool calls or assistant responses)
3. After each step, the plan is updated based on results
4. Process continues until final answer is ready

**Two implementations available**:
- `service/pne.py` - Pure OpenAI structured output implementation (currently active in `route/pne.py:14`)
- `service/pne_langchain.py` - LangChain/LangGraph implementation (alternative, imported but not used)

## Architecture

### MCP Server Layer (`core/server/`)

FastMCP servers define tools using the `@mcp.tool()` decorator. Each tool:
- Must have `async` signature
- Accepts `Context` as last parameter for logging
- Returns `ToolResult` with `TextContent` and `structured_content`
- Can be tagged and have metadata for filtering

### MCP Client Layer (`core/client/`)

**Entry point**: `client.py` creates FastAPI app with four routers:
- `route/chat.py` - Chat endpoint for simple conversations
- `route/tool.py` - Tool listing endpoint
- `route/pne.py` - Plan-and-execute endpoint for complex multi-step tasks
- `route/test.py` - Test endpoints

**Static file serving**: FastAPI also serves the frontend application:
- `GET /` - Returns `index.html` from `core/client/resource/app/` directory
- `/static/*` - Serves static files (JavaScript, CSS, images) from `core/client/resource/app/` directory
- Uses `StaticFiles` middleware to mount the app directory at `/static`
- Frontend files are served directly from FastAPI, eliminating the need for a separate web server

**Service layer** (`service/`):
- `ChatService` - Orchestrates LLM + MCP tool invocation workflow for simple chat
- `PlanAndExecuteChatService` - Two implementations for plan-and-execute workflow:
  - `service/pne.py` - Pure implementation using OpenAI structured output
  - `service/pne_langchain.py` - LangChain/LangGraph-based implementation
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

*Plan-and-Execute mode* (`service/pne.py:PlanAndExecuteChatService.complete()`):
1. **Planning phase**: Use `OpenAIProvider.structured_output_with_tools()` to generate initial plan as structured `Action` object (contains either `Plan` or `Response`)
2. **Execution phase**: If result is a `Plan`, execute first step:
   - For `tool_call` steps: Invoke MCP tools via `OpenAIProvider.invoke_tools()` and execute with `McpTool.call()`
   - For `assistant` steps: Generate response using `OpenAIProvider.structured_output()`
3. **Replanning phase**: After each step, call `structured_output_with_tools()` with updated context and past steps to get next `Action`
4. **Iteration**: Repeat steps 2-3 until `Action.response.type == 'response'`, then return final message
5. Uses Pydantic models (`Plan`, `Step`, `Response`, `Action`) to enforce structured planning workflow

*Plan-and-Execute with LangChain* (`service/pne_langchain.py:PlanAndExecuteChatService.complete()`):
1. Uses LangGraph's `StateGraph` to model plan-execute-replan workflow
2. Three nodes: `planner` (initial planning), `agent` (execute step), `replan` (re-plan or finish)
3. State: `PlanExecute` TypedDict with input, plan, past_steps, response
4. Integrates with MCP servers via `langchain_mcp_adapters.MultiServerMCPClient`
5. Uses LangChain agents created with `create_agent()` for task execution

**MCP server configuration**: Defined in `common/service.py:CommonService.config` as a dictionary mapping server names to HTTP URLs. The `fastmcp.Client` aggregates multiple MCP servers.

**LLM integration** (`common/llm/`):
- `OpenAIProvider` - Wraps OpenAI API with multiple capabilities:
  - `invoke_tools()` - LLM function calling to decide which tools to invoke
  - `chat_complete()` - Generate final response with tool results
  - `chat_stream()` - Generate streaming response
  - `structured_output()` - Generate response parsed into Pydantic model structure
  - `structured_output_with_tools()` - Generate structured response with tool results
  - `get_langchain_object()` - Returns LangChain `ChatOpenAI` instance for LangChain integration
  - Model: `gpt-4.1-mini`
- `model.py:AvailableTool` - Represents an available MCP tool with tag filtering support
- `model.py:McpTool` - Represents an invoked tool with `call()` method to execute via MCP client using `client.call_tool_mcp()`
- Uses OpenAI's `responses.create()` and `responses.parse()` APIs for function calling and structured output

**Prompt management**: `PromptManager` (singleton) loads prompts from `resource/prompt.yaml`:
- Chat prompts (`system_prompt`)
- Plan-and-Execute prompts:
  - `planning_instruction_prompt` - Initial plan generation
  - `replanning_prompt` - Re-planning after step execution
  - `plan_executor.system_prompt` / `plan_executor.user_prompt_template` - Step execution
- LangChain-specific prompts:
  - `langchain_task_executor` - Task execution agent prompt
  - `langchain_planner` - Planning agent prompt
  - `langchain_replanner` - Re-planning agent prompt

**CORS configuration**: The FastAPI client (`client.py:14-21`) includes CORS middleware to allow frontend apps to make API calls. Configured with `allow_origins=["*"]` for development.

### Frontend App Layer (`core/client/resource/app/`)

Simple single-page application for testing MCP client functionality:
- **Technology**: Vanilla JavaScript, HTML5, CSS3 (no frameworks)
- **Files**:
  - `index.html` - Main HTML structure with embedded CSS styles
  - `app.js` - JavaScript application logic and API integration
- **Features**:
  - Chat interface with message history
  - Mode toggle for normal vs. streaming responses
  - Tool list modal for viewing available MCP tools
  - Real-time message display with animations
- **API Integration**: Calls FastAPI client endpoints at `http://localhost:8000`
- **Modes**:
  - Normal mode: Fetches complete response from `/pne/complete`
  - Stream mode: Receives Server-Sent Events (SSE) from `/pne/stream`

### Data Models

**Request/Response models** (`models/`):
- `models/request.py`:
  - `ChattingRequest` - Simple chat request with question and roomId
  - `PlanAndExecuteChattingRequest` - Plan-and-execute request for complex multi-step queries
- `models/response.py` - `ChatResponse`, `ToolListResponse`

**Plan-and-Execute models** (`service/pne.py`):
- `Step` - Single step in a plan with task description and type (`tool_call` or `assistant`)
- `Plan` - Structured plan with list of sequential steps
- `Response` - Final response message to user
- `Action` - Union type containing either a Plan or Response

**LangChain Plan-and-Execute models** (`service/pne_langchain.py`):
- `PlanExecute` - TypedDict state for LangGraph workflow (input, plan, past_steps, response)
- `Plan` - List of step descriptions
- `Response` - Final response to user
- `Act` - Action containing either Plan or Response

## Key Files

**Client Core**:
- `core/client/client.py:19-25` - CORS middleware configuration for API access
- `core/client/client.py:35-43` - Static file serving and frontend app configuration
- `core/client/common/service.py:10` - MCP server URL configuration in `CommonService.config`

**Chat Service**:
- `core/client/route/chat.py` - Chat router with `/chat/main/complete` and `/chat/main/stream` endpoints
- `core/client/service/chat.py:27` - Main chat workflow orchestration in `ChatService.run()`
- `core/client/service/chat.py:18` - Available tool retrieval with tag filtering

**Plan-and-Execute Service**:
- `core/client/route/pne.py` - PNE router with `/pne/complete` and `/pne/stream` endpoints
- `core/client/service/pne.py` - Pure implementation of plan-and-execute workflow
  - `service/pne.py:82` - `execute_task()` - Executes single step from plan
  - `service/pne.py:108` - `complete()` - Main PNE orchestration loop
- `core/client/service/pne_langchain.py` - LangChain/LangGraph implementation
  - `service/pne_langchain.py:51` - `AgentBuilder` - Builds LangChain agents
  - `service/pne_langchain.py:120` - `complete()` - LangGraph workflow execution

**LLM Provider**:
- `core/client/common/llm/openai_provider/model.py` - OpenAI provider with multiple methods:
  - `:28` - `invoke_tools()` - LLM function calling
  - `:48` - `chat_complete()` - Final response generation
  - `:72` - `chat_stream()` - Streaming response generation
  - `:96` - `structured_output()` - Structured response parsing
  - `:122` - `structured_output_with_tools()` - Structured response with tool results
  - `:24` - `get_langchain_object()` - LangChain ChatOpenAI instance
- `core/client/common/llm/model.py:41` - `McpTool` class definition
- `core/client/common/llm/model.py:47` - MCP tool execution via `McpTool.call()`

**Prompts**:
- `core/client/common/prompt.py` - `PromptManager` singleton for prompt management
- `core/client/resource/prompt.yaml` - Prompt templates for chat, PNE, and LangChain

**Data Models**:
- `core/client/models/request.py` - Request models (ChattingRequest, PlanAndExecuteChattingRequest)
- `core/client/models/response.py` - Response models

**MCP Servers**:
- `core/server/alpha.py` - Alpha MCP server (user information tools)
- `core/server/beta.py` - Beta MCP server (price calculation tools)

**Frontend App**:
- `core/client/resource/app/index.html` - Frontend web interface HTML structure and CSS styles
- `core/client/resource/app/app.js` - JavaScript application logic and API integration

## Dependencies

Core dependencies (in `pyproject.toml`):
- `fastapi[standard]` - Client web framework
- `fastmcp` - MCP protocol implementation
- `openai` - LLM provider
- `numpy` - Data processing
- `langchain-openai` - LangChain integration with OpenAI
- `langgraph` - Graph-based workflow orchestration
- `langchain-mcp-adapters` - MCP integration for LangChain
- `pydantic` - Data validation and structured output models

## Instruction
- update CLAUDE.md after modify code