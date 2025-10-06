from dataclasses import dataclass
from enum import EnumDict
from typing import List, Optional, Type

from mcp import StdioServerParameters


import instructions
from tools import continue_builtins
from smolagents.tools import Tool
from smolagents import (
    ToolCallingAgent,
    LiteLLMModel,
    CodeAgent,
    FinalAnswerTool,
)


@dataclass
class AgentConfig:
    class LiteLLMModelConfig(EnumDict):
        OLLAMA_QWEN_3__8b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen3:8b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
            # "ctx-size": 40960,
        }
        OLLAMA_QWEN_3_MAX_CTX__8b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen3-max-context:8b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
            # "ctx-size": 40960,
        }
        OLLAMA_QWEN_3_HALF_CTX__8b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen3-max-context:8b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
            "ctx-size": 20960,
        }
        OLLAMA_QWEN_3__14b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen3:14b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
        }
        OLLAMA_QWEN_3_MAX_CTX__14b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen3-max-context:14b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
        }

        OLLAMA_QWEN_2_5_CODER_1_5b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen2.5-coder:1.5b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
        }
        OLLAMA_QWEN_2_5_CODER_7b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen2.5-coder:7b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
            # "num_ctx": 8192,
        }
        OLLAMA_llama_3_1__8b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/llama3.1:8b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
        }

    class ServerConfig(EnumDict):
        LOCAL_GRADIO_HTTP_SSE = {
            "url": "http://localhost:7860/gradio_api/mcp/sse",
            "transport": "sse",
        }
        LOCAL_FASTMCP_HTTP = {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable-http",
        }

    model_config: LiteLLMModelConfig
    server_configs: List[ServerConfig | StdioServerParameters]
    instructions: List[str]
    tools: List[Tool]

    def _as_agent(
        self,
        agent_type: Type,
        name: str,
        desc: str,
        extra_tools: Optional[List[Tool]] = None,
        model: LiteLLMModel = None,
        **kwargs,
    ):
        if self.instructions is None:
            self.instructions = []
        agent: CodeAgent = agent_type(
            # tools=self.tools + extra_tools if extra_tools else self.tools,
            tools=extra_tools,
            model=model if model else LiteLLMModel(**self.model_config),
            name=name,
            description=desc,
            instructions="\n".join(self.instructions) if self.instructions else None,
            **kwargs,
        )
        print(f"{agent.name} has tools: {[t.name for t in extra_tools]}")
        print(f"{agent.name} has instructions:\n{agent.instructions}\n\n")
        # agent-web-interface/.venv/lib/python3.13/site-packages/smolagents/prompts/code_agent.yaml
        return agent

    def as_tool_calling_agent(
        self, name: str, desc: str, extra_tools: Optional[List[Tool]] = None, **kwargs
    ) -> ToolCallingAgent:
        if extra_tools is None:
            extra_tools = []
        tool_names = [t.name for t in self.tools]
        tools = (
            self.tools + [et for et in extra_tools if et.name not in tool_names]
            if extra_tools
            else self.tools
        )
        _extra_tools = (
            [FinalAnswerTool()]
            if not any(isinstance(t, FinalAnswerTool) for t in tools)
            else []
        )
        self.instructions.append(instructions.USING_JSON_TOOLS)
        kwargs["max_tool_threads"] = 1
        return self._as_agent(
            ToolCallingAgent, name, desc, tools + _extra_tools, **kwargs
        )

    def as_code_agent(
        self,
        name: str,
        desc: str,
        extra_tools: Optional[List[Tool]] = None,
        reinforce_tool_format=False,
        is_manager=False,
        model: LiteLLMModel = None,
        **kwargs,
    ) -> CodeAgent:
        if extra_tools is None:
            extra_tools = []
        tool_names = [t.name for t in self.tools]
        tools = (
            self.tools + [et for et in extra_tools if et.name not in tool_names]
            if extra_tools
            else self.tools
        )
        _extra_tools = (
            [FinalAnswerTool()]
            if not any(isinstance(t, FinalAnswerTool) for t in tools)
            else []
        )
        if reinforce_tool_format:
            self.instructions.append(instructions.USING_CODE_TOOLS)
        if is_manager:
            self.instructions.append(instructions.MANAGER)
        # if instructions.FINAL_ANSWER not in self.instructions:
        #     self.instructions.append(instructions.FINAL_ANSWER)
        return self._as_agent(
            CodeAgent, name, desc, tools + _extra_tools, model, **kwargs
        )


