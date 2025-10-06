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
    "glob",
    "smolagents.tools",
    "typing",
    "pathlib",
    "itertools",
    "functools",
    "re",
    "enum",
    "typing",
    "pathlib",
    "pathlib.path",
    "json",
    "time",
    "datetime",
    "datetime.datetime",
    "abc",
    "math",
    "uuid",
    "random",
    "csv",
    "pydantic",
]

blocked_tools = ["init", "models"]

prd_and_task_generation = [
    "parse_prd",
    "add_task",
    "add_subtask",
    "generate",
]

project_initialization_and_configuration = [
    "initialize_project",
    "rules",
    "models",
    "response_language",
]

task_expansion_and_refinement = [
    "expand_task",
    "expand_all",
    "scope_up_task",
    "scope_down_task",
    "update",
    "update_task",
    "update_subtask",
]

task_management_and_status = [
    "get_tasks",
    "get_task",
    "next_task",
    "set_task_status",
    "remove_task",
    "remove_subtask",
    "clear_subtasks",
    "move_task",
]

task_complexity = [
    "analyze_project_complexity",
    "complexity_report",
]

tagging_and_context_management = [
    "list_tags",
    "add_tag",
    "delete_tag",
    "use_tag",
    "rename_tag",
    "copy_tag",
]

research_and_ai_integration = [
    "research",
]

dependency_and_task_relationships = [
    "add_dependency",
    "remove_dependency",
    "validate_dependencies",
    "fix_dependencies",
]


def get_group_tools(group, tools):
    return [tool for tool in tools if tool.name in group]


