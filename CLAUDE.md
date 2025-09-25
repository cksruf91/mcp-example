# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a minimal Python project with a simple structure:
- `main.py` - Single entry point with a basic "Hello World" function
- `pyproject.toml` - Project configuration using modern Python packaging standards
- `mcp-project/` - Virtual environment directory (should be ignored for development)

## Development Commands

### Installing Dependencies
```bash
pip install -e .
```

### Running the MCP Server
```bash
python main.py server
```

### Running the MCP Client (Demo Mode)
```bash
python main.py client
```

### Running the MCP Client (Interactive Mode)
```bash
python main.py client --interactive
```

### Running Individual Components
```bash
# Run server directly
python mcp_server.py

# Run client directly
python mcp_client.py
python mcp_client.py --interactive
```

### Python Environment
The project uses Python 3.12+ as specified in pyproject.toml. A virtual environment exists in `mcp-project/` but standard Python virtual environment practices should be used for development.

## Project Configuration

- Licensed under Apache License 2.0
- Dependencies: fastmcp, asyncio-mqtt
- Project name: "mcp-example"
- Version: 0.1.0

## Architecture Notes

This is an MCP (Model Context Protocol) implementation with client-server architecture:

### Server (`mcp_server.py`)
- Built using FastMCP framework
- Provides tools for: time queries, math operations, file operations, note management
- Supports resources and prompts
- Uses stdio transport for communication

### Client (`mcp_client.py`)
- Connects to MCP servers via subprocess
- Can run in demo mode or interactive mode
- Demonstrates tool calling, resource reading, and prompt usage

### Main Entry Point (`main.py`)
- Unified interface to run either server or client
- Handles argument parsing and mode selection

### Available Tools
- `get_current_time()`: Returns current timestamp
- `add_numbers(a, b)`: Adds two numbers
- `list_files(directory)`: Lists files in a directory
- `write_note(filename, content)`: Writes content to a note file
- `read_note(filename)`: Reads content from a note file

### Resources
- `config://system`: System configuration information

### Prompts
- `greeting`: Generates personalized greeting messages