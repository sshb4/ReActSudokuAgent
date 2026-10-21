"""Sudoku board operations with immutable clues and a placement undo stack."""

from copy import deepcopy

from .schemas import failure, success


def _coordinate(value):
    return type(value) is int and 1 <= value <= 9


def _units(board):
    yield from board
    for col in range(9):
        yield [board[row][col] for row in range(9)]
    for top in (0, 3, 6):
        for left in (0, 3, 6):
            yield [board[row][col] for row in range(top, top + 3)
                   for col in range(left, left + 3)]


class Puzzle:
    def __init__(self, board):
        if (not isinstance(board, list) or len(board) != 9
                or any(not isinstance(row, list) or len(row) != 9 for row in board)
                or any(type(value) is not int or not 0 <= value <= 9
                       for row in board for value in row)):
            raise ValueError("Board must be nine lists of nine integer values from 0 through 9.")
        for unit in _units(board):
            filled = [digit for digit in unit if digit]
            if len(filled) != len(set(filled)):
                raise ValueError("Given clues conflict in a row, column, or box.")
        self._original = tuple(tuple(row) for row in board)
        self._board = deepcopy(board)
        self._history = []

    def _legal(self, row, col, digit):
        top, left = row // 3 * 3, col // 3 * 3
        return (digit not in self._board[row]
                and all(self._board[r][col] != digit for r in range(9))
                and all(self._board[r][c] != digit
                        for r in range(top, top + 3) for c in range(left, left + 3)))

    def inspect(self, scope, row=None, col=None, box=None):
        supplied = {key: value for key, value in {"row": row, "col": col, "box": box}.items()
                    if value is not None}
        fields = {"board": set(), "cell": {"row", "col"}, "row": {"row"},
                  "column": {"col"}, "box": {"box"}}
        if not isinstance(scope, str) or scope not in fields:
            return failure("invalid_scope", "Unsupported inspection scope.")
        if set(supplied) != fields[scope] or not all(_coordinate(v) for v in supplied.values()):
            return failure("invalid_coordinates", "Supply the coordinates required by the scope.")
        if scope == "board":
            return success(values=deepcopy(self._board),
                           givens=[[bool(v) for v in r] for r in self._original],
                           empty_cells=[
                               {"row": r + 1, "col": c + 1,
                                "candidates": [d for d in range(1, 10) if self._legal(r, c, d)]}
                               for r in range(9) for c in range(9) if self._board[r][c] == 0])
        if scope == "cell":
            r, c = row - 1, col - 1
            value = self._board[r][c]
            return success(values=value, givens=bool(self._original[r][c]),
                           candidates=[] if value else [d for d in range(1, 10) if self._legal(r, c, d)])
        if scope == "row":
            cells = [(row - 1, c) for c in range(9)]
        elif scope == "column":
            cells = [(r, col - 1) for r in range(9)]
        else:
            top, left = (box - 1) // 3 * 3, (box - 1) % 3 * 3
            cells = [(r, c) for r in range(top, top + 3) for c in range(left, left + 3)]
        return success(values=[self._board[r][c] for r, c in cells],
                       givens=[bool(self._original[r][c]) for r, c in cells])

    def place(self, row, col, digit):
        if not _coordinate(row) or not _coordinate(col):
            return failure("invalid_coordinates", "Row and column must be integers from 1 through 9.")
        if not _coordinate(digit):
            return failure("invalid_digit", "Digit must be an integer from 1 through 9.")
        r, c = row - 1, col - 1
        if self._original[r][c]:
            return failure("given_cell", "Original clues cannot be changed.")
        if self._board[r][c]:
            return failure("occupied_cell", "Undo an occupied cell before replacing its value.")
        if not self._legal(r, c, digit):
            return failure("sudoku_conflict", "Digit conflicts with a row, column, or box.")
        self._board[r][c] = digit
        self._history.append((row, col, digit))
        return success(row=row, col=col, digit=digit)

    def undo(self):
        if not self._history:
            return failure("empty_undo", "There are no accepted placements to undo.")
        row, col, digit = self._history.pop()
        self._board[row - 1][col - 1] = 0
        return success(row=row, col=col, digit=digit)

    def validate_solution(self):
        # Recheck the board and original clues independently of placement history.
        if (not isinstance(self._board, list) or len(self._board) != 9
                or any(not isinstance(row, list) or len(row) != 9 for row in self._board)
                or any(type(value) is not int or not 0 <= value <= 9
                       for row in self._board for value in row)):
            return failure("invalid_solution", "Board representation is invalid.")
        for r in range(9):
            for c in range(9):
                if self._original[r][c] and self._board[r][c] != self._original[r][c]:
                    return failure("invalid_solution", "An original clue has changed.")
        if any(len([v for v in unit if v]) != len({v for v in unit if v})
               for unit in _units(self._board)):
            return failure("invalid_solution", "A row, column, or box contains duplicate digits.")
        if any(0 in row for row in self._board):
            return failure("incomplete_board", "Fill every cell before submitting.")
        if any(set(unit) != set(range(1, 10)) for unit in _units(self._board)):
            return failure("invalid_solution", "Every unit must contain each digit once.")
        return success()
