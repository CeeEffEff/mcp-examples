from smolagents.tools import tool


def create_function():
    """
    Creates a synchronous version of the original asynchronous function.

    Returns:
        function: The converted synchronous function.
    """

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
                "embeddings_provider": extras["config"]
                .get("selected_model_by_role")
                .get("embed"),
                "reranker": extras["config"]
                .get("selected_model_by_role")
                .get("rerank"),
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
                        content=f"""No relevant code found for query: "{query}". This could mean:
- The codebase hasn't been indexed yet
- No code matches the search criteria
- Embeddings provider is not configured
Try re-indexing the codebase or using a more specific query.""",
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
