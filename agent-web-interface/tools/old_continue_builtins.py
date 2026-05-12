# py_tools.py
import os
import re
import subprocess
import glob
import requests
from typing import Optional, Dict, List, Any
from difflib import unified_diff


class ToolImplementations:
    @staticmethod
    def split_grep_results_by_file(content: str) -> Dict[str, List[str]]:
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

    @staticmethod
    def resolve_ls_tool_dir_path(dir_path: Optional[str]) -> str:
        """Resolve directory path for ls tool."""
        if not dir_path:
            return os.getcwd()
        return os.path.abspath(dir_path)

    @staticmethod
    def throw_if_file_exceeds_half_of_context(
        filepath: str, content: str, model: Optional[Any] = None
    ) -> None:
        """Check if file content exceeds half of model context."""
        if model and len(content) > model.max_context_length / 2:
            raise ValueError(f"File {filepath} exceeds half of model context length")

    @staticmethod
    def get_decoded_output(data: bytes) -> str:
        """Decode buffer according to platform encoding."""
        return data.decode("utf-8")

    @staticmethod
    def edit_existing_file(filepath: str, changes: str) -> None:
        """Edit an existing file with the provided changes."""
        if not os.path.isfile(filepath):
            raise FileNotFoundError()
        with open(filepath, "w") as f:
            f.write(changes)

    @staticmethod
    def search_and_replace_in_file(
        filepath: str,
        search: str,
        replace: str,
        case_sensitive: bool = True,
        whole_words: bool = False,
    ) -> None:
        """Perform a search and replace in the specified file."""

        with open(filepath, "r") as f:
            content = f.read()

        if not case_sensitive:
            search = search.lower()
            content = content.lower()

        if whole_words:
            # Use regex to match whole words
            pattern = r"\b" + re.escape(search) + r"\b"
            content = re.sub(pattern, replace, content)
        else:
            content = content.replace(search, replace)

        with open(filepath, "w") as f:
            f.write(content)

    @staticmethod
    def create_new_file(filepath: str, contents: str) -> None:
        """Create a new file with specified contents."""
        os.makedirs(os.path.dirname(filepath), exist_ok=False)
        with open(filepath, "w") as f:
            f.write(contents)

    @staticmethod
    def run_terminal_command(
        command: str, wait_for_completion: bool = True
    ) -> Optional[str]:
        """Run a terminal command."""
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if wait_for_completion:
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise RuntimeError(f"Command failed: {command}\nError: {stderr}")
            return stdout
        return None

    @staticmethod
    def grep_search(query: str) -> List[str]:
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

    @staticmethod
    def file_glob_search(pattern: str) -> List[str]:
        """Search for files using glob patterns."""
        return glob.glob(pattern, recursive=True)

    @staticmethod
    def search_web(query: str) -> List[Dict[str, str]]:
        """Perform a web search."""
        try:
            response = requests.get(f"https://api.example.com/search?q={query}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

    @staticmethod
    def ls_tool(dir_path: Optional[str] = None, recursive: bool = False) -> List[str]:
        """List files and folders in a directory."""
        path = ToolImplementations.resolve_ls_tool_dir_path(dir_path)
        if recursive:
            return [
                os.path.join(root, f) for root, _, files in os.walk(path) for f in files
            ]
        return os.listdir(path)

    @staticmethod
    def create_rule_block(rule: Dict[str, Any]) -> None:
        """Create a new rule block."""
        # Implementation depends on specific rule format
        pass

    @staticmethod
    def request_rule(rule_id: str) -> Dict[str, Any]:
        """Request a specific rule."""
        # Implementation depends on rule storage system
        return {}

    @staticmethod
    def fetch_url_content(url: str) -> str:
        """Fetch content from a URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error fetching URL: {str(e)}"

    @staticmethod
    def codebase_tool(query: str) -> Dict[str, Any]:
        """Handle codebase-level operations."""
        # Implementation depends on specific codebase structure
        return {}

    @staticmethod
    def view_diff(filepath: str, original: str, modified: str) -> str:
        """Generate a diff between two files."""
        return "\n".join(
            unified_diff(
                original.splitlines(),
                modified.splitlines(),
                fromfile=filepath,
                tofile=filepath,
            )
        )

    @staticmethod
    def read_file(filepath: str) -> str:
        """Reads the contents of a file at the given filepath."""
        try:
            with open(filepath, "r") as file:
                return file.read()
        except FileNotFoundError:
            raise Exception(f"File not found: {filepath}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
