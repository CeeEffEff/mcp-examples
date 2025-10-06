from smolagents import CodeAgent, LiteLLMModel, MCPClient
from agent_config import (
    DEBUGGER_AGENT,
    LOCAL_AGENT,
    TOOL_CONVERT_AGENT,
    FILE_MANAGEMENT_AGENT,
    TOOL_CONVERT_DELEGATOR_AGENT,
)
from host import Host


def main():
    with MCPClient(LOCAL_AGENT.server_configs) as tools:
        # debugger = DEBUGGER_AGENT.as_tool_calling_agent(
        #     name="ErrorFirstLook",
        #     desc="When an error occurs twice in a row you must use this agent. Task it with identifying the error, use the output bug report to inform your next action. Requires SAFELY ESCAPED inputs. Input: additional_args(dict)(error(str), full_previous_input(str)), full_previous_output(str). Output: bug report(str). All strings must be JSON safe and escaped properly.",
        #     # extra_tools=tools,
        #     max_steps=1,
        #     planning_interval=1,  # Plan every 5 step
        #     verbosity_level=2,
        # )
        file_management_agent = FILE_MANAGEMENT_AGENT.as_code_agent(
            name="FileManager",
            desc="You MUST USE THIS TOOL for file operations.. Just provide plan, dir and index. Reads file content using index of file, and writes python conversion to python file. Please provide it a plan as an additional_arg.",
            # extra_tools=tools,
            max_steps=3,
            planning_interval=3,  # Plan every 5 step
            verbosity_level=2,
            # managed_agents=[debugger],
        )
        # tool_convert_agent = TOOL_CONVERT_AGENT.as_tool_calling_agent(
        #     name="ToolConversionExpert",
        #     desc="Coder that takes a string representing a tool in a programming language and converts it to a Python Tool.",
        #     extra_tools=tools,
        #     max_steps=10,
        #     planning_interval=5,  # Plan every 5 steps
        #     verbosity_level=1,
        #     # managed_agents=[debugger],
        # )
        assistant = CodeAgent(
            tools=TOOL_CONVERT_DELEGATOR_AGENT.tools,
            model=LiteLLMModel(**TOOL_CONVERT_DELEGATOR_AGENT.model_config),
            stream_outputs=True,
            managed_agents=[
                # debugger,
                file_management_agent,
                # tool_convert_agent,
            ],
            name="Assistant",
            instructions="\n".join(TOOL_CONVERT_DELEGATOR_AGENT.instructions),
            planning_interval=5,  # Plan every 5 steps
            verbosity_level=1,
        )
        host = Host(assistant)
        host.launch_chat()


if __name__ == "__main__":
    main()
