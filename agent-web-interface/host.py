import gradio as gr

from smolagents import CodeAgent


class Host:
    def __init__(self, agent: CodeAgent):
        self.agent = agent
        self.first_message = True

    def _update_tools(self, tools, add_base_tools):
        self.agent._setup_tools(tools, add_base_tools)
        self.agent._validate_tools_and_managed_agents(tools, self.agent.managed_agents)

    def handle_message(self, message, history) -> str:
        response = str(self.agent.run(message, reset=self.first_message))
        self.first_message = False
        return response

    def launch_chat(self):
        demo = gr.ChatInterface(
            # fn=lambda message, history: str(self.agent.run(message)),
            fn=self.handle_message,
            type="messages",
            examples=[
                "Analyze the sentiment of the following text 'This is awesome'",
                """The tools to convert are TS files located in /Users/conor.fehilly/Documents/repos/continue/core/tools/implementations
Within the TS files in that directory the tools are exported as ToolImpl consts, for example:
export const someExampleToolImpl: ToolImpl = ...""",
            ],
            title="Agent with MCP Tools",
            description="This is a simple agent that uses MCP tools to answer questions.",
        )
        demo.launch()