def main():
    with MCPClient(MANAGED_TASKMASTER_AGENT.server_configs) as tools:
        # tools = [
        #     tool
        #     for tool in tools
        #     if all(blocked not in tool.name for blocked in blocked_tools)
        # ]
        # managed_taskmaster = get_managed_taskmaster_agent_config().as_code_agent(
        #     name="TaskmasterAiToolAgent",
        #     desc="Exposes taskmaster-ai tools and actions. Expects a single step of a plan - CANNOT PROCESS AN ENTIRE PLAN. Use this to manage and organize tasks, including generating, expanding, updating, and prioritizing tasks. Use to analyze project complexity, handle dependencies, and support research-backed operations. Use to manage tags for organizing tasks, set response languages, and provide detailed reports on task status and complexity.",
        #     extra_tools=get_group_tools(tools, tools),
        #     reinforce_tool_format=False,
        #     #  planning_interval=4,
        #     verbosity_level=2,
        #     max_steps=4,
        #     use_structured_outputs_internally=False,
        #     step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
        #     additional_authorized_imports=additional_authorized_imports,
        # )
        model = LiteLLMModel(
            **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # **kwargs={"ctx-size": 40960},
        )
        managed_taskmaster_prd_and_task_generation_agent = get_managed_taskmaster_agent_config().as_code_agent(
            name="TaskmasterAiPrdAndTaskGenerationAgent",
            desc="Use this agent when you need to parse product requirements (PRD), add tasks/subtasks, or generate content. It handles PRD parsing, task creation, and generation workflows. Provide precise PRD details or task instructions for optimal results.",
            extra_tools=get_group_tools(prd_and_task_generation, tools),
            reinforce_tool_format=False,
            #  planning_interval=4,
            verbosity_level=2,
            max_steps=4,
            use_structured_outputs_internally=False,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            # additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
        )
        managed_taskmaster_project_initialization_and_configuration_agent = get_managed_taskmaster_agent_config().as_code_agent(
            name="TaskmasterAiProjectInitializationAndConfigurationAgent",
            desc="Use this agent when setting up new projects. It handles project initialization, rule configuration, model setup, and language selection. Provide project parameters and configuration preferences to create a properly structured project environment.",
            extra_tools=get_group_tools(
                project_initialization_and_configuration, tools
            ),
            reinforce_tool_format=False,
            #  planning_interval=4,
            verbosity_level=2,
            max_steps=4,
            use_structured_outputs_internally=False,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            # additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
        )
        managed_taskmaster_task_expansion_and_refinement_agent = get_managed_taskmaster_agent_config().as_code_agent(
            name="TaskmasterAiTaskExpansionAndRefinementAgent",
            desc="Use this agent when you need to expand, refine, or update tasks/subtasks. It handles scope adjustments, task refinement, and iterative improvements. Provide specific expansion parameters or refinement requirements for focused task optimization.",
            extra_tools=get_group_tools(task_expansion_and_refinement, tools),
            reinforce_tool_format=False,
            #  planning_interval=4,
            verbosity_level=2,
            max_steps=4,
            use_structured_outputs_internally=False,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            # additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
        )
        managed_taskmaster_task_management_and_status_agent = get_managed_taskmaster_agent_config().as_code_agent(
            name="TaskmasterAiTaskManagementAndStatusAgent",
            desc="Use this agent for managing task lifecycles and status tracking. It handles task retrieval, status updates, movement between tasks, and subtask management. Provide specific task identifiers or status change requests for precise control.",
            extra_tools=get_group_tools(task_management_and_status, tools),
            reinforce_tool_format=False,
            #  planning_interval=4,
            verbosity_level=2,
            max_steps=4,
            use_structured_outputs_internally=False,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            # additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
        )
        managed_taskmaster_tagging_and_context_management_agent = get_managed_taskmaster_agent_config().as_code_agent(
            name="TaskmasterAiTaggingAndContextManagementAgent",
            desc="Use this agent for managing tags and contextual metadata. It handles tag creation, deletion, usage, and organization. Provide tag operations or context management requirements to structure information effectively.",
            extra_tools=get_group_tools(tagging_and_context_management, tools),
            reinforce_tool_format=False,
            #  planning_interval=4,
            verbosity_level=2,
            max_steps=4,
            use_structured_outputs_internally=False,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            # additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
        )
        managed_taskmaster_research_and_ai_integration_agent = get_managed_taskmaster_agent_config().as_code_agent(
            name="TaskmasterAiResearchAndAiIntegrationAgent",
            desc="Use this agent for research-based AI integration tasks. It leverages the research tool to gather information and integrate AI capabilities. Provide research queries or AI integration requirements for targeted knowledge acquisition.",
            extra_tools=get_group_tools(research_and_ai_integration, tools),
            reinforce_tool_format=False,
            #  planning_interval=4,
            verbosity_level=2,
            max_steps=4,
            use_structured_outputs_internally=False,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            # additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
        )
        managed_taskmaster_dependency_and_task_relationships_agent = get_managed_taskmaster_agent_config().as_code_agent(
            name="TaskmasterAiDependencyAndTaskRelationshipsAgent",
            desc="Use this agent for managing task dependencies and relationships. It handles dependency creation, removal, validation, and fixing. Provide dependency specifications or relationship management requirements for accurate workflow configuration.",
            extra_tools=get_group_tools(dependency_and_task_relationships, tools),
            reinforce_tool_format=False,
            #  planning_interval=4,
            verbosity_level=2,
            max_steps=4,
            use_structured_outputs_internally=False,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            # additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
        )
        # managed_taskmaster = get_managed_taskmaster_agent_config().as_code_agent(
        #     name="TaskmasterAiLabelAgent",
        #     desc="Exposes taskmaster-ai tools and actions. Expects a single step of a plan - CANNOT PROCESS AN ENTIRE PLAN. Use to manage tags for organizing tasks and setting response languages.",
        #     extra_tools=get_group_tools(tools, tools),
        #     reinforce_tool_format=False,
        #     #  planning_interval=4,
        #     verbosity_level=2,
        #     max_steps=4,
        #     use_structured_outputs_internally=False,
        #     step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
        #     additional_authorized_imports=additional_authorized_imports,
        #     model = LiteLLMModel(
        # **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
        # **kwargs={"ctx-size": 40960},
        # )
        # )
        managed_taskmaster = get_managed_taskmaster_agent_config().as_code_agent(
            name="TaskmasterAiAgent",
            desc="Exposes taskmaster-ai tools and actions. Use this to manage and organize tasks, including generating, expanding, updating, and prioritizing tasks. Use to analyze project complexity, handle dependencies, and support research-backed operations. Use to manage tags for organizing tasks, set response languages, and provide detailed reports on task status and complexity.",
            extra_tools=[],
            reinforce_tool_format=False,
            is_manager=True,
            planning_interval=3,
            verbosity_level=2,
            max_steps=6,
            use_structured_outputs_internally=False,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            additional_authorized_imports=additional_authorized_imports,
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
            managed_agents=[
                managed_taskmaster_prd_and_task_generation_agent,
                # managed_taskmaster_project_initialization_and_configuration_agent,
                managed_taskmaster_task_expansion_and_refinement_agent,
                managed_taskmaster_task_management_and_status_agent,
                managed_taskmaster_tagging_and_context_management_agent,
                managed_taskmaster_research_and_ai_integration_agent,
                managed_taskmaster_dependency_and_task_relationships_agent,
            ],
        )
        assistant = CodeAgent(
            tools=[
                continue_builtins.ReadFile(),
                # continue_builtins.WriteFileToContinueDir(),
                # continue_builtins.WriteFileToTaskMasterDir(),
                continue_builtins.LSTool(),
            ],
            # model=LiteLLMModel(
            #     **AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
            # ),
            model=model,
            stream_outputs=True,
            step_callbacks=[partial(trim_memory, max_prev_actions_steps=-1)],
            additional_authorized_imports=additional_authorized_imports,
            name="Assistant",
            instructions=f"{instructions.MANAGER}\n{instructions.FINAL_ANSWER}\n{instructions.TRIMMED_MEMORY}\n{instructions.QWEN_THINKING}",
            planning_interval=5,  # Plan every 5 steps
            verbosity_level=2,
            max_steps=100,
            use_structured_outputs_internally=False,
            managed_agents=[managed_taskmaster],
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
