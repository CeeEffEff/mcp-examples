If you cancel a task or chat the process may still run in the background
Kill ollama or kill the process.

Ollama models sometimes need to be explicitly marked as being able to use tools - for example with Continue.
Even then, not all integrations are uptodate.

qwen (2.3 and 3) is an opensource model that does work with agent mode in most extensions.

Model context window size or parameter size is one of the most likely reasons for you to not seem to get responses - check out Activity monitor should see crashes if so and reduce appropriately.
You can also stop other programs on your system that might be using up RAM.

Prompts that use markdown seem effective on qwen3.

Auto applied rules can massively inflate the system prompt hogging context.

Context management, document generation and "offline" memory are important concepts.

Continue can index the project, allowing parts of it to be referenced and mapped to the important snippits.

If the index is out-of-date you might see generations based off of old/deleted files - manually reindex.

Anecdotally, the index for a large repository can impact performance - this should be tested.

Rules that force agents to ask clarifying questions are very important. For example, Qwen2.5 can easily get stuck in loops due to how it scrutinises itselfs - look for "wait" in the logs for a chuckle.

Cline requires frequent task resets with local models do context size being limited by your machine and cline using large complex prompts. You might want to use premium models with Cline, so really understand if the task you have is requiring it.

Agent thinking but then not performing any action - seems like it doesn't want to use tools - actually may be hitting token limits - the default are quite low.

MCP server-memory - you should overwrite the storage path. My data got corrupts and I couldn't locate the file

Be careful when requesting json escaping as this can cause issues later on even if the value is escaped correctly by the agent.
