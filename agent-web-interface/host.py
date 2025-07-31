import gradio as gr

from smolagents import CodeAgent


class Host:
    def __init__(self, agent: CodeAgent):
        self.agent = agent

    def _update_tools(self, tools, add_base_tools):
        self.agent._setup_tools(tools, add_base_tools)
        self.agent._validate_tools_and_managed_agents(tools, self.agent.managed_agents)

    def launch_chat(self):
        demo = gr.ChatInterface(
            fn=lambda message, history: str(self.agent.run(message)),
            type="messages",
            examples=["Analyze the sentiment of the following text 'This is awesome'"],
            title="Agent with MCP Tools",
            description="This is a simple agent that uses MCP tools to answer questions.",
        )
        demo.launch()
