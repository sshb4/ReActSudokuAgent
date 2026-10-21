"""Requirement-audit regression tests, written before the corresponding fixes."""

import json

import pytest

from react_sudoku.agent import run
from react_sudoku.controller import Controller


@pytest.mark.parametrize("outcome", ["running", "success", "action_limit", "model_error"])
def test_t02_observations_include_explicit_terminal_reason(solved, outcome):
    controller = Controller(solved, 1 if outcome in ("success", "action_limit") else 5)
    if outcome == "model_error":
        controller.fail_model()
    tool = "submit" if outcome == "success" else "inspect"
    args = {} if tool == "submit" else {"scope": "board"}
    observation = controller.step({"tool": tool, "arguments": args})
    expected = {"running": None, "success": "solution_accepted",
                "action_limit": "action_limit", "model_error": "model_error"}[outcome]
    assert observation["terminal_reason"] == expected
    if outcome != "model_error":
        assert controller.snapshot()["trace"][-1]["observation"] == observation
    if outcome != "running":
        before = controller.snapshot()
        assert controller.step({"tool": "undo", "arguments": {}})["terminal_reason"] == expected
        assert controller.snapshot() == before


def test_a01_model_receives_entailment_before_choosing_placement(one_empty):
    class ReasoningModel:
        def __init__(self):
            self.turn = 0

        def next_request(self, messages, tool_schemas):
            self.turn += 1
            if self.turn == 1:
                return {"tool": "inspect", "arguments": {"scope": "board"}}
            observation = json.loads([m["content"] for m in messages if m["role"] == "tool"][-1])
            if self.turn == 2:
                assert observation["data"]["empty_cells"] == [
                    {"row": 1, "col": 3, "candidates": [4]}]
                return {"tool": "add_fact", "arguments": {"literal": "Board_v0_Only4"}}
            if self.turn == 3:
                return {"tool": "add_rule", "arguments": {
                    "premises": ["Board_v0_Only4"], "conclusion": "Board_v0_CanPlace4"}}
            if self.turn == 4:
                return {"tool": "query", "arguments": {"literal": "Board_v0_CanPlace4"}}
            if self.turn == 5:
                assert observation["data"]["result"] == "entailed"
                return {"tool": "place", "arguments": {"row": 1, "col": 3, "digit": 4}}
            return {"tool": "submit", "arguments": {}}

    result = run(Controller(one_empty, 6), ReasoningModel())
    assert result["status"] == "success"
    assert [e["request"]["tool"] for e in result["trace"]] == [
        "inspect", "add_fact", "add_rule", "query", "place", "submit"]


def test_a05_goals_advance_only_after_accepted_observations(one_empty):
    class GoalModel:
        def __init__(self):
            self.turn = 0

        def next_request(self, messages, tool_schemas):
            self.turn += 1
            reminder = [m["content"] for m in messages if m["role"] == "developer"][-1]
            requests = [
                ("inspect", {"tool": "inspect", "arguments": {"scope": "board"}}),
                ("add_fact", {"tool": "add_fact", "arguments": {"literal": "bad literal"}}),
                ("add_fact", {"tool": "add_fact", "arguments": {"literal": "Singleton"}}),
                ("add_rule", {"tool": "add_rule", "arguments": {"premises": ["Singleton"], "conclusion": "Safe"}}),
                ("query", {"tool": "query", "arguments": {"literal": "Unknown"}}),
                ("query", {"tool": "query", "arguments": {"literal": "Safe"}}),
                ("place", {"tool": "place", "arguments": {"row": 1, "col": 3, "digit": 4}}),
                ("inspect", {"tool": "inspect", "arguments": {"scope": "board"}}),
                ("submit", {"tool": "submit", "arguments": {}}),
            ]
            goal, request = requests[self.turn - 1]
            assert "NEXT GOAL: " + goal in reminder
            return request

    assert run(Controller(one_empty, 9), GoalModel())["status"] == "success"


def test_a05_reminder_preserves_model_selected_negation_and_conclusion(one_empty):
    class LiteralModel:
        def __init__(self):
            self.turn = 0

        def next_request(self, messages, tool_schemas):
            self.turn += 1
            goal = [m["content"] for m in messages if m["role"] == "developer"][-1]
            if self.turn == 1:
                return {"tool": "inspect", "arguments": {"scope": "board"}}
            if self.turn == 2:
                return {"tool": "add_fact", "arguments": {"literal": "~HasAlternatives"}}
            if self.turn == 3:
                assert '"~HasAlternatives"' in goal
                return {"tool": "add_rule", "arguments": {"premises": ["~HasAlternatives"], "conclusion": "Forced"}}
            assert '"Forced"' in goal
            return {"tool": "query", "arguments": {"literal": "Forced"}}

    result = run(Controller(one_empty, 4), LiteralModel())
    assert result["trace"][-1]["observation"]["data"]["result"] == "entailed"
