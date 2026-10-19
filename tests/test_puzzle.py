"""Black-box tests derived from P01–P06 and I01–I03 before implementation."""

from copy import deepcopy

import pytest

from react_sudoku.puzzle import Puzzle


@pytest.mark.parametrize("value", [-1, 10, True, False, 1.0, "1", None])
def test_p01_rejects_invalid_values(board, value):
    board[0][2] = value
    with pytest.raises(ValueError):
        Puzzle(board)


@pytest.mark.parametrize("value", [[], [[0] * 9] * 8, [[0] * 8] * 9, None])
def test_p01_rejects_invalid_shapes(value):
    with pytest.raises(ValueError):
        Puzzle(value)


@pytest.mark.parametrize("cells", [((0, 0), (0, 8)), ((0, 0), (8, 0)), ((0, 0), (1, 1))])
def test_p01_duplicate_clues_in_each_unit(cells):
    board = [[0] * 9 for _ in range(9)]
    for row, col in cells:
        board[row][col] = 5
    with pytest.raises(ValueError):
        Puzzle(board)


def test_p01_p03_input_and_observation_are_copies(board):
    expected = deepcopy(board)
    puzzle = Puzzle(board)
    board[0][0] = 0
    observed = puzzle.inspect("board")
    assert observed["data"]["values"] == expected
    observed["data"]["values"][0][0] = 0
    observed["data"]["givens"][0][0] = False
    assert puzzle.inspect("cell", row=1, col=1)["data"]["values"] == 5
    assert puzzle.inspect("cell", row=1, col=1)["data"]["givens"] is True


@pytest.mark.parametrize("scope,kwargs,expected", [
    ("row", {"row": 1}, [5, 3, 0, 0, 7, 0, 0, 0, 0]),
    ("column", {"col": 1}, [5, 6, 0, 8, 4, 7, 0, 0, 0]),
    ("box", {"box": 1}, [5, 3, 0, 6, 0, 0, 0, 9, 8]),
    ("box", {"box": 9}, [2, 8, 0, 0, 0, 5, 0, 7, 9]),
])
def test_p02_p03_scope_order(board, scope, kwargs, expected):
    result = Puzzle(board).inspect(scope, **kwargs)
    assert result["ok"] is True
    assert result["data"]["values"] == expected
    assert result["data"]["givens"] == [v != 0 for v in expected]


def test_p03_candidates(board):
    puzzle = Puzzle(board)
    assert puzzle.inspect("cell", row=1, col=3)["data"]["candidates"] == [1, 2, 4]
    assert puzzle.inspect("cell", row=1, col=1)["data"]["candidates"] == []


def test_p04_p05_placement_rejection_does_not_enter_undo_stack(board):
    puzzle = Puzzle(board)
    placed = puzzle.place(1, 3, 4)
    assert placed == {"ok": True, "code": "ok", "data": {"row": 1, "col": 3, "digit": 4}}
    assert puzzle.place(1, 3, 4)["code"] == "occupied_cell"
    assert puzzle.place(1, 1, 5)["code"] == "given_cell"
    puzzle.inspect("board")
    assert puzzle.undo()["data"] == placed["data"]
    assert puzzle.inspect("board")["data"]["values"] == board
    assert puzzle.undo()["code"] == "empty_undo"


@pytest.mark.parametrize("other", [(0, 8), (8, 0), (1, 1)])
def test_p04_conflicts_rejected_without_mutation(other):
    board = [[0] * 9 for _ in range(9)]
    board[other[0]][other[1]] = 5
    puzzle = Puzzle(board)
    assert puzzle.place(1, 1, 5)["code"] == "sudoku_conflict"
    assert puzzle.inspect("board")["data"]["values"] == board
    assert puzzle.undo()["code"] == "empty_undo"


@pytest.mark.parametrize("row,col,digit,code", [
    (0, 3, 4, "invalid_coordinates"), (10, 3, 4, "invalid_coordinates"),
    (1, True, 4, "invalid_coordinates"), (1, 3, 0, "invalid_digit"),
    (1, 3, 10, "invalid_digit"), (1, 3, True, "invalid_digit"),
])
def test_p02_p04_boundaries(board, row, col, digit, code):
    puzzle = Puzzle(board)
    assert puzzle.place(row, col, digit)["code"] == code
    assert puzzle.inspect("board")["data"]["values"] == board


def test_p05_undo_is_last_in_first_out(board):
    puzzle = Puzzle(board)
    assert puzzle.place(1, 3, 4)["ok"]
    assert puzzle.place(1, 4, 6)["ok"]
    assert puzzle.undo()["data"] == {"row": 1, "col": 4, "digit": 6}
    assert puzzle.inspect("cell", row=1, col=3)["data"]["values"] == 4
    assert puzzle.undo()["data"] == {"row": 1, "col": 3, "digit": 4}
    assert puzzle.inspect("board")["data"]["values"] == board


def test_p06_submission_validates_complete_board(one_empty, solved):
    puzzle = Puzzle(one_empty)
    assert puzzle.validate_solution()["code"] == "incomplete_board"
    assert puzzle.place(1, 3, 4)["ok"]
    assert puzzle.validate_solution()["ok"] is True
    assert puzzle.inspect("board")["data"]["values"] == solved
    assert puzzle.undo()["ok"]  # Validation does not erase history.
