from smolagents import CodeAgent, LiteLLMModel, MCPClient, PlanningStep
from agent_config import (
    LOCAL_AGENT,
    TOOL_CONVERT_AGENT,
    FILE_MANAGEMENT_AGENT,
    TOOL_CONVERT_DELEGATOR_AGENT,
)
from host import Host


def main():
    with MCPClient(LOCAL_AGENT.server_configs) as tools:
        file_management_agent = FILE_MANAGEMENT_AGENT.as_tool_calling_agent(
            name="FileManager",
            desc="Able to perform operations in the filespace such as searches, directory lookups, and reading file content",
            extra_tools=tools,
            max_steps=1,
            # planning_interval=1,  # Plan every 5 step
            verbosity_level=1,
        )
        tool_convert_agent = TOOL_CONVERT_AGENT.as_tool_calling_agent(
            name="ToolConversionExpert",
            desc="Coder that takes a string representing a tool in a programming language and converts it to a Python Tool.",
            extra_tools=tools,
            max_steps=10,
            planning_interval=5,  # Plan every 5 steps
            verbosity_level=1,
        )
        assistant = CodeAgent(
            tools=TOOL_CONVERT_DELEGATOR_AGENT.tools,
            model=LiteLLMModel(**TOOL_CONVERT_DELEGATOR_AGENT.model_config),
            stream_outputs=True,
            managed_agents=[file_management_agent, tool_convert_agent],
            name="Assistant",
            instructions="\n".join(TOOL_CONVERT_DELEGATOR_AGENT.instructions),
            planning_interval=5,  # Plan every 5 steps
            # step_callbacks={PlanningStep: interrupt_after_plan},
            verbosity_level=1,
        )
        host = Host(assistant)
        host.launch_chat()


if __name__ == "__main__":
    main()
