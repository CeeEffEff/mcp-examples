# mcp-sentiment
https://huggingface.co/learn/mcp-course/unit2/gradio-server

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
Run the server via:
```bash
uv run main.py
```

### View the Server Schema
The capabilities sof your MCP server are compiled into a schema.
This schema dictates to an agent how to interact with the server.

You can view it at: http://localhost:7860/gradio_api/mcp/schema

### Send Request via the Web UI
Gradio provides a web interface that allows you to interact with your Gradio server.

You can view it at: http://localhost:7860/?lang=mcp

### View Server-Sent Events
Server-Sent Events (SSE) are events that are pushed by the server (and could be consumed by a client).
The most common use in MCP is for Sampling, which is where the Server requests the Client (specifically, the Host application) to perform LLM interactions.

The stream of SSE is viewable at: http://localhost:7860/gradio_api/mcp/sse


## Registering the MCP Server

### Basic Server
1. Create a new file `mcp.json`.
2. Add the following JSON content to the file:
```json
{
  "mcpServers": {
    "sentiment-analysis": {
      "url": "http://localhost:7860/gradio_api/mcp/sse"
    }
  }
}
```

### mcp-remote Server
Most MCP clients, including Cursor, currently only support local servers via stdio transport and don’t yet support remote servers with OAuth authentication.
The mcp-remote tool serves as a bridge solution that:
* Runs locally on your machine
* Forwards requests from Cursor to the remote MCP server
* Uses the familiar configuration file format
To configure:
1. Create a new file `mcp.json`.
2. Add the following JSON content to the file:
```json
{
  "mcpServers": {
    "sentiment-analysis": {
      "command": "npx",
      "args": [
        "-y", 
        "mcp-remote", 
        "https://example.com/gradio_api/mcp/sse", 
        "--transport", 
        "sse-only"
      ]
    }
  }
}
```
Once configured, you can ask, for example, Cursor to use your sentiment analysis tool for tasks like analyzing code comments, user feedback, or pull request descriptions.