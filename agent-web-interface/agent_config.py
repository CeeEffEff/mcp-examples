from dataclasses import dataclass
from enum import EnumDict
from typing import List


@dataclass
class AgentConfig:
    class LiteLLMModelConfig(EnumDict):
        OLLAMA_QWEN_3 = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model_id": "ollama_chat/qwen3:8b",
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
    AgentConfig.LiteLLMModelConfig.OLLAMA_QWEN_3,
    [AgentConfig.ServerConfig.LOCAL_GRADIO_HTTP_SSE],
)
