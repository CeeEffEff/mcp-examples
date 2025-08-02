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
brew install astral-sh/uv/uv
```

Once the repo is cloned, for each service check the relevant README.md to see service specific setup.

---

### ✅ 3. VS Code + Extensions

Please install the following extensions:

- [Continue](https://marketplace.visualstudio.com/items?itemName=Continue.continue) – highly configurable Agent interface
- [Cline](https://marketplace.visualstudio.com/items?itemName=clineb.cline) – Heavy duty task and workflow agent interface
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

Please download the models below **before** the session — they are large and may take time:

```bash
ollama pull qwen3:8b
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5-coder:7b
```

This is based on having 18GB of unified memory - if you have less you will need to scale down.
Make sure you have qwen3 and at least one other model.

## 📂 What’s in This Repo

Once cloned, this repo will include at the root:

- **Directories**:
  - `agent-cli/`: Command-line interface tools for interacting with the agent.
  - `agent-web-interface/`: Web-based interface or API for managing the agent.
  - `fastmcp-util-server/`: Backend server for utility functions related to fastmcp.
  - `mcp-sentiment-server/`: Server for sentiment analysis or machine learning tasks (MCP).
  - `.continue/`: Configuration directory for the continue extension, defining MCP Components
  - `.taskmaster/`: Taskmaster-ai workspace for managing tasks and workflows.
  - `.cursor/`: Likely related to code navigation or UI components (e.g., cursor-based tools).
  - `.clinerrules/`: Configuration directory for cline rules (code formatting/linting).

- **Configuration Files**:
  - `.env.example`: Sample environment variables for development setup.
  - `docker-compose.yml`: Docker configuration for containerized services (not complete).

- **Documentation**:
  - `README.md`: This file (current location).
  - `gotchas.md`: Notes on common pitfalls, setup issues, or best practices.

- **Other Files**:
  - `memory.jsonl`: Stores memory data for @modelcontextprotocol/server-memory (can be configured)
  - `.clineignore`: File specifying files to ignore for cline tools.

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

### VS Code Developer Console
Almost all interactions will be viewable via the Developer Console.
In order to view debug logs, which contain extra information, click the dropdown at the top that says “Default levels” and select “Verbose”.
To enable:
1. `cmd` + `shift` + `P`
2. Search for and then select “Developer: Toggle Developer Tools”
3. Select the Console tab
4. Click the dropdown at the top that says “Default levels” and select “Verbose”.
5. Read the console logs

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

Alternatively, `fastmcp-util-server` has MCP Inspector support by default which you can access by:
```bash
cd fastmcp-util-server
uv run fastmcp dev main.py:mcp --transport http
```

MCP Inspector will open in your browser on http://localhost:6274/ by default.

---

Need help before we start? Reach out on gchat to me.
