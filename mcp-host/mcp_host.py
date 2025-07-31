from typing import Any, Optional
import gradio as gr

from mcp import StdioServerParameters
from smolagents import (
    CodeAgent,
    Model,
    MCPClient,
)


class McpHost:
    def __init__(
        self,
        model: Model,
        mcp_server_parameters: StdioServerParameters
        | dict[str, Any]
        | list[StdioServerParameters | dict[str, Any]],
        mcp_server_adapter_kwargs: Optional[dict[str, Any]] = None,
    ):
        self.model = model
        self.mcp_server_parameters = mcp_server_parameters
        self.mcp_server_adapter_kwargs = mcp_server_adapter_kwargs

    def run(self):
        with MCPClient(
            self.mcp_server_parameters, self.mcp_server_adapter_kwargs
        ) as tools:
            agent = CodeAgent(tools=[*tools], model=self.model)
            demo = gr.ChatInterface(
                fn=lambda message, history: str(agent.run(message)),
                type="messages",
                examples=[
                    "Analyze the sentiment of the following text 'This is awesome'"
                ],
                title="Agent with MCP Tools",
                description="This is a simple agent that uses MCP tools to answer questions.",
            )
            demo.launch()
