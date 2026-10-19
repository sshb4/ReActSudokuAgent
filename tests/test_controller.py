"""Public controller behavior from C01–C07, including ordered terminal checks."""

from copy import deepcopy

import pytest

from react_sudoku.controller import Controller


def call(controller, tool, **arguments):
    return controller.step({"tool": tool, "arguments": arguments})


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "10"])
def test_c01_invalid_budget(board, limit):
    with pytest.raises(ValueError):
        Controller(board, limit)


def test_c01_initial_state_and_input_isolation(board):
    controller = Controller(board, 10)
    expected = deepcopy(board)
    board[0][0] = 0
    state = controller.snapshot()
    assert state["board"] == expected
    assert state["status"] == "running"
    assert state["terminal_reason"] is None
    assert state["actions_used"] == 0
    assert state["actions_remaining"] == 10
    assert state["trace"] == []
    assert state["events"] == []


def test_c02_c03_every_attempt_counts_and_rejection_is_atomic(board):
    controller = Controller(board, 6)
    requests = [
        {"tool": "inspect", "arguments": {"scope": "board"}},
        {"tool": "query", "arguments": {"literal": "A"}},
        "I solved it", {"tool": "win", "arguments": {}},
        {"tool": "place", "arguments": {"row": 1, "col": 1, "digit": 5}},
        {"tool": "submit", "arguments": {}},
    ]
    for number, request in enumerate(requests, 1):
        result = controller.step(request)
        assert {"ok", "code", "data", "actions_used", "actions_remaining", "status"} <= result.keys()
        assert result["actions_used"] == number
        assert result["actions_remaining"] == 6 - number
        assert controller.snapshot()["board"] == board
    assert result["status"] == "action_limit"
    assert len(controller.snapshot()["trace"]) == 6


def test_c03_extra_fields_cannot_inject_terminal_status(board):
    controller = Controller(board, 5)
    result = controller.step({"tool": "submit", "arguments": {}, "status": "success"})
    assert result["code"] == "invalid_request"
    assert result["status"] == "running"
    assert controller.snapshot()["board"] == board


def test_c04_last_action_success_and_terminal_immutability(solved):
    controller = Controller(solved, 1)
    assert controller.snapshot()["status"] == "running"
    assert call(controller, "submit")["status"] == "success"
    before = controller.snapshot()
    assert before["terminal_reason"] == "solution_accepted"
    assert call(controller, "undo")["code"] == "session_terminal"
    assert controller.snapshot() == before


def test_c04_final_placement_requires_explicit_submission(one_empty):
    controller = Controller(one_empty, 1)
    result = call(controller, "place", row=1, col=3, digit=4)
    assert result["ok"] is True
    assert result["status"] == "action_limit"
    before = controller.snapshot()
    assert call(controller, "submit")["code"] == "session_terminal"
    assert controller.snapshot() == before


def test_c05_failed_submission_does_not_clear_undo(board):
    controller = Controller(board, 5)
    assert call(controller, "place", row=1, col=3, digit=4)["ok"]
    assert call(controller, "submit")["code"] == "incomplete_board"
    assert call(controller, "undo")["ok"]
    assert controller.snapshot()["board"] == board


def test_k06_kb_survives_undo_but_cannot_override_board_rules(board):
    controller = Controller(board, 10)
    assert call(controller, "add_fact", literal="Board_v1_Cell13Is4")["ok"]
    assert call(controller, "place", row=1, col=3, digit=4)["ok"]
    assert call(controller, "undo")["ok"]
    assert call(controller, "query", literal="Board_v1_Cell13Is4")["data"]["result"] == "entailed"
    assert call(controller, "place", row=1, col=3, digit=5)["code"] == "sudoku_conflict"
    assert controller.snapshot()["board"] == board


def test_c06_trace_has_ordered_requests_and_final_observations(board):
    controller = Controller(board, 2)
    request = {"tool": "inspect", "arguments": {"scope": "board"}}
    original = deepcopy(request)
    result = controller.step(request)
    request["arguments"]["scope"] = "invalid"
    result["data"]["values"][0][0] = 0
    final = controller.step("malformed")
    state = controller.snapshot()
    assert [entry["action"] for entry in state["trace"]] == [1, 2]
    assert state["trace"][0]["request"] == original
    assert state["trace"][0]["observation"]["data"]["values"][0][0] == 5
    assert state["trace"][1]["request"] == "malformed"
    assert state["trace"][1]["observation"] == final
    state["board"][0][0] = 0
    state["trace"].clear()
    assert len(controller.snapshot()["trace"]) == 2
    assert controller.snapshot()["board"] == board


def test_c07_model_failure_preserves_state_without_tool_action(board):
    controller = Controller(board, 5)
    call(controller, "place", row=1, col=3, digit=4)
    before = controller.snapshot()
    controller.fail_model()
    after = controller.snapshot()
    assert after["status"] == "model_error"
    assert after["terminal_reason"] == "model_error"
    for field in ("board", "givens", "trace", "actions_used", "actions_remaining"):
        assert after[field] == before[field]
    assert after["events"][0]["code"] == "model_error"
