`.PHONY: all run-agent-cli run-fastmcp-util-server run-mcp-inspector run-agent-web-interface run-mcp-sentiment-server docker-mcp-sentiment-server

all: run-agent-cli run-fastmcp-util-server run-agent-web-interface run-mcp-sentiment-server run-mcp-inspector

run-agent-cli:
	@echo "Running agent-cli service..."
	@cd agent-cli && source .venv/bin/activate && uv run tiny-agents run agent/agent.json

run-fastmcp-util-server:
	@echo "Running fastmcp-util-server service (Standard)..."
	@cd fastmcp-util-server && source .venv/bin/activate && uv run fastmcp run main.py:mcp --transport http

run-mcp-inspector:
	@echo "Running MCP Inspector"
	@cd fastmcp-util-server && source .venv/bin/activate && npx @modelcontextprotocol/inspector

run-agent-web-interface:
	@echo "Running agent-web-interface service..."
	@cd agent-web-interface && source .venv/bin/activate && uv run main.py

run-mcp-sentiment-server:
	@echo "Running mcp-sentiment-server service..."
	@cd mcp-sentiment-server && source .venv/bin/activate && uv run python main.py

docker-mcp-sentiment-server:
	@echo "Building mcp-sentiment-server docker image..."
	@docker build --build-arg PYTHON_VERSION=$(cat .python-version) -t mcp-sentiment-server .
	@echo "Running mcp-sentiment-server docker image..."
	@docker run --rm -p 7860:7860 mcp-sentiment-server
