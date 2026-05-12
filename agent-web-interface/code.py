from rich.panel import Panel
from rich.text import Text
from smolagents import ActionStep, CodeAgent, LiteLLMModel, LogLevel, MCPClient
from agent_config import (
    DEBUGGER_AGENT,
    LOCAL_AGENT,
    TOOL_CONVERT_AGENT,
    FILE_MANAGEMENT_AGENT,
    TOOL_CONVERT_DELEGATOR_AGENT,
)
from host import Host


# from builtins import o
def trim_memory(memory_step: ActionStep, agent: CodeAgent) -> None:
    latest_step = memory_step.step_number
    keep = []
    for index in range(
        len(agent.memory.steps)
    ):  # Remove previous screenshots from logs for lean processing
        previous_memory_step = agent.memory.steps[index]
        msgs = []
        if (
            isinstance(previous_memory_step, ActionStep)
            and previous_memory_step.step_number <= latest_step - 2
        ):
            msgs.append(f"Discarding {previous_memory_step.dict()}")
            continue
        msgs.append(f"Keeping {previous_memory_step.dict()}")
        keep.append(previous_memory_step)

    agent.logger.log(
        Panel(Text("\n".join(msgs))),
        level=LogLevel.INFO,
    )

    agent.memory.steps = keep


def main():
    with MCPClient(LOCAL_AGENT.server_configs) as _:
        assistant = CodeAgent(
            tools=TOOL_CONVERT_AGENT.tools,
            model=LiteLLMModel(**TOOL_CONVERT_AGENT.model_config),
            stream_outputs=True,
            step_callbacks=[trim_memory],
            additional_authorized_imports=[
                "os",
                "os.path",
                "glob",
                "builtins.open",
                "smolagents.tools",
                "typing",
            ],
            name="Assistant",
            instructions="\n".join(TOOL_CONVERT_AGENT.instructions),
            planning_interval=5,  # Plan every 5 steps
            verbosity_level=1,
        )
        host = Host(assistant)
        host.launch_chat()


if __name__ == "__main__":
    main()

"""
You said:


It appears that the TypeScript code has been successfully converted to Python. The converted function is defined within a create_function method, which returns a new tool instance.

Here's the complete Python code:


from smolagents.tools import tool

def create_function():
    \"\"\"
    Creates a synchronous version of the original asynchronous function.

    Returns:
        function: The converted synchronous function.
    \"\"\"
    class ContextItem:
        def __init__(self, name: str, description: str, content: str):
            self.name = name
            self.description = description
            self.content = content

    def codebase_tool_impl(parameters: dict, extras: dict) -> list[ContextItem]:
        query = parameters.get("query")

        try:
            context_extras = {
                "config": extras.get("config"),
                "full_input": query,
                "embeddings_provider": extras["config"].get("selected_model_by_role").get("embed"),
                "reranker": extras["config"].get("selected_model_by_role").get("rerank"),
                "llm": extras["llm"],
                "ide": extras.get("ide"),
                "selected_code": [],  # List[RangeInFile]
                "fetch": extras["fetch"],
                "is_in_agent_mode": True,  # always true in tool call
            }

            # Use the existing retrieval function to get context items
            results = retrieve_context_items_from_embeddings(
                context_extras,
                None,
                None,
            )

            # If no results found, return helpful message
            if not results:
                return [
                    ContextItem(
                        name="No Results",
                        description="Codebase search",
                        content=f"No relevant code found for query: \"{query}\". This could mean:\n- The codebase hasn't been indexed yet\n- No code matches the search criteria\n- Embeddings provider is not configured\nTry re-indexing the codebase or using a more specific query.",
                    ),
                ]

            return results

        except Exception as error:
            return [
                ContextItem(
                    name="Error",
                    description="Codebase search error",
                    content=f"Failed to search codebase: {str(error)}",
                ),
            ]

    new_tool = tool(codebase_tool_impl)
    return new_tool
To use this function, you can call create_function() and assign the returned tool instance to a variable:
s

tool_instance = create_function()
This will give you a synchronous version of the original asynchronous function that you can use within Smolagents.


Can you finish the conversion job please? Write the file if you are done
"""
