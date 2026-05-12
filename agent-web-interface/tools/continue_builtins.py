import os
import subprocess
import glob
from typing import Optional, Dict, List, Union
from smolagents.tools import Tool, tool
import re

ROOT_DIR = "/Users/conor.fehilly/Documents/repos/mcp-examples/"
TASKMASTER_DIR = ROOT_DIR + ".taskmaster/"
CONTINUE_DIR = ROOT_DIR + ".continue/"


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
            print(f"Grepping {query}...")
            result = subprocess.run(
                ["rg", "--files", "--color=never", query],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"Grep returned {len(result.stdout.splitlines())} results.")
            return result.stdout.splitlines()
        except subprocess.CalledProcessError as e:
            print(f"Exception on grep: {e}")
            return []


class FileGlobSearch(Tool):
    name = "file_glob_search"
    description = "Search for files using glob patterns."
    inputs = {
        "pattern": {
            "type": "string",
            "description": "The pattern may contain simple shell-style wildcards a la fnmatch. Unlike fnmatch, filenames starting with a dot are special cases that are not matched by '*' and '?' patterns by default.",
        },
        "root_dir": {
            "type": "string",
            "nullable": True,
            "description": "The pattern may contain simple shell-style wildcards a la fnmatch. Unlike fnmatch, filenames starting with a dot are special cases that are not matched by '*' and '?' patterns by default.",
        },
        "recursive": {
            "type": "boolean",
            "description": "Whether to search recursively (use with caution)",
        },
    }
    output_type = "array"

    def __init__(self):
        self.is_initialized = True

    def forward(
        self, pattern: str, recursive: bool, root_dir: Optional[str] = None
    ) -> List[str]:
        """Search for files using glob patterns."""
        try:
            return glob.glob(pattern, root_dir=root_dir, recursive=recursive)
        except Exception as e:
            print(e)


class LSTool(Tool):
    name = "ls_tool"
    description = "List the first 20 files and folders in a directory. Use offset to get the next 20 files. Before doing a recursive ls it is wise to do a non-recursive ls as there may be directories you want to avoid, e.g. .venv directories."
    inputs = {
        "dir_path": {
            "type": "string",
            "nullable": True,
            "description": "Directory path",
        },
        "recursive": {
            "type": "boolean",
            "nullable": True,
            "description": "Whether to list recursively. Use with caution.",
        },
        "ignore": {
            "type": "array",
            "nullable": True,
            "description": "List of strings. If any paths contain any of these strings as a substring, they will not be returned.",
        },
        "offset": {
            "type": "integer",
            "nullable": True,
            "description": "Offset for the starting index for the selection of the 20 items.",
        },
    }
    output_type = "array"

    def __init__(self):
        self.is_initialized = True

    def forward(
        self,
        dir_path: Optional[str] = None,
        recursive: bool = False,
        ignore: Optional[List[str]] = None,
        offset: Optional[int] = None,
    ) -> List[str]:
        """Lists the first 20 files and folders in a directory."""
        path = ResolveLSToolDirPath().forward(dir_path)
        if recursive:
            result = [
                os.path.join(root, f)
                for root, _, files in os.walk(path)
                for f in files
                if not ignore or all(i not in os.path.join(root, f) for i in ignore)
            ]
        else:
            result = [
                f
                for f in os.listdir(path)
                if not ignore or all(i not in f for i in ignore)
            ]
        print(f"LS found {len(result)} items.")
        if len(result) > 20:
            print(
                f"Number of results too large to display. Limiting LS results to the first 20 item after the offset of {offset}. Consider ignoring any files you've already processed, or setting the offset, to get the rest."
            )
        if not offset:
            offset = 0
        elif offset < 0:
            offset = 0
        result = result[offset : 20 + offset]
        print(result)
        return result


