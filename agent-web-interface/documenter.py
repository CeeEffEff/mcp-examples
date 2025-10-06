from smolagents import CodeAgent, LiteLLMModel, MCPClient
from agent_config import (
    LOCAL_AGENT,
    TOOL_CONVERT_AGENT,
    FILE_MANAGEMENT_AGENT,
    TOOL_CONVERT_DELEGATOR_AGENT,
    TOOL_AGENT,
)
from host import Host


def main():
    with MCPClient(TOOL_AGENT.server_configs) as tools:
        assistant = CodeAgent(
            tools=TOOL_AGENT.tools + tools,
            model=LiteLLMModel(**TOOL_AGENT.model_config),
            stream_outputs=True,
            # managed_agents=[file_management_agent, tool_convert_agent],
            name="Assistant",
            instructions="\n".join(TOOL_AGENT.instructions),
            planning_interval=5,  # Plan every 5 steps
            verbosity_level=1,
        )
        host = Host(assistant)
        host.launch_chat()


if __name__ == "__main__":
    main()
