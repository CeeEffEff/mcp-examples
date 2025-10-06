# mcp-sentiment-server
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
The capabilities of your MCP server are compiled into a schema.
This schema dictates to an agent how to interact with the server.

You can view it at: http://localhost:7860/gradio_api/mcp/schema

### Send Request via the Web UI
Gradio provides a web interface that allows you to interact with your Gradio server.

You can view it at: http://localhost:7860/?lang=mcp

### View Server-Sent Events
Server-Sent Events (SSE) are events that are pushed by the server (and could be consumed by a client).
The most common use in MCP is for Sampling, which is where the Server requests the Client (specifically, the Host application) to perform LLM interactions.

The stream of SSE is viewable at: http://localhost:7860/gradio_api/mcp/sse

## Core Functionality

The server implements a sentiment analysis tool using TextBlob for NLP processing. Here's how it works:

### Sentiment Analysis Function
```python
def sentiment_analysis(text: str) -> dict:
    """
    Analyze the sentiment of the given text.

    Args:
        text (str): The text to analyze

    Returns:
        dict: A dict string containing polarity, subjectivity, and assessment.
            Use these values to assess the sentiment of the text:
              - Polarity ranges from -1 (negative) to 1 (positive).
              - Assessment indicates whether the sentiment is positive, negative, or neutral.
              - Subjectivity ranges from 0 (objective) to 1 (subjective).
    """
    blob = TextBlob(text)
    sentiment = blob.sentiment

    result = {
        "polarity": round(sentiment.polarity, 2),  # -1 (negative) to 1 (positive)
        "subjectivity": round(sentiment.subjectivity, 2),  # 0 (objective) to 1 (subjective)
        "assessment": "positive" if sentiment.polarity > 0 else "negative" if sentiment.polarity < 0 else "neutral",
    }

    return result
```

### Gradio Interface
The server provides a simple web interface for testing:
```python
demo = gr.Interface(
    fn=sentiment_analysis,
    inputs=gr.Textbox(placeholder="Enter text to analyze..."),
    outputs=gr.JSON(),
    title="Text Sentiment Analysis",
    description="Analyze the sentiment of text using TextBlob",
)
```

## Server Capabilities & Integration

### Web Interface
You can interact with the server directly through the web UI:
- Accessible at: http://localhost:7860/?lang=mcp
- Allows manual testing of sentiment analysis
- Shows real-time results from the `sentiment_analysis` function

### Server-Sent Events (SSE)
The server supports streaming interactions through SSE:
- Stream endpoint: http://localhost:7860/gradio_api/mcp/sse
- Used for:
  - Agent communication
  - LLM sampling (pushing results to clients)

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

## Tutorial Workflow Mapping

| Tutorial Step                | Code Component                     | Description |
|-----------------------------|------------------------------------|-------------|
| Local LLM setup             | `pyproject.toml`, `Dockerfile`     | Dependency management and containerization |
| VS Code integration        | `mcp.json` configuration           | Registering MCP server for VS Code extensions |
| Web UI testing              | Gradio interface in `main.py`      | Manual sentiment analysis |
| Agent communication         | SSE endpoint (`/gradio_api/mcp/sse`) | Server-Sent Events for agent interaction |
| MCP schema usage           | `/gradio_api/mcp/schema`           | Discovering server capabilities |