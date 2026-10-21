"""JSON tool contracts and strict validation, without runtime dependencies."""

from copy import deepcopy
import re
from typing import Any, TypedDict


class Request(TypedDict):
    tool: str
    arguments: dict[str, Any]


class Result(TypedDict):
    ok: bool
    code: str
    data: dict[str, Any]


def success(**data: Any) -> Result:
    return {"ok": True, "code": "ok", "data": data}


def failure(code: str, reason: str) -> Result:
    return {"ok": False, "code": code, "data": {"reason": reason}}


LITERAL_PATTERN = r"~?[A-Za-z][A-Za-z0-9_]{0,63}"


def valid_literal(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(LITERAL_PATTERN, value) is not None


def _object(properties: dict) -> dict:
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


_DIGIT = {"type": "integer", "minimum": 1, "maximum": 9}
# Ollama requires ordinary anchors. Its character grammar excludes newlines;
# JSON Schema validators also need to exclude a final newline explicitly.
_LITERAL = {"type": "string", "pattern": "^" + LITERAL_PATTERN + "$",
            "not": {"pattern": r"^[\s\S]*\n$"}}
_ARGUMENTS = {
    "inspect": {"oneOf": [
        _object({"scope": {"const": "board"}}),
        _object({"scope": {"const": "cell"}, "row": _DIGIT, "col": _DIGIT}),
        _object({"scope": {"const": "row"}, "row": _DIGIT}),
        _object({"scope": {"const": "column"}, "col": _DIGIT}),
        _object({"scope": {"const": "box"}, "box": _DIGIT}),
    ]},
    "place": _object({"row": _DIGIT, "col": _DIGIT, "digit": _DIGIT}),
    "undo": _object({}),
    "add_fact": _object({"literal": _LITERAL}),
    "add_rule": _object({
        "premises": {"type": "array", "items": _LITERAL, "minItems": 1, "maxItems": 9},
        "conclusion": _LITERAL,
    }),
    "query": _object({"literal": _LITERAL}),
    "submit": _object({}),
}
TOOL_SCHEMAS = {"$schema": "https://json-schema.org/draft/2020-12/schema", "oneOf": [
    _object({"tool": {"const": tool}, "arguments": arguments})
    for tool, arguments in _ARGUMENTS.items()
]}


def parse_request(raw: Any) -> Result:
    """Validate exactly one request; never coerce types or execute anything."""
    if not isinstance(raw, dict) or set(raw) != {"tool", "arguments"}:
        return failure("invalid_request", "Expected exactly tool and arguments.")
    tool, arguments = raw["tool"], raw["arguments"]
    if not isinstance(tool, str) or not isinstance(arguments, dict):
        return failure("invalid_request", "Tool must be a string and arguments an object.")
    if tool not in _ARGUMENTS:
        return failure("unknown_tool", "Tool is not available.")
    if tool == "inspect":
        scope = arguments.get("scope")
        fields = {"board": set(), "cell": {"row", "col"}, "row": {"row"},
                  "column": {"col"}, "box": {"box"}}
        if not isinstance(scope, str) or scope not in fields:
            return failure("invalid_request", "Expected a supported inspection scope.")
        required = fields[scope] | {"scope"}
    else:
        required = set(_ARGUMENTS[tool]["properties"])
    if set(arguments) != required:
        return failure("invalid_request", "Arguments do not match the tool schema.")
    for name in ("row", "col", "box", "digit"):
        if name not in arguments:
            continue
        value = arguments[name]
        if type(value) is not int:
            return failure("invalid_request", "Coordinates and digits must be integers.")
        if not 1 <= value <= 9:
            code = "invalid_digit" if name == "digit" else "invalid_coordinates"
            return failure(code, "Coordinates and digits must be between 1 and 9.")
    for name in ("literal", "conclusion"):
        if name in arguments and not valid_literal(arguments[name]):
            return failure("invalid_literal", "Expected a propositional literal.")
    if "premises" in arguments:
        premises = arguments["premises"]
        if (not isinstance(premises, list) or not 1 <= len(premises) <= 9
                or not all(valid_literal(item) for item in premises)):
            return failure("invalid_rule", "Expected one through nine literal premises.")
    return success(request=deepcopy(raw))
