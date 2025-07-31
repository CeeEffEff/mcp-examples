from smolagents import CodeAgent, LiteLLMModel, MCPClient
from agent_config import LOCAL_AGENT
from host import Host


def main():
    local_model = LiteLLMModel(**LOCAL_AGENT.model_config)
    with MCPClient(LOCAL_AGENT.server_configs) as tools:
        agent = CodeAgent(tools=tools, model=local_model)
        host = Host(agent)
        host.launch_chat()


if __name__ == "__main__":
    main()
