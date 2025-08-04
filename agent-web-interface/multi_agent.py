from smolagents import CodeAgent, LiteLLMModel, MCPClient
from agent_config import (
    LOCAL_AGENT,
    OVERSEER_AGENT,
    RESEARCHER_AGENT,
    EXPENSIVE_RESEARCHER_AGENT,
    SENIOR_SOFTWARE_ENGINEER_AGENT,
)
from host import Host


def main():
    with MCPClient(LOCAL_AGENT.server_configs) as tools:
        researcher = CodeAgent(
            tools=tools,
            model=LiteLLMModel(**RESEARCHER_AGENT.model_config),
            name="researcher",
            description="Pretty good at reasoning and problem solving.",
        )
        expensive_researcher = CodeAgent(
            tools=tools,
            model=LiteLLMModel(**EXPENSIVE_RESEARCHER_AGENT.model_config),
            name="expensive-researcher",
            description="Good at reasoning and problem solving, but more expensive for us to use.",
        )
        engineer = CodeAgent(
            tools=tools,
            model=LiteLLMModel(**SENIOR_SOFTWARE_ENGINEER_AGENT.model_config),
            name="senior-software-engineer",
            description="The best we have a engineering code. Not very chatty, but reliable.",
        )
        agent = CodeAgent(
            tools=[],
            model=LiteLLMModel(**OVERSEER_AGENT.model_config),
            stream_outputs=True,
            managed_agents=[researcher, expensive_researcher, engineer],
        )
        host = Host(agent)
        host.launch_chat()


if __name__ == "__main__":
    main()
