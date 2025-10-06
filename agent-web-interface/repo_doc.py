from functools import partial
import uuid
from mcp import stdio_client
from rich.panel import Panel
from rich.text import Text
from smolagents import (
    ActionStep,
    CodeAgent,
    LiteLLMModel,
    LogLevel,
    MCPClient,
    PlanningStep,
    TaskStep,
)
from agent_config import (
    TASTMASTER_AI,
    NEO4J_MEMORY,
    EXPENSIVE_RESEARCHER_AGENT,
    MANAGED_TASKMASTER_AGENT,
    get_managed_taskmaster_agent_config,
    AgentConfig,
)
from tools import continue_builtins
from callbacks.memory_step import trim_memory
from host import Host
import instructions

additional_authorized_imports = [
    "os",
    "os.path",
    # "glob",
    "smolagents.tools",
    "typing",
    # "pathlib",
    "itertools",
    "functools",
    "re",
    "enum",
    "typing",
    # "pathlib",
    # "pathlib.path",
    "json",
    "time",
    "datetime",
    "datetime.datetime",
    # "abc",
    # "math",
    "uuid",
    "random",
    "csv",
    "pydantic",
]

blocked_tools = ["init", "models"]

managed_neo4j = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
    [NEO4J_MEMORY],
    [
        instructions.MANAGED_AGENT,
        instructions.MANAGED_NEO4J,
        instructions.CLARIFY_IMMEDIATELY,
    ],
    [
        # continue_builtins.read_files,
        # continue_builtins.ReadFile(),
        # continue_builtins.LSTool(),
    ],
)

orchestrator = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
    [],
    [
        # instructions.MANAGED_AGENT,
        instructions.CLARIFY_IMMEDIATELY,
        instructions.NEO4J,
    ],
    [
        # continue_builtins.read_files,
        continue_builtins.ReadFile(),
        continue_builtins.LSTool(),
        continue_builtins.GrepSearch(),
        continue_builtins.FileGlobSearch(),
    ],
)


def main():
    with MCPClient(NEO4J_MEMORY) as neo_tools:
        # MCPClient(TASTMASTER_AI) as tm_tools:
        model = LiteLLMModel(
            **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_HALF_CTX__8b,
            # **kwargs={"ctx-size": 40960},
        )

        managed_neo4j_agent = managed_neo4j.as_code_agent(
            name="KnowledgeAndMemory",
            desc="Tool that can store or retreive neo4j knowledge memories. Memories are composed of entities, relationships and observations. You **must** make frequent use of this tool to store new memories and retrieve prior memories. Thoughts, observations, facts, entities etc. Suitable task descriptions should explain exactly what is to be stored, why and any analysis that needs doing, or the kind of memory that need retrieving.",
            extra_tools=neo_tools,
            reinforce_tool_format=False,
            #  planning_interval=4,
            verbosity_level=2,
            max_steps=2,
            use_structured_outputs_internally=False,
            # step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            # additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=LiteLLMModel(
                **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_HALF_CTX__8b,
                # **kwargs={"ctx-size": 40960},
            ),
        )
        assistant = orchestrator.as_code_agent(
            name="Explorer",
            desc="Explorer",
            extra_tools=[],
            # [n for n in neo_tools if "memory" in n.name],
            is_manager=True,
            model=model,
            stream_outputs=True,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            additional_authorized_imports=additional_authorized_imports,
            # instructions=f"{instructions.MANAGER}\n{instructions.FINAL_ANSWER}\n{instructions.TRIMMED_MEMORY}\n{instructions.QWEN_THINKING}",
            planning_interval=3,  # Plan every 5 steps
            verbosity_level=2,
            max_steps=100,
            use_structured_outputs_internally=False,
            managed_agents=[managed_neo4j_agent],
        )
        host = Host(
            assistant,
            summarise=False,
            reset=True,  # Cross chat history
        )
        host.launch_chat()
        # index, block = host.demo.blocks.popitem()
        # block.


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
