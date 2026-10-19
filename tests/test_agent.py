"""A01–A04: a scripted model tests orchestration, not model solving ability."""

from copy import deepcopy
import json

import pytest

from react_sudoku.agent import run
from react_sudoku.controller import Controller


class ScriptedModel:
    def __init__(self, requests):
        self.requests = iter(requests)
        self.calls = []

    def next_request(self, messages, tool_schemas):
        self.calls.append((deepcopy(messages), deepcopy(tool_schemas)))
        return next(self.requests)


def test_a01_observations_return_to_model_and_a04_success_stops(one_empty, solved):
    model = ScriptedModel([
        {"tool": "inspect", "arguments": {"scope": "board"}},
        {"tool": "place", "arguments": {"row": 1, "col": 3, "digit": 4}},
        {"tool": "submit", "arguments": {}},
        {"tool": "undo", "arguments": {}},
    ])
    result = run(Controller(one_empty, 5), model)
    assert result["status"] == "success"
    assert result["board"] == solved
    assert result["actions_used"] == 3
    assert len(model.calls) == 3
    initial_messages, schema = model.calls[0]
    assert any(message["role"] == "developer" for message in initial_messages)
    assert schema
    json.dumps(initial_messages)
    second_messages = model.calls[1][0]
    observation = json.loads([m["content"] for m in second_messages if m["role"] == "tool"][-1])
    assert observation["data"]["values"] == one_empty
    assert observation["actions_remaining"] == 4
    request = json.loads([m["content"] for m in second_messages if m["role"] == "assistant"][-1])
    assert request == {"tool": "inspect", "arguments": {"scope": "board"}}


@pytest.mark.parametrize("response", ["Success!", [], [
    {"tool": "undo", "arguments": {}}, {"tool": "submit", "arguments": {}},
]])
def test_a02_free_text_zero_or_multiple_requests_cannot_establish_success(solved, response):
    model = ScriptedModel([response])
    result = run(Controller(solved, 1), model)
    assert result["status"] == "action_limit"
    assert result["actions_used"] == 1
    assert result["trace"][0]["observation"]["ok"] is False
    assert result["board"] == solved
    assert len(model.calls) == 1


def test_c07_a04_transport_exception_is_terminal_and_redacted(board):
    class FailingModel:
        def next_request(self, messages, tool_schemas):
            raise RuntimeError("secret-token=DO_NOT_RECORD_THIS")

    result = run(Controller(board, 5), FailingModel())
    assert result["status"] == "model_error"
    assert result["actions_used"] == 0
    assert result["trace"] == []
    assert result["events"][0]["code"] == "model_error"
    assert "DO_NOT_RECORD_THIS" not in json.dumps(result)


def test_a04_already_terminal_controller_does_not_call_model(solved):
    controller = Controller(solved, 1)
    controller.step({"tool": "submit", "arguments": {}})
    model = ScriptedModel([])
    assert run(controller, model)["status"] == "success"
    assert model.calls == []