class ReadFile(Tool):
    name = "read_file"
    description = """
    Reads a chunk of the contents of a file at the given filepath.
    Contents are split into chunks of lines (max 20 lines). USE INSTEAD OF OPEN READ.
    Returned object is a `ReadFileResult` object with the following attributes:
    - chunk_contents (str): the read contents for the chunk
    - chunk_id (int): ID (index) of the chunk (1 based)
    - total_chunks (int): The total number of chunks available
    """

    inputs = {
        "filepath": {"type": "string", "description": "Filepath of file to read."},
        # "as_lines": {
        #     "type": "boolean",
        #     "nullable": True,
        #     "description": "If true, list of strings will be returned with one strig per line (safer for large files).",
        # },
        "chunk_index": {
            "type": "integer",
            "default": 1,
            "nullable": True,
            "description": "The index of the chunk of the file contents to return. 1 based index.",
        },
    }
    output_type = "object"

    class ReadFileResult:
        def __init__(self, chunk_contents, chunk_id, total_chunks):
            self.chunk_contents, self.chunk_id, self.total_chunks = (
                chunk_contents,
                chunk_id,
                total_chunks,
            )

    CHUNK_SIZE = 20

    def __init__(self):
        self.is_initialized = True

    def forward(self, filepath: str, chunk_index: int = 1) -> str:
        """Reads a chunk of the contents of a file at the given filepath."""
        print(f"Reading {filepath=}...")
        try:
            with open(filepath, "r") as file:
                lines = file.readlines()
                num_lines = len(lines)
                num_chunks = num_lines / self.CHUNK_SIZE
                num_chunks = int(num_chunks) + int(not num_chunks.is_integer())
                print(f"Read {filepath=}: {num_lines=} {num_chunks=}.")

                if chunk_index >= num_chunks:
                    raise ValueError(
                        f"Chunk {chunk_index} outside of range {num_chunks}."
                    )
                chunk = lines[chunk_index - 1 : chunk_index - 1 + self.CHUNK_SIZE]
                print(f"Chunk {chunk_index} has {len(chunk)} lines.")
                return self.ReadFileResult(chunk, chunk_index, num_chunks)
        except FileNotFoundError:
            raise Exception(f"File not found: {filepath}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")


class WriteFileToContinueDir(Tool):
    name = "write_file_to_continue_dir"
    description = f"Writes the contents of a file to `{CONTINUE_DIR}<filepath>`. USE INSTEAD OF OPEN WRITE.  Any directorys will be created as needed if they don't exist."
    inputs = {
        "filepath": {
            "type": "string",
            "description": "Filepath within the directory to write to.",
        },
        "contents": {
            "type": "string",
            "description": "string content to write to the file",
        },
    }
    output_type = "string"

    def __init__(self):
        self.is_initialized = True

    def forward(self, filepath: str, contents: str) -> str:
        f"""
        Writes the contents to a file at `{CONTINUE_DIR}<filepath>`.
        Will overwrite any existing file so use with caution.
        """
        filepath = filepath.removeprefix(CONTINUE_DIR)
        if ".taskmaster" in filepath:
            raise ValueError(
                f"Nested `.taskmaster` of {filepath=} is forbidden within `{CONTINUE_DIR}`: "
            )
        if ".continue" in filepath:
            raise ValueError(
                f"Nested `.continue` of {filepath=} is forbidden within `{CONTINUE_DIR}`"
            )
        filepath = os.path.join(CONTINUE_DIR, filepath)
        try:
            os.makedirs("/".join(filepath.split("/")[0:-1]), exist_ok=True)
            with open(filepath, "w") as file:
                # if isinstance(contents, List[str]):
                #     file.writelines(contents)
                # else:
                file.write(contents)
            return f"Succesfully wrote to {filepath}"
        except Exception as e:
            raise Exception(f"Error writing {filepath}: {str(e)}")


class WriteFileToTaskMasterDir(Tool):
    name = "write_file_to_taskmaster_dir"
    description = f"Writes the contents of a file to `{TASKMASTER_DIR}<filepath>`. USE INSTEAD OF OPEN WRITE. Any directorys will be created as needed if they don't exist."
    inputs = {
        "filepath": {
            "type": "string",
            "description": "Filepath within the directory to write to.",
        },
        "contents": {
            "type": "string",
            "description": "string content to write to the file",
        },
    }
    output_type = "string"

    def __init__(self):
        self.is_initialized = True

    def forward(self, filepath: str, contents: str) -> str:
        f"""
        Writes the contents to a file at `{TASKMASTER_DIR}<filepath>`.
        Will overwrite any existing file so use with caution.
        """
        filepath = filepath.removeprefix(TASKMASTER_DIR)
        if ".taskmaster" in filepath:
            raise ValueError(
                f"Nested `.taskmaster` of {filepath=} is forbidden within `{TASKMASTER_DIR}`: "
            )
        if ".continue" in filepath:
            raise ValueError(
                f"Nested `.continue` of {filepath=} is forbidden within `{TASKMASTER_DIR}`"
            )
        filepath = os.path.join(TASKMASTER_DIR, filepath)
        try:
            os.makedirs("/".join(filepath.split("/")[0:-1]), exist_ok=True)
            with open(filepath, "w") as file:
                # if isinstance(contents, List[str]):
                #     file.writelines(contents)
                # else:
                file.write(contents)
            print(f"Succesfully wrote to {filepath}")
            return f"Succesfully wrote to {filepath}"
        except Exception as e:
            raise Exception(f"Error writing {filepath}: {str(e)}")


@tool
def filter_for_suffix(list_items: List[str], suffix: str) -> List[str]:
    """
    Filters a list of strings, returning only those that have the given suffix.

    For example:
    ```
    filter_for_suffix(["test_one", "a_best/cat", "test_cat"], "cat")
    ```
    Would return:
    ```
    ["a_best/cat", "test_cat"]
    ```

    Args:
        list_items (List[str]): The list of strings to filter.
        suffix (str): Suffix to filter the items on.

    Returns:
        List[str]: A list containing only the items from `list_items` that have the suffix `suffix`.
    """
    results = [item for item in list_items if item.endswith(suffix)]
    print(f"list_items with suffix `{suffix}`: `{results}`")
    return results


@tool
def get_number_of_files(dir_path: str, suffix: str) -> str:
    """
    Returns the number of files in the given directory that have
    the specified suffix - suffix is intereted as-is, e.g. no wildcards.

    Args:
        dir_path (str): The directory path to search.
        suffix (str): The file suffix to filter by.

    Returns:
        str: The number of files with the specified suffix in the directory.
    """
    files = LSTool().forward(ResolveLSToolDirPath().forward(dir_path), False)
    msg = f"There are {len([item for item in files if item.endswith(suffix)])} in {dir_path} with suffix {suffix}"
    print(msg)
    return msg


@tool
def read_files(dir_path: str, index: int, suffix: str) -> Dict:
    """
    Reads a specific file from a directory based on suffix and index.

    Returns a dictionary containing:
    - Directory: Original directory path
    - Suffix: Filtered file suffix
    - Total Files: Count of matching files
    - Index {index} filename: Full path of the selected file
    - Index {index} content: File contents as a string

    Args:
        dir_path (str): Directory path to search
        index (int): Zero-based index of the file to retrieve
        suffix (str): File suffix filter (no wildcards)

    Note: The suffix is treated as an exact match, not a pattern.
    """
    dir_path = ResolveLSToolDirPath().forward(dir_path)
    files = LSTool().forward(dir_path, False)
    files = [item for item in files if item.endswith(suffix)]
    print(f"There are {len(files)} in {dir_path} with suffix {suffix}")
    file_path = os.path.join(dir_path, files[index])
    content = ReadFile().forward(file_path)
    msg = {
        "Directory": dir_path,
        "Suffix": suffix,
        "Total Files": f"{len(files)}",
        f"Index {index} filename": file_path,
        f"Index {index} content": content,
    }
    print(msg)
    return msg


@tool
def write_converted_file(original_ts_filename: str, python_coversion: str) -> Dict:
    """
    Writes the converted Python code to a file. USE INSTEAD OF OPEN WRITE.

    Args:
        original_ts_filename (str): The name of the original TypeScript file.
        python_coversion (str): The converted Python code.

    Returns:
        Dict: A dictionary containing the status message and the path to the saved Python file.
    """
    dir_path = ResolveLSToolDirPath().forward(
        "/Users/conor.fehilly/Documents/repos/mcp-examples/agent-web-interface/tools"
    )
    py_filename = f"{os.path.splitext(os.path.basename(original_ts_filename))[0]}.py"
    filepath = os.path.join(dir_path, py_filename)

    with open(filepath, "w") as file:
        file.write(python_coversion)

    msg = {
        "status": "success",
        "message": f"Python code written to {filepath}",
        "file_path": filepath,
    }
    print(msg)
    return msg


def initialize_tools() -> Dict[str, Tool]:
    """Initialize and return all tools."""
    tools = {
        "split_grep_results_by_file": SplitGrepResultsByFile(),
        "resolve_ls_tool_dir_path": ResolveLSToolDirPath(),
        "grep_search": GrepSearch(),
        "file_glob_search": FileGlobSearch(),
        "ls_tool": LSTool(),
        "read_file": ReadFile(),
        "filter_for_suffix": filter_for_suffix,
    }
    return tools
