"""T01–T02: the advertised schema and parser agree on public requests."""

from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator

from react_sudoku.schemas import TOOL_SCHEMAS, parse_request


VALID = [
    {"tool": "inspect", "arguments": {"scope": "board"}},
    {"tool": "inspect", "arguments": {"scope": "cell", "row": 1, "col": 9}},
    {"tool": "inspect", "arguments": {"scope": "row", "row": 9}},
    {"tool": "inspect", "arguments": {"scope": "column", "col": 1}},
    {"tool": "inspect", "arguments": {"scope": "box", "box": 9}},
    {"tool": "place", "arguments": {"row": 1, "col": 9, "digit": 4}},
    {"tool": "undo", "arguments": {}},
    {"tool": "add_fact", "arguments": {"literal": "~A"}},
    {"tool": "add_rule", "arguments": {"premises": ["A", "~B"], "conclusion": "C"}},
    {"tool": "query", "arguments": {"literal": "A"}},
    {"tool": "submit", "arguments": {}},
]

INVALID = [
    None, "success", [], VALID[:2], {}, {"tool": "undo"},
    {"tool": "win", "arguments": {}},
    {"tool": "undo", "arguments": {}, "status": "success"},
    {"tool": "undo", "arguments": {"row": 1}},
    {"tool": "submit", "arguments": {"board": []}},
    {"tool": "inspect", "arguments": {"scope": "cell", "row": 1}},
    {"tool": "inspect", "arguments": {"scope": "board", "row": 1}},
    {"tool": "place", "arguments": {"row": True, "col": 3, "digit": 4}},
    {"tool": "place", "arguments": {"row": 0, "col": 3, "digit": 4}},
    {"tool": "place", "arguments": {"row": 1, "col": 3, "digit": "4"}},
    {"tool": "add_fact", "arguments": {"literal": "~~A"}},
    {"tool": "add_rule", "arguments": {"premises": [], "conclusion": "A"}},
]


def test_t01_schema_is_well_formed():
    Draft202012Validator.check_schema(TOOL_SCHEMAS)


@pytest.mark.parametrize("request", VALID)
def test_t01_valid_tools_match_schema_and_parser(request):
    assert Draft202012Validator(TOOL_SCHEMAS).is_valid(request)
    result = parse_request(deepcopy(request))
    assert result["ok"] is True
    assert result["data"]["request"] == request


@pytest.mark.parametrize("request", INVALID)
def test_t01_invalid_tools_match_schema_and_parser(request):
    assert not Draft202012Validator(TOOL_SCHEMAS).is_valid(request)
    assert parse_request(deepcopy(request))["ok"] is False


def test_i03_parser_distinguishes_errors():
    assert parse_request({"tool": "win", "arguments": {}})["code"] == "unknown_tool"
    assert parse_request({"tool": "place", "arguments": {"row": 0, "col": 1, "digit": 1}})["code"] == "invalid_coordinates"
    assert parse_request({"tool": "undo"})["code"] == "invalid_request"
