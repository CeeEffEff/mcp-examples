import os
import subprocess
import glob
from typing import Optional, Dict, List
from smolagents.tools import Tool, tool
import re


class SplitGrepResultsByFile(Tool):
    name = "split_grep_results_by_file"
    description = "Split grep results by file path."
    inputs = {"content": {"type": "string", "description": "Content of grep results"}}
    output_type = "object"

    def __init__(self):
        self.is_initialized = True

    def forward(self, content: str) -> Dict[str, List[str]]:
        """Split grep results by file path."""
        results = {}
        current_file = None
        lines = content.splitlines()

        for line in lines:
            if line.startswith("----"):
                current_file = line.replace("----", "").strip()
                results[current_file] = []
            elif current_file and line:
                results[current_file].append(line)

        return results


class ResolveLSToolDirPath(Tool):
    name = "resolve_ls_tool_dir_path"
    description = "Resolve directory path for ls tool."
    inputs = {
        "dir_path": {
            "type": "string",
            "nullable": True,
            "description": "Directory path",
        }
    }
    output_type = "string"

    def __init__(self):
        self.is_initialized = True

    def forward(self, dir_path: Optional[str]) -> str:
        """Resolve directory path for ls tool."""
        if not dir_path:
            return os.getcwd()
        return os.path.abspath(dir_path)


class GrepSearch(Tool):
    name = "grep_search"
    description = "Perform a grep search using ripgrep."
    inputs = {"query": {"type": "string", "description": "Search query"}}
    output_type = "array"

    def __init__(self):
        self.is_initialized = True

    def forward(self, query: str) -> List[str]:
        """Perform a grep search using ripgrep."""
        try:
            result = subprocess.run(
                ["rg", "--files", "--color=never", query],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.splitlines()
        except subprocess.CalledProcessError as e:
            return []


class FileGlobSearch(Tool):
    name = "file_glob_search"
    description = "Search for files using glob patterns."
    inputs = {"pattern": {"type": "string", "description": "Glob pattern"}}
    output_type = "array"

    def __init__(self):
        self.is_initialized = True

    def forward(self, pattern: str) -> List[str]:
        """Search for files using glob patterns."""
        return glob.glob(pattern, recursive=True)


class LSTool(Tool):
    name = "ls_tool"
    description = "List files and folders in a directory."
    inputs = {
        "dir_path": {
            "type": "string",
            "nullable": True,
            "description": "Directory path",
        },
        "recursive": {
            "type": "boolean",
            "nullable": True,
            "description": "Whether to list recursively",
        },
    }
    output_type = "array"

    def __init__(self):
        self.is_initialized = True

    def forward(
        self, dir_path: Optional[str] = None, recursive: bool = False
    ) -> List[str]:
        """List files and folders in a directory."""
        path = ResolveLSToolDirPath().forward(dir_path)
        if recursive:
            return [
                os.path.join(root, f) for root, _, files in os.walk(path) for f in files
            ]
        return os.listdir(path)


class ReadFile(Tool):
    name = "read_file"
    description = "Reads the contents of a file at the given filepath."
    inputs = {"filepath": {"type": "string", "description": "Filepath"}}
    output_type = "string"

    def __init__(self):
        self.is_initialized = True

    def forward(self, filepath: str) -> str:
        """Reads the contents of a file at the given filepath."""
        try:
            with open(filepath, "r") as file:
                return file.read()
        except FileNotFoundError:
            raise Exception(f"File not found: {filepath}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")


@tool
def filter_list(list_items: List[str], regex: str) -> List[str]:
    """
    Filters a list of strings, returning only those that match a given regular expression.

    Args:
        list_items (List[str]): The list of strings to filter.
        regex (str): The regular expression pattern to match against each string in the list.

    Returns:
        List[str]: A list containing only the items from `list_items` that match `regex`.
    """
    compiled_regex = re.compile(regex)
    return [item for item in list_items if compiled_regex.match(item)]


def initialize_tools() -> Dict[str, Tool]:
    """Initialize and return all tools."""
    tools = {
        "split_grep_results_by_file": SplitGrepResultsByFile(),
        "resolve_ls_tool_dir_path": ResolveLSToolDirPath(),
        "grep_search": GrepSearch(),
        "file_glob_search": FileGlobSearch(),
        "ls_tool": LSTool(),
        "read_file": ReadFile(),
        "filter_list": filter_list,
    }
    return tools
