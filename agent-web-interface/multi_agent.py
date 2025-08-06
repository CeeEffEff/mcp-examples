from smolagents import (
    CodeAgent,
    LiteLLMModel,
    MCPClient,
    AUTHORIZED_TYPES,
    UserInputTool,
    FinalAnswerTool,
    PythonInterpreterTool,
    ApiWebSearchTool,
    ToolCallingAgent,
    PromptTemplates,
)
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
        intern = CodeAgent(
            tools=tools,
            model=LiteLLMModel(**OVERSEER_AGENT.model_config),
            name="Intern",
            description="An intern who is learning coding. Capable of more simple tasks.",
            additional_authorized_imports=[
                "requests",
                "math",
                "random",
                "datetime",
                "json",
                "os",
                "sys",
                "re",
                "logging",
            ],
        )
        researcher = ToolCallingAgent(
            tools=tools,
            model=LiteLLMModel(**RESEARCHER_AGENT.model_config),
            name="Researcher",
            description="Use if you need to think through a problem.",
        )
        expensive_researcher = ToolCallingAgent(
            tools=tools,
            model=LiteLLMModel(**EXPENSIVE_RESEARCHER_AGENT.model_config),
            name="ExpensiveResearcher",
            description="Use if you need to think through a comlpex problem. Excellent at reasoning and problem solving. Not for trivial problems.",
        )
        engineer = CodeAgent(
            tools=tools,
            model=LiteLLMModel(**SENIOR_SOFTWARE_ENGINEER_AGENT.model_config),
            name="SeniorSoftwareEngineer",
            description="Extremely capable, can handle complex tasks",
            additional_authorized_imports=[
                "requests",
                "fastmcp",
                "mcp",
                "smolagents",
                "pandas",
                "numpy",
                "fastapi",
                "uvicorn",
                "grpc",
                "flask",
                "sqlalchemy",
                "django",
                "celery",
                "math",
                "random",
                "datetime",
                "json",
                "os",
                "sys",
                "re",
                "logging",
            ],
        )

        agent = CodeAgent(
            tools=[],
            model=LiteLLMModel(**SENIOR_SOFTWARE_ENGINEER_AGENT.model_config),
            stream_outputs=True,
            managed_agents=[intern, engineer, researcher, expensive_researcher],
            name="Assistant",
            # instructions="Remember, during each intermediate step, you can use 'print()' to save whatever important information you will then need. These print outputs will then appear in the 'Observation:' field, which will be available as input for the next step. In the last step you return the final answer using the `final_answer` code function.",
            instructions="You are connected with the user via a webchat inteface. This means to speak to the user you can use the final_answer tool with what you want to say. final_answer always is sent to the user.",
        )
        host = Host(agent)
        host.launch_chat()


if __name__ == "__main__":
    main()
