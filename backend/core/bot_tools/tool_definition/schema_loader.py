import json
from pathlib import Path
from typing import Any, Dict


def _tool_definition_dir() -> Path:
    # Directory of this file (tool_definition)
    return Path(__file__).parent


def load_tool_parameters(file_name: str) -> Dict[str, Any]:
    """Load and return the `function.parameters` object from a tool-definition JSON file.

    Args:
        file_name: name of the json file (e.g. 'rag_tool.json') inside this folder.

    Returns:
        The parameters dict (or empty dict if not found).
    """
    path = _tool_definition_dir() / file_name
    if not path.exists():
        raise FileNotFoundError(f"Tool definition file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    params = data.get("function", {}).get("parameters")
    if not params:
        raise ValueError(f"Missing 'function.parameters' in tool definition: {path}")

    return params
