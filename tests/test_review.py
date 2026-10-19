"""Supplemental review checks written after implementation.

These supplement the test-first black-box suite; fault-injection tests below
deliberately access private puzzle storage to verify independent validation.
"""

from copy import deepcopy
from itertools import product
import random

import pytest

from react_sudoku.agent import run
from react_sudoku.controller import Controller
from react_sudoku.knowledge import KnowledgeBase
from react_sudoku.puzzle import Puzzle


def test_classical_kb_agrees_with_independent_truth_tables():
    """Compare public update/query results with all eight three-atom worlds."""
    rng = random.Random(4300)
    literals = ["A", "~A", "B", "~B", "C", "~C"]

    def holds(literal, world):
        return not world[literal[1:]] if literal.startswith("~") else world[literal]

    for _ in range(40):
        worlds = [dict(zip("ABC", values)) for values in product([False, True], repeat=3)]
        kb = KnowledgeBase()
        for _ in range(12):
            conclusion = rng.choice(literals)
            if rng.randrange(3) == 0:
                candidate = [w for w in worlds if holds(conclusion, w)]
                result = kb.add_fact(conclusion)
            else:
                premises = rng.choices(literals, k=rng.randint(1, 3))
                candidate = [w for w in worlds
                             if not all(holds(p, w) for p in premises) or holds(conclusion, w)]
                result = kb.add_rule(premises, conclusion)
            assert result["ok"] is bool(candidate)
            if candidate:
                worlds = candidate
            for literal in literals:
                truths = [holds(literal, w) for w in worlds]
                expected = "entailed" if all(truths) else "contradicted" if not any(truths) else "unresolved"
                assert kb.query(literal)["data"]["result"] == expected


@pytest.mark.parametrize("damage", ["clue", "row", "column", "box", "type"])
def test_independent_validator_rejects_corrupted_state(solved, damage):
    puzzle = Puzzle(solved if damage == "clue" else [[0] * 9 for _ in range(9)])
    corrupted = deepcopy(solved)
    if damage == "clue":
        # Another valid Sudoku still fails because original clues differ.
        corrupted = [[2 if d == 1 else 1 if d == 2 else d for d in row] for row in solved]
    elif damage == "row":
        corrupted[0][0] = corrupted[0][1]
    elif damage == "column":
        corrupted[0][0], corrupted[0][1] = corrupted[0][1], corrupted[0][0]
    elif damage == "box":
        # Swapping columns across stacks preserves rows/columns, breaks boxes.
        for row in corrupted:
            row[0], row[3] = row[3], row[0]
    else:
        corrupted[0][0] = True
    puzzle._board = corrupted  # White-box fault injection, not an agent capability.
    assert puzzle.validate_solution()["code"] == "invalid_solution"


def test_adapter_mutation_cannot_change_prior_messages_or_schema(solved):
    class MutatingModel:
        def __init__(self):
            self.calls = 0

        def next_request(self, messages, tool_schemas):
            self.calls += 1
            assert messages[0]["role"] == "developer"
            assert "oneOf" in tool_schemas
            messages[0]["role"] = "corrupted"
            tool_schemas.clear()
            if self.calls == 1:
                return {"tool": "inspect", "arguments": {"scope": "board"}}
            return {"tool": "submit", "arguments": {}}

    result = run(Controller(solved, 3), MutatingModel())
    assert result["status"] == "success"
    assert result["board"] == solved
