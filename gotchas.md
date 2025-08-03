# Common GOTCHAS and Best Practices

This document outlines common pitfalls and recommendations when working with agent systems, LLMs, and related tools. Proper attention to these details can significantly improve reliability and performance.

---

## Task Management

- **Background Processes**: Cancelling a task or ending a chat session may not stop background processes. Always:
  - Terminate the Ollama service (`ollama stop` or `kill -9 <pid>`)
  - Manually kill lingering processes using `ps aux | grep ollama`

- **Model Tool Integration**: Some models require explicit configuration to use tools:
  - Qwen 2.3/3 works well with agent mode in most extensions
  - Continue integration may require special flags
  - Verify tool compatibility with your specific model version

---

## Model-Specific Considerations

- **Context Window Limits**:
  - Ollama defaults to 4096 tokens (may override local settings)
  - Monitor system activity for crashes related to memory/RAM usage
  - Close unused applications to free system resources

- **Prompt Engineering**:
  - Markdown formatting works well with Qwen3
  - Avoid excessive auto-applied rules that bloat the system prompt
  - Test prompt complexity with smaller context windows first

- **Model Behavior**:
  - Qwen2.5 may enter analysis loops (look for "wait" in logs)
  - Use premium models with Cline for complex tasks
  - Local models may require frequent task resets due to context limits

---

## Context Management

- **Project Indexing**:
  - Use Continue to index projects for better reference capabilities
  - Reindex manually if seeing outdated file references
  - Large repositories may impact performance - test with subsets

- **Offline Memory**:
  - Implement document generation strategies for persistent knowledge
  - Use proper storage paths for MCP server-memory (avoid default locations)
  - Backup storage files regularly to prevent data corruption

---

## Technical GOTCHAS

- **JSON Handling**:
  - Be cautious with JSON escaping - even properly escaped values can cause downstream issues
  - Validate JSON outputs with schema checks when possible

- **Token Limits**:
  - Agents may appear unresponsive due to hitting token limits
  - Monitor token usage in logs and adjust prompt complexity accordingly

- **Storage Management**:
  - Overwrite default storage paths for MCP server-memory
  - Regularly verify storage file integrity

---

## Contributing to This Document

This is a living document. Please add your own observations or clarify any points that need better explanation. Proper documentation of edge cases helps the community avoid common pitfalls.
