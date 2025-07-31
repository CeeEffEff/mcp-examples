# agent-cli
https://huggingface.co/learn/mcp-course/unit2/tiny-agents
https://ollama.com/blog/openai-compatibility

The CLI bridges an Ollama model with a Gradio server, both locally running.

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
!WARNING huggingface-hub==0.34.2 works, but huggingface-hub==0.34.3 does not.

## Running the CLI
1. Ensure a `qwen3:8b` model is running via Ollama on `http://localhost:11434`
2. Ensure a Gradio MCP server is running on `http://localhost:7860/gradio_api/mcp/
3. Run the CLI via:
```bash
uv run tiny-agents run agent/agent.json
```

## Configuration Details
The agent configuration is:
```json
{
	"model": "qwen3:8b",
	"endpointUrl": "http://localhost:11434/v1",
	"servers": [
		{
			"type": "sse",
			"url": "http://localhost:7860/gradio_api/mcp/sse"
		}
	]
}
```

### Model Configuration
The agent is configured to use a local qwen3:8b model running locally via Ollama.
Ensure Ollama is running on `http://localhost:11434` before starting the CLI.

### Server Configuration
The agent is connects to local a Gradio MCP server via HTTP+SSE.
Ensure it is running on `http://localhost:7860` before starting the CLI.
