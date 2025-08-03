import aiofiles
import json
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.resources import FileResource
from pathlib import Path

mcp = FastMCP("LocalUtil")

# TODO thos won't work with docker
CODEBASE_MEMORY_PATH = "/Users/conor.fehilly/Documents/repos/mcp-examples/.continue/data_stores/server-memory/memory.jsonl"
GOTCHAS_PATH = "/Users/conor.fehilly/Documents/repos/mcp-examples/GOTCHAS.md"


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
    with open(CODEBASE_MEMORY_PATH, "r") as f:
        for line in f:
            try:
                json.loads(line)  # Try parsing each line as a JSON object
                keep_lines.append(line)  # If successful, add to keep list
            except json.JSONDecodeError:
                error_lines.append(line)  # If not successful, add to error list

    # Overwrite the memory.jsonl file with only valid lines
    with open(CODEBASE_MEMORY_PATH, "w") as f:
        for line in keep_lines:
            f.write(line)

    result = {"valid_lines": len(keep_lines), "invalid_lines": len(error_lines), "error_lines": error_lines}
    return json.dumps(result)


# TODO tools that get past developer events
@mcp.tool()
def get_past_events(max_lines):
    pass


# Decorator style async resource
@mcp.resource("resource://GOTCHAS_DEC", mime_type="text/markdown")
async def get_gotchas() -> str:
    try:
        async with aiofiles.open(GOTCHAS_PATH, mode="r") as f:
            content = await f.read()
        return content
    except FileNotFoundError:
        return "GOTCHAS file was not fond"


# Function style Model based resource
gotchas_path = Path(GOTCHAS_PATH).resolve()
if gotchas_path.exists():
    # Use a file:// URI scheme
    readme_resource = FileResource(
        uri="resource://GOTCHAS_FN",
        # f"file://{gotchas_path.as_posix()}",
        path=gotchas_path,  # Path to the actual file
        name="GOTCHAS File",
        description="Some GOTCHAS.",
        mime_type="text/markdown",
        tags={"documentation"},
    )
    mcp.add_resource(readme_resource)
