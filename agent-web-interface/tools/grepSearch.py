
from typing import List, Optional
import re

def split_grep_results_by_file(content: str) -> List[dict]:
    matches = list(re.finditer(r'^\.\/([^
]+)$', content, re.MULTILINE))

    if not matches:
        return []

    context_items = []

    for i in range(len(matches)):
        match = matches[i]
        filepath = match.group(1)
        start_index = match.start()
        end_index = (matches[i + 1].start() if i < len(matches) - 1 else len(content))

        file_content = content[start_index:end_index].replace(r'^\.\/[^
]+\n', "").strip()

        if file_content:
            context_items.append({
                "name": f"Search results in {filepath}",
                "description": f"Grep search results from {filepath}",
                "content": file_content,
                "uri": {{"type": "file", "value": filepath}},
            })

    return context_items

async def grep_search_impl(args: dict, extras: dict) -> List[dict]:
    query = args.get("query")
    
    results = await extras["ide"].get_search_results(query, 100)
    formatted, num_results, truncated = format_grep_search_results(results, 5000)
    truncation_reasons = []
    if num_results == 100:
        truncation_reasons.append("the number of results exceeded 100")
    if truncated:
        truncation_reasons.append("the number of characters exceeded 5000")

    context_items = []

    split_by_file = args.get("splitByFile", False)
    if split_by_file:
        context_items = split_grep_results_by_file(formatted)
    else:
        context_items = [
            {
                "name": "Search results",
                "description": "Results from grep search",
                "content": formatted,
            }
        ]

    if truncation_reasons:
        context_items.append({
            "name": "Search truncation warning",
            "description": "Informs the model that search results were truncated",
            "content": f"The above search results were truncated because {', '.join(truncation_reasons)}. If the results are not satisfactory, try refining your search query.",
        })

    return context_items