TASTMASTER_AI = StdioServerParameters(
    command="npx",
    # args=["-y", "--package=task-master-ai", "task-master-ai"],
    args=["-y", "task-master-ai"],
    env={
        "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_HERE",
        "PERPLEXITY_API_KEY": "YOUR_PERPLEXITY_API_KEY_HERE",
        "OPENAI_API_KEY": "YOUR_OPENAI_KEY_HERE",
        "GOOGLE_API_KEY": "YOUR_GOOGLE_KEY_HERE",
        "XAI_API_KEY": "YOUR_XAI_KEY_HERE",
        "OPENROUTER_API_KEY": "YOUR_OPENROUTER_KEY_HERE",
        "MISTRAL_API_KEY": "YOUR_MISTRAL_KEY_HERE",
        "AZURE_OPENAI_API_KEY": "YOUR_AZURE_KEY_HERE",
        "OLLAMA_API_KEY": "YOUR_OLLAMA_API_KEY_HERE",
    },
)

NEO4J_MEMORY = StdioServerParameters(
    command="uvx",
    # args=["-y", "--ßpackage=task-master-ai", "task-master-ai"],
    args=[
        "mcp-neo4j-memory@0.3.0",
        "--db-url",
        "bolt://localhost:7687/",
        "--username",
        "neo4j",
        "--password",
        "2VZi3xnzpl&2ZThU",
    ],
    env={},
)

LOCAL_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3__8b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [],
    [],
)

OVERSEER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_2_5_CODER_1_5b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [],
    [],
)

RESEARCHER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3__8b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [],
    [],
)

EXPENSIVE_RESEARCHER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__14b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [],
    # [instructions.WEB_CHAT, instructions.TASKMASTER_PLANNING],
    [],
)

SENIOR_SOFTWARE_ENGINEER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_2_5_CODER_7b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [],
    [],
)

WEB_CHAT_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_2_5_CODER_7b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [instructions.WEB_CHAT],
    [],
)

TOOL_CONVERT_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_2_5_CODER_7b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [instructions.TOOL_CONVERT, instructions.ERROR_REPORTS],
    [continue_builtins.ReadFile(), continue_builtins.write_converted_file],
)

TOOL_CONVERT_DELEGATOR_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_2_5_CODER_7b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [
        instructions.WEB_CHAT,
        instructions.TOOL_CONVERT_INPUT,
        instructions.TOOL_CONVERT_OUTPUT,
        instructions.PLAN_TOOL_CONVERT,
        instructions.DELEGATE,
        instructions.TOOL_CONVERT_DISCOVERY,
        instructions.MORE_INFO,
    ],
    [],
)

FILE_MANAGEMENT_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_2_5_CODER_7b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [instructions.FILE_MANAGER, instructions.ERROR_REPORTS],
    tools=[
        # continue_builtins.get_number_of_files,
        continue_builtins.read_files,
        continue_builtins.write_converted_file,
    ],
    # list(continue_builtins.initialize_tools().values()),
)


TOOL_CONVERT_SINGLE_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3__8b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [
        instructions.WEB_CHAT,
        instructions.PLAN_TOOL_CONVERT,
        instructions.MORE_INFO,
        instructions.TOOL_CONVERT,
        instructions.TOOL_CONVERT_OUTPUT,
        instructions.ERROR_REPORTS,
        instructions.QWEN_CODE_AGENT,
    ],
    tools=list(continue_builtins.initialize_tools().values()),
)

TOOL_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_llama_3_1__8b,
    [
        AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE,
        AgentConfig.ServerConfig.LOCAL_FASTMCP_HTTP,
    ],
    [
        instructions.WEB_CHAT,
        instructions.MORE_INFO,
        instructions.ERROR_REPORTS,
        instructions.CAUTIOUS_ACTOR,
    ],
    tools=list(continue_builtins.initialize_tools().values()),
)

