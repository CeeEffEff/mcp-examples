from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("LocalUtil")


@mcp.tool()
def fix_codebase_memory() -> str:
    """
    Fix Codebase Memory by removing corrupted entries.
    If you are getting errors when using Codebase Memory that aren't becuause of invalid input,
    you can try to fix the memory via this method.
    A good example is if the read_graph tool as it takes no arguments.
    Any invalid entries will be returned in case you would like to try and fix them.
    """
    error_lines = []
    keep_lines = []
    with open("../memory.jsonl", "r") as f:
        for line in f:
            try:
                json.loads(line)  # Try parsing each line as a JSON object
                keep_lines.append(line)  # If successful, add to keep list
            except json.JSONDecodeError:
                error_lines.append(line)  # If not successful, add to error list

    # Overwrite the memory.jsonl file with only valid lines
    with open("../memory.jsonl", "w") as f:
        for line in keep_lines:
            f.write(line)

    result = {"valid_lines": len(keep_lines), "invalid_lines": len(error_lines), "error_lines": error_lines}
    return json.dumps(result)
