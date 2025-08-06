from dataclasses import dataclass
from enum import EnumDict
from typing import List, Optional, Type
import instructions
from tools import continue_builtins
from smolagents.tools import Tool
from smolagents import ToolCallingAgent, LiteLLMModel, CodeAgent, FinalAnswerTool


@dataclass
class AgentConfig:
    class LiteLLMModelConfig(EnumDict):
        OLLAMA_QWEN_3__8b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen3:8b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
        }
        OLLAMA_QWEN_3__14b = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen3:14b",
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
        }

    class ServerConfig(EnumDict):
        LOCAL_GRADIO_HTTP_SSE = {
            "url": "http://localhost:7860/gradio_api/mcp/sse",
            "transport": "sse",
        }

    model_config: LiteLLMModelConfig
    server_configs: List[ServerConfig]
    instructions: List[str]
    tools: List[Tool]

    def _as_agent(
        self,
        agent_type: Type,
        name: str,
        desc: str,
        extra_tools: Optional[List[Tool]] = None,
        **kwargs,
    ):
        return agent_type(
            tools=self.tools + extra_tools if extra_tools else self.tools,
            model=LiteLLMModel(**self.model_config),
            name=name,
            description=desc,
            instructions="\n".join(self.instructions) if self.instructions else None,
            **kwargs,
        )

    def as_tool_calling_agent(
        self, name: str, desc: str, extra_tools: Optional[List[Tool]] = None, **kwargs
    ) -> ToolCallingAgent:
        tools = self.tools + extra_tools if extra_tools else self.tools
        _extra_tools = (
            [FinalAnswerTool()]
            if not any(isinstance(t, FinalAnswerTool) for t in tools)
            else []
        )
        return self._as_agent(
            ToolCallingAgent, name, desc, extra_tools + _extra_tools, **kwargs
        )

    def as_code_agent(
        self, name: str, desc: str, extra_tools: Optional[List[Tool]] = None, **kwargs
    ) -> CodeAgent:
        tools = self.tools + extra_tools if extra_tools else self.tools
        _extra_tools = (
            [FinalAnswerTool()]
            if not any(isinstance(t, FinalAnswerTool) for t in tools)
            else []
        )
        return self._as_agent(
            CodeAgent, name, desc, extra_tools + _extra_tools, **kwargs
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
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3__14b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
    [],
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
    [],
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
    tools=list(continue_builtins.initialize_tools().values()),
)