DEBUGGER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_2_5_CODER_1_5b,
    [],
    [instructions.ERROR_REPORTS, instructions.DEBUGGER],
    [],
)


TASKMASTER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__14b,
    [
        StdioServerParameters(
            command="npx",
            # args=["-y", "--package=task-master-ai", "task-master-ai"],
            args=["-y", "task-master-ai"],
            env={
                "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_HERE",
                "PERPLEXITY_API_KEY": "YOUR_PERPLEXITY_API_KEY_HERE",
                "OPENAI_API_KEY": "YOUR_OPENAI_KEY_HERE",
                "GOOGLE_API_KEY": "YOUR_GOOGLE_KEY_HERE",
                "XAI_API_KEY": "YOUR_XAI_KEY_HERE",
                "OPENROUTER_API_KEY": "YOUR_OPENROUTER_KEY_HERE",
                "MISTRAL_API_KEY": "YOUR_MISTRAL_KEY_HERE",
                "AZURE_OPENAI_API_KEY": "YOUR_AZURE_KEY_HERE",
                "OLLAMA_API_KEY": "YOUR_OLLAMA_API_KEY_HERE",
            },
        )
    ],
    [
        # "If you are in planning mode DO NOT THINK.",
        instructions.PLANNING_STEP,
        instructions.CLARIFY_IMMEDIATELY,
        # instructions.WEB_CHAT,
        instructions.CONCISE_THINKING,
        instructions.TASKMASTER_PLANNING,
    ],
    [
        # continue_builtins.read_files,
        continue_builtins.ReadFile(),
        # continue_builtins.WriteFileToContinueDir(),
        # continue_builtins.ResolveLSToolDirPath(),
        # continue_builtins.filter_for_suffix,
        # continue_builtins.LSTool(),
        # continue_builtins.FileGlobSearch(),
        # continue_builtins.SplitGrepResultsByFile(),
    ],
)


def get_managed_taskmaster_agent_config():
    return AgentConfig(
        AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3_MAX_CTX__8b,
        [
            StdioServerParameters(
                command="npx",
                # args=["-y", "--package=task-master-ai", "task-master-ai"],
                args=["-y", "task-master-ai"],
                env={
                    "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_HERE",
                    "PERPLEXITY_API_KEY": "YOUR_PERPLEXITY_API_KEY_HERE",
                    "OPENAI_API_KEY": "YOUR_OPENAI_KEY_HERE",
                    "GOOGLE_API_KEY": "YOUR_GOOGLE_KEY_HERE",
                    "XAI_API_KEY": "YOUR_XAI_KEY_HERE",
                    "OPENROUTER_API_KEY": "YOUR_OPENROUTER_KEY_HERE",
                    "MISTRAL_API_KEY": "YOUR_MISTRAL_KEY_HERE",
                    "AZURE_OPENAI_API_KEY": "YOUR_AZURE_KEY_HERE",
                    "OLLAMA_API_KEY": "YOUR_OLLAMA_API_KEY_HERE",
                },
            )
        ],
        [
            # "If you are in planning mode DO NOT THINK.",
            instructions.MANAGED_AGENT,
            # instructions.PLANNING_STEP,
            instructions.CLARIFY_IMMEDIATELY,
            instructions.TRIMMED_MEMORY,
            instructions.TRIPLE_QUOTES,
            instructions.TASKMASTER_FILES,
            # instructions.WEB_CHAT,
            # instructions.CONCISE_THINKING,
            # instructions.TASKMASTER_PLANNING,
        ],
        [
            # continue_builtins.read_files,
            continue_builtins.ReadFile(),
            continue_builtins.WriteFileToContinueDir(),
            continue_builtins.WriteFileToTaskMasterDir(),
            continue_builtins.LSTool(),
            # continue_builtins.ResolveLSToolDirPath(),
            # continue_builtins.filter_for_suffix,
            # continue_builtins.LSTool(),
            # continue_builtins.FileGlobSearch(),
            # continue_builtins.SplitGrepResultsByFile(),
        ],
    )


MANAGED_TASKMASTER_AGENT = get_managed_taskmaster_agent_config()
