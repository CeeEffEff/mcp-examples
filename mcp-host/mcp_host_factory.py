from enum import EnumDict
from smolagents import LiteLLMModel
from mcp_host import McpHost


class McpHostFactoy:
    class ServerConfig(EnumDict):
        LOCAL_GRADIO_HTTP_SSE = {
            "url": "http://localhost:7860/gradio_api/mcp/sse",
            "transport": "sse",
        }

    class LiteLLMModelConfig(EnumDict):
        OLLAMA_QWEN_3 = {  # https://docs.litellm.ai/docs/providers/ollama#using-ollama-apichat
            "model": "ollama_chat/qwen3:8b",
            "api_base": "http://localhost:11434",
            "api_key": "ollama",
        }

    @staticmethod
    def construct_host(
        server_configs: list[ServerConfig], model_config: LiteLLMModelConfig
    ):
        """
        Constructs and returns a configured McpHost instance that facilitates communication between a Model and some Servers

        Parameters:
            server_configs (list[ServerConfig]): A list of ServerConfig instances.
            model_config (LiteLLMModelConfig): A LiteLLMModelConfig instance.

        Returns:
            McpHost: A configured McpHost instance with the specified server configurations and model settings.
        """
        servers_configs = [srv_cfg for srv_cfg in server_configs]
        local_model = LiteLLMModel(**model_config)
        host = McpHost(local_model, servers_configs)
        return host
