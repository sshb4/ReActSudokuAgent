"""Regression tests from the first real local-runtime integration review."""

from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator

from react_sudoku.puzzle import Puzzle
from react_sudoku.schemas import TOOL_SCHEMAS, parse_request


def test_board_labels_empty_cells_and_updates_candidates(one_empty):
    puzzle = Puzzle(one_empty)
    assert puzzle.inspect("board")["data"]["empty_cells"] == [
        {"row": 1, "col": 3, "candidates": [4]}]
    assert puzzle.place(1, 3, 4)["ok"]
    assert puzzle.inspect("board")["data"]["empty_cells"] == []
    assert puzzle.undo()["ok"]
    assert puzzle.inspect("board")["data"]["empty_cells"] == [
        {"row": 1, "col": 3, "candidates": [4]}]


def test_labeled_cells_are_ordered_and_detached(board):
    puzzle = Puzzle(board)
    cells = puzzle.inspect("board")["data"]["empty_cells"]
    expected = deepcopy(cells)
    assert [(c["row"], c["col"]) for c in cells] == sorted(
        (r + 1, c + 1) for r in range(9) for c in range(9) if board[r][c] == 0)
    for cell in cells:
        assert cell["candidates"] == puzzle.inspect("cell", row=cell["row"], col=cell["col"])["data"]["candidates"]
    cells[0]["candidates"].clear()
    assert puzzle.inspect("board")["data"]["empty_cells"] == expected


@pytest.mark.parametrize("literal", ["A\n", "A\r\n", "~B\n", "A B", "~~A"])
def test_schema_and_parser_reject_invalid_literal_endings(literal):
    request = {"tool": "add_fact", "arguments": {"literal": literal}}
    assert not Draft202012Validator(TOOL_SCHEMAS).is_valid(request)
    assert not parse_request(request)["ok"]


def test_schema_patterns_use_runtime_compatible_anchors():
    def walk(node):
        if isinstance(node, dict):
            if "pattern" in node:
                assert node["pattern"].startswith("^")
                assert node["pattern"].endswith("$")
                assert "(?" not in node["pattern"]
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(TOOL_SCHEMAS)
