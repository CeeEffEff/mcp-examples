# 🧠 Local AI Workshop Starter
Welcome! This repo contains everything you need to follow along during the **Local AI Workshop**. By the end, you'll have a fully local LLM setup including:

- Running models with Ollama  
- Integrating models with VS Code  
- Building a local agent server with a simple Web + CLI interface

---

## ⚙️ Prerequisites

If you'd like to follow along please complete the following **before** the session to ensure you can.

---

### ✅ 1. Homebrew

If you don’t already have Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

### ✅ 2. Python (via `uv`)

We’ll use [`uv`](https://github.com/astral-sh/uv), a superfast Python package and virtual environment manager.

Install `uv`:

```bash
brew install uv
```

Once the repo is cloned, for each service check the relevant README.md to see service specific setup.

---

### ✅ 3. VS Code + Extensions

Please install the following extensions:

- [Continue](https://marketplace.visualstudio.com/items?itemName=Continue.continue) – Highly configurable Agent interface
- [Cline](https://marketplace.visualstudio.com/items?itemName=clineb.cline) (optional) - Heavy duty task and workflow agent interface
- GitHub Copilot (optional)

---

### ✅ 4. Ollama (LLM Runtime)

Install Ollama:

```bash
brew install ollama
```

Start the Ollama daemon:

```bash
ollama serve
```

You could also install the GUI version, but you will be using the command line anyway to add models.
Additionally running the server via the command line gives access to more logs.


---

### ✅ 5. Download Models
Models tend to be large and may take time to download.

The models I use most often:
```bash
ollama pull qwen3:8b
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```
This is my current go to and is based on having 18GB of unified memory - if you have less you will need to scale down.
I have managed to also get qen3:14 running for some tasks.

Take a look online for recommendations or the model specs, or read the next section.


### Selecting a Model
Some important hyperparameters of models include:
- Number of parameters (🤖)
- Context window size (📖)
- Quantization level (🗂️)

These factors impact memory and/or VRAM usage, determining which models you can run. By adjusting one down, you might allow yourself to increase another.

Consider your use case requirements when making a decision. The [VRAM estimator](https://smcleod.net/2024/12/bringing-k/v-context-quantisation-to-ollama/#interactive-vram-estimator) can help with calculations.
Ollama also provides a rough [model selection guide](https://github.com/ollama/ollama?tab=readme-ov-file#model-library).

For model selection, consider its intended purpose (💡) and whether it has tool calling capabilities. You can search for models on the [Ollama website](https://ollama.com/search).


#### Recommended models
Generally speaking my experience and recommendation is as follows:
- **qwen3:8b & qwen3:14b**
  - The only open source Ollama models that work in Chat, Plan and Agent modes
  - Good for plan and act approaches
  - Sometimes need to be told not to think concisely and avoid thought loops
  - Struggle with full context windows
    - Be careful with registering too many rules and/or tools as they will be included in every system prompt.
  - Benefit from frequent session resets
  - Are very receptive to Markdown
- **qwen2.5-coder:1.5b**
  - Nice small model for autocompletes - you may need to adjust timeouts and other settings for them to succeed
- **qwen2.5-coder:7b**
  - Strong performing coder and relatively fast.
  - Unline qwen3, it doesn't have a thinking stage which means you are less likely to get the LLM's thoughts in your edit
  - Good for edits and applies
- **nomic-embed-text**
  - Recommended by Ollama, continue.dev and others as a replacement for the default embeddings used for the @codebase index


## 📂 What’s in This Repo
Once cloned, this repo will include at the root:

## Directories
  - `agent-cli/`: Command-line interface tools for interacting with the agent. Contains `.python-version`, `README.md`, `package.json`, `pyproject.toml`, and an `agent/` directory with `PROMPT.md` and `agent.json`.
  - `agent-web-interface/`: Web-based interface or API for managing the agent. Includes `agent_config.py`, `host.py`, `main.py`, `.python-version`, `README.md`, and `pyproject.toml`.
  - `fastmcp-util-server/`: Backend server for utility functions related to fastmcp. Contains `main.py`, `.python-version`, `README.md`, `pyproject.toml`, and `server-info.json`.
  - `mcp-sentiment-server/`: Server for sentiment analysis or machine learning tasks (MCP). Includes `main.py`, `.python-version`, `Dockerfile`, `README.md`, ajd `pyproject.toml`.
  - `.continue/`: Configuration directory for the continue extension, defining MCP Components.
  - `.taskmaster/`: Taskmaster-ai workspace for managing tasks and workflows. Contains `state.json`, `templates/`, `tasks/`, and `docs/`.
  - `.cursor/`: Likely related to code navigation or UI components (e.g., cursor-based tools). Contains `mcp.json` and a `rules/` directory with files like `cursor_rules.mdc`, `self_improve.mdc`, and workflow definitions.
  - `.clinerrules/`: Configuration directory for cline rules (code formatting/linting). Contains `documentation_guidelines.md` and `expand-requirements-to-mcp-prompt.md`.


## Configuration Files
  - `.env.example`: Sample environment variables for development setup.
  - `docker-compose.yml`: Docker configuration for containerized services (not complete).
  - `.clineignore`: File specifying files to ignore for cline tools.
  - `Makefile`: Build automation tool for compiling and packaging the project.
  - `memory.jsonl`: Stores memory data for `@modelcontextprotocol/server-memory` (can be configured).

## Documentation
  - `README.md`: This file (current location).
  - `GOTCHAS.md`: Notes on common pitfalls, setup issues, or best practices.
  - `docs/definitions.md`: Definitions and explanations of key concepts.
  - `docs/report.md`: Report or analysis documentation.
  - `TODO`: List of tasks or improvements to be addressed.

---

## MCP and This Repo
This repository is designed to give examples of how to implement MCP Components and Capabilities,
along with Agents to use them, and integrate this within VS Code.
Some of the below and other aspects are inspired by https://huggingface.co/mcp-course.

### Components
The three Components in MCP are:
- Host
- Client
- Server

#### Host
The user-facing AI application that end-users interact with directly. Examples include Anthropic’s Claude Desktop,
AI-enhanced IDEs like Cursor, inference libraries like Hugging Face Python SDK, or custom applications built in
libraries like LangChain or smolagents. Hosts initiate connections to MCP Servers and orchestrate the overall flow
between user requests, LLM processing, and external tools.

Some examples of hosts within this repository are:
- agent-web-interface: a simple chat host with a web interface
- agent-cli: an extremely lightweight host with a CLI
- continue: VS Code extension, configured via .continue
- cline: VS Code extension

#### Client
A component within the host application that manages communication with a specific MCP Server.
Each Client maintains a 1:1 connection with a single Server, handling the protocol-level details
of MCP communication and acting as an intermediary between the Host’s logic and the external Server.

Clients usually sit within a Host so the implementation details may not be evident, but you will
notice that Hosts often expect configuration of MPC Servers and LLMs, and this configuration is used
by the Client

Some examples of clients configurations within this repository are:
- agent-web-interface/agent_config.py
- agent-cli/agent/agent.json
- .continue/assistants and .continue/mcpServers

cline also exposes some configuration somewhere.

#### Server
An external program or service that exposes capabilities (Tools, Resources, Prompts) via the MCP protocol.

Some examples of local Servers defined within this repository are:
- mcp-sentiment-server: simple Gradio SSE MCP server with a sentiment-analysis tool (which is not very good)
- fastmcp-util-server: modern fastmcp http-streaming MCP server with local util tools

Some examples of external Servers defined within this repository are:
- @modelcontextprotocol/server-memory: Knowledge Graph memory for an agent
- taskmaster-ai: Task management tool for agents


### Capabilities
MCP defines the following Capabilities:
- Tools: Executable functions that the AI model can invoke to perform actions or retrieve computed data
- Resources: Read-only data sources that provide context without significant computation.
- Prompts: Pre-defined templates or workflows that guide interactions between users, AI models, and the available capabilities.
- Sampling: erver-initiated requests for the Client/Host to perform LLM interactions, enabling recursive actions where the LLM can review generated content and make further 

I think that ./continue best exhibits the configuration of these capabilities:
- ./continue/mcpServers expose **Tools**
- ./continue/docs and various .md files in the repo act as **Resources** that provide context
- ./continue/prompts and ./continue/rules are **Prompts** that initiate and constraint, respectively, interactions with the AI models

## Debugging
The following might be useful for debugging.

### Activity Monitor
It is incredibly important to monitor your memory usage and adjust your prompts/models appropriately.
Use the Activity Monitor program to view memory usage via the Memory tab.
This also helps you to identify if any models are secretely running in the background.


### VS Code Developer Console
Almost all interactions will be viewable via the Developer Console.
In order to view debug logs, which contain extra information, click the dropdown at the top that says “Default levels” and select “Verbose”.
To enable:
1. `cmd` + `shift` + `P`
2. Search for and then select “Developer: Toggle Developer Tools”
3. Select the Console tab
4. Click the dropdown at the top that says “Default levels” and select “Verbose”.
5. Read the console logs

### continue Events Data Store 
continue allows us to configure data stores that all or a selection of agent events are stored.

For example this config sends all events to a directory in this repo:
```yaml .continue/assistants/config.yaml
data:
  - name: Local Data Bank
    destination: file:///Users/conor.fehilly/Documents/repos/mcp-examples/.continue/data_stores
    schema: 0.2.0
    level: all
```

There will be a jsonl file for each event type:
- chatFeedback.jsonl
- chatInteraction.jsonl
- editInteraction.jsonl
- editOutcome.jsonl
- tokensGenerated.jsonl
- toolUsage.jsonl


### Ollama
Ensure you run Ollama via the command line:
```bash
ollama serve
```
This ensures you can view the server logs easily.

You can check for running models via:
```bash
ollama ps
```

Sometimes stopping exection via Hosts isn't enough and the model will still be running.
In this case you can stop running models via Ollama, for example:
```bash
ollama stop qwen3:14b
```

And if that doesn't work, in the running Ollama server:
```bash
CTRL-C
```

### Continue Console
As at https://docs.continue.dev/troubleshooting, to enable the Continue Console:
1. `cmd` + `shift` + `P` -> Search for and then select “Continue: Enable Console” and enable
3. `cmd` + `shift` + `P` -> Reload the window
4. `cmd` + `shift` + `P` -> Search for  “Continue: Focus on Continue Console View” to Open the Continue Console

### MCP Inspector
MCP Inspector provides an easy way to interact with MCP servers via a Web UI.
You should use the same transports/entry commands for the MCP server as you have configured for the Host you are using.

You can run it via:
```bash
npx @modelcontextprotocol/inspector
```

Alternatively, `fastmcp-util-server` has MCP Inspector support by default, but only over STDIO, which you can access by:
```bash
cd fastmcp-util-server
uv run fastmcp dev main.py:mcp
```

MCP Inspector will open in your browser on http://localhost:6274/ by default.

## Performance
In some situations the following can improve performance.

### Embeddings
continue recommends for Ollama using `nomic-embed-text`,
```bash
  - name: Nomic Embed Text
    provider: ollama
    model: nomic-embed-text
    roles:
      - embed
    apiBase: http://0.0.0.0:11434
```

### Flash Attention
Before launching the Ollama server run:
```bash
export OLLAMA_FLASH_ATTENTION=1
```
This may have been switched on by default depending on your model.
When on, the attention mechanism changes to one which uses less VRAM and is quicker.


### Quantisation
This controls how the context cache is quantised:
- f16 - high precision and memory usage (default).
- q8_0 - 8-bit quantization, uses approximately 1/2 the memory of f16 with a very small loss in precision, this usually has no noticeable impact on the model's quality (recommended if not using f16).
- q4_0 - 4-bit quantization, uses approximately 1/4 the memory of f16 with a small-medium loss in precision that may be more noticeable at higher context sizes.

Quantisation reduces the context cache memory footprint and VRAM usage, enabling larger context usage.
Set this to the type of quantisation you want:
```bash
export OLLAMA_KV_CACHE_TYPE="q8_0"
```
`OLLAMA_FLASH_ATTENTION` must be set.

For more details on when and how you should or should not use quantisation, read this [article](https://smcleod.net/2024/12/bringing-k/v-context-quantisation-to-ollama/), which also has an [interactive vram estimator](https://smcleod.net/2024/12/bringing-k/v-context-quantisation-to-ollama/#interactive-vram-estimator)

### Context Size
Context size, and how much of that context is being used, have a quite a few impacts on performance - both on tokens per second and the content that is generated.

Smaller context size will mean fewer tokens can be processed in a single interaction, which can lead to faster response times but may limit the model's ability to understand longer or more complex conversations. This is particularly important in scenarios where the user expects concise, direct answers rather than nuanced, multi-turn dialogues.

With a larger context size you can process more tokens in a single interaction, which can improve the model's ability to understand and generate more coherent, contextually rich responses but may increase latency and resource usage. This is beneficial for tasks requiring deep reasoning, multi-step problem-solving, or maintaining context across extended interactions, but may not be optimal for real-time or low-latency applications.

You should consider the following when deciding on context size:
- **Available VRAM**: Larger context sizes require more memory, so ensure your system can handle the chosen model's requirements.
- **Use Case**: Prioritize speed for rapid, straightforward queries or richer context for complex tasks.
- **Quantization**: Pair larger context sizes with lower-precision quantization (e.g., q4_0) to balance performance and resource constraints.
- **Model Capabilities**: Some models are optimized for specific context lengths; consult the model's documentation for recommended settings.
- **User Experience**: Balance response quality with interaction speed based on your application's goals.

By carefully tuning context size alongside quantization and flash attention settings, you can optimize both performance and output quality for your specific workload.

---
https://docs.continue.dev/guides/cli 👀
---

Need help before we start? Reach out on gchat to me.
