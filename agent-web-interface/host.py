import gradio as gr

from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from smolagents import CodeAgent, LogLevel


class Host:
    def __init__(self, agent: CodeAgent, summarise=False, reset=True):
        self.agent = agent
        self.reset = reset
        self.summarise = summarise

    def _update_tools(self, tools, add_base_tools):
        self.agent._setup_tools(tools, add_base_tools)
        self.agent._validate_tools_and_managed_agents(tools, self.agent.managed_agents)

    def handle_message(self, message, history) -> str:
        self.agent.visualize()
        additional_args = {"history": history} if history else {}
        if self.summarise:
            compressed_history = (
                self.agent.run(
                    f"Summarise the following history returning a short bullet point summary:\n```{history}```",
                    max_steps=3,
                )
                if self.summarise and history
                else ""
            )
            history = history if not compressed_history else []
            additional_args = {
                "compressed_history": compressed_history,
                "history": history,
            }
        additional_args = None
        # messages = self.agent.write_memory_to_messages()
        # messages.append(message)
        # self.agent.logger.log_markdown(
        #     "\n".join([m.render_as_markdown() for m in messages[:-2]]),
        #     title="Last two messages after adding message currently being handled",
        #     level=LogLevel.INFO,
        # )

        response = str(
            self.agent.run(
                message,
                # stream=self.agent.stream_outputs,  # TODO implement this
                reset=self.reset,
                additional_args=additional_args,
            )
        )
        # self.first_message = False
        return response

    def launch_chat(self):
        self.demo = gr.ChatInterface(
            # fn=lambda message, history: str(self.agent.run(message)),
            fn=self.handle_message,
            # chatbot=gr.Chatbot()
            type="messages",
            run_examples_on_click=False,
            examples=[
                "Analyze the sentiment of the following text 'This is awesome'",
                """Over 5 steps, count to 5
By that, I mean do not in one python execution count to 5, but rather over 5 thought, code, execution steps, count to 5.
So each code step should print just one number""",
                """Over 10 steps, count to 10
By that, I mean do not in one python execution count to 10, but rather over 10 thought, code, execution steps, count to 10.
So each code step should print just one number""",
                """The tools to convert are TS files located in /Users/conor.fehilly/Documents/repos/continue/core/tools/implementations
Within the TS files in that directory the tools are exported as ToolImpl consts, for example:
export const someExampleToolImpl: ToolImpl = ...""",
                """
There are TS files located in /Users/conor.fehilly/Documents/repos/continue/core/tools/implementations
Within the TS files in that directory the tools are exported as ToolImpl consts, for example:
export const someExampleToolImpl: ToolImpl = ...

You need to convert ONLY the .ts file in index 0 to a .py file.
Only convert one file.
                """,
                """
Use /Users/conor.fehilly/Documents/repos/mcp-examples/.continue/rules/docs/rule_evaluation_framework_v3.md and taskmaster-ai (plus any other tools you need) to plan a project.
This project is going to be the implementation of a python service that evaluates the adherence of LLMs to rules, as described in the md framework guide.

Always ask clarifying questions immediately if you think you need one answered by me, the user.
                """,
                """Basic plan:
1. Use tools to read  /Users/conor.fehilly/Documents/repos/mcp-examples/.continue/rules/docs/rule_evaluation_framework_v3.md
2. Use taskmaster-ai (plus any other tools you need) to plan a project.

Details:
This project is going to be the implementation of a python service that evaluates the adherence of LLMs to rules, as described in the md framework guide.

Rules:
Always ask clarifying questions immediately if you think you need one answered by me, the user.
                """,
                """

# User Task

## Previous attempts
You previously created some Taskmaster tasks for a project of implementing a python service that would evaluate the effectiveness of rules in controlling llm agent behaviour.
There was a Taskmaster PRD and tasks created by you so you should try and continue that work.
Failing that, the original input framework guide exists at /Users/conor.fehilly/Documents/repos/mcp-examples/.continue/rules/docs/rule_evaluation_framework_v3.md so you could start again.

## Requirements
- I would like you to fully implement a python service that can evaluate rules, using Taskmaster to manage your workflow.
- You should use the established Taskmaster workflow (recommended by Taskmaster) to complete the work.
    - It might be possible to find this in an auto-generated file in a .taskmaster directory or a subdirectory of .taskmaster.
- I would like the python to actually be written somewhere - previously you have never output the python to a file and that's a problem.
    - Be careful writing python or including it in planning steps as you may run into issues escaping quotes.
    - Also, I need the service implementation to be complete - do not just output placeholder code with core parts of the implementation missing.
- You should make sure you update the status of tasks/subtasks in taskmaster as you work through the project.
- You should create reports via taskmaster too when it makes sense, and document via md files when it makes sense or you have written some important part of the python service implementation.

- Once you have created your tasks via taskmaster, you should use it for your planning, and your own internal planning stage should refer to using taskmaster.
- When you pick up a task and start, make sure you update it.
- When you think you may have completed a task, make sure you evaluate what you have done against the original task I gave you, and the PRD, and rule_evaluation_framework_v3.md in order to determine if the task is complete, and if so you must update the task in taskamster-ai.
- During planning it is sensible plan a step that might check if you need to update or expand tasks in taskmaster.


----

Fully implement this python llm rule evaluation service using Taskmaster to manage your workflow (aka the User Task).""",
            ],
            title="Agent with MCP Tools",
            description="This is a simple agent that uses MCP tools to answer questions.",
        )
        self.demo.launch()
        # self.demo.chatbot_value
        # demo.chatbot.mes
