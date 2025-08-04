from dataclasses import dataclass
from enum import EnumDict
from typing import List


@dataclass
class AgentConfig:
    class LiteLLMModelConfig(EnumDict):
        OLLAMA_QWEN_3__8b = (
            {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
                "model_id": "ollama_chat/qwen3:8b",
                "api_base": "http://localhost:11434",
                "api_key": "ollama",
            },
        )
        OLLAMA_QWEN_3__14b = (
            {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
                "model_id": "ollama_chat/qwen3:14b",
                "api_base": "http://localhost:11434",
                "api_key": "ollama",
            },
        )
        OLLAMA_QWEN_2_5_CODER_1_5b = (
            {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
                "model_id": "ollama_chat/qwen2.5-coder:1.5b",
                "api_base": "http://localhost:11434",
                "api_key": "ollama",
            },
        )
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


LOCAL_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3__8b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
)

OVERSEER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_2_5_CODER_1_5b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
)

RESEARCHER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3__8b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
)

EXPENSIVE_RESEARCHER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3__14b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
)

SENIOR_SOFTWARE_ENGINEER_AGENT = AgentConfig(
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3__14b,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
)
