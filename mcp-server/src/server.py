"""Read-only MCP server that supplies approved project guidance documents."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_VERSION = "2024-11-05"
DOCUMENTS = {
    "project-instructions": "AGENTS.md",
    "workflow": "_docs/process.md",
    "permissions": "docs/permissions.md",
    "ai-tool-data-policy": "docs/ai-tool-data-policy.md",
}


def result(request_id: Any, payload: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "get_project_guidance",
            "description": "Read one preapproved, non-secret project guidance document.",
            "inputSchema": {
                "type": "object",
                "properties": {"document": {"type": "string", "enum": sorted(DOCUMENTS)}},
                "required": ["document"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "destructiveHint": False},
        }
    ]


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return None
    if method == "initialize":
        requested = message.get("params", {}).get("protocolVersion", PROTOCOL_VERSION)
        return result(
            request_id,
            {
                "protocolVersion": requested,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "weekly-growth-project-context", "version": "1.0.0"},
                "instructions": "Read-only server for the fixed guidance documents in its tool schema.",
            },
        )
    if method == "ping":
        return result(request_id, {})
    if method == "tools/list":
        return result(request_id, {"tools": list_tools()})
    if method == "tools/call":
        params = message.get("params", {})
        if params.get("name") != "get_project_guidance":
            return error(request_id, -32602, "Unknown tool")
        document = params.get("arguments", {}).get("document")
        if document not in DOCUMENTS:
            return error(request_id, -32602, "Choose a document listed in the tool schema")
        text = (ROOT / DOCUMENTS[document]).read_text(encoding="utf-8")
        return result(request_id, {"content": [{"type": "text", "text": text}], "isError": False})
    return error(request_id, -32601, "Method not found")


def main() -> None:
    for line in sys.stdin:
        try:
            response = handle(json.loads(line))
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            response = error(None, -32603, f"Request could not be handled: {type(exc).__name__}")
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
