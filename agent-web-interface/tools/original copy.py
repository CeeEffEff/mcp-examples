from . import ToolImpl
import { RangeInFile } from "../../";
import { retrieveContextItemsFromEmbeddings } from "../../context/retrieval/retrieval";
import { getStringArg } from "../parseArgs";

async def codebaseToolImpl(args, extras):
  query = getStringArg(args, "query")

  try:
    contextExtras = {
      "config": extras.config,
      "fullInput": query,
      "embeddingsProvider": extras.config.selectedModelByRole.embed,
      "reranker": extras.config.selectedModelByRole.rerank,
      "llm": extras.llm,
      "ide": extras.ide,
      "selectedCode": [] as RangeInFile[],
      "fetch": extras.fetch,
      "isInAgentMode": True, # always true in tool call
    }

    results = await retrieveContextItemsFromEmbeddings(
      contextExtras,
      None,
      None,
    )

    if len(results) == 0:
      return [
        {
          "name": "No Results",
          "description": "Codebase search",
          "content": "No relevant code found for query: \"{query}\". This could mean:\n- The codebase hasn't been indexed yet\n- No code matches the search criteria\n- Embeddings provider is not configured\n
Try re-indexing the codebase or using a more specific query."
        },
      ]
    }

    return results
  except Exception as e:
    return [
      {
        "name": "Error",
        "description": "Codebase search error",
        "content": f"Failed to search codebase: {str(e)}"
      },
    ]
