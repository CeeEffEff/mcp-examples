# fastmcp-util-server

## Installation

### Local
1. Install UV via the [docs](https://docs.astral.sh/uv/getting-started/installation/).
2. Check UV is installed by running 
```bash
uv
```
3. Install packages 
```bash
uv sync
```

## Running the Server

### Standard
Run the server via:
```bash
uv run fastmcp run main.py:mcp --transport http
```
It will be available at: http://127.0.0.1:8000

### Dev
Runs with MCP Inspector which is web UI for interacting with the server.

```bash
uv run fastmcp dev main.py:mcp --transport http
```

MCP Inspector will open in your browser on localhost:6247 by default.

## Registering the MCP Server

You can use the following commands to generate the config for or register the server:
```bash
uv run mcp install claude-code main.py
uv run mcp install claude-desktop main.py
uv run mcp install cursor main.py
uv run mcp install mcp-json main.py
```
