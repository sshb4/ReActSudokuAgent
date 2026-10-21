"""Validate and dispatch requests; own the session's budget, trace, and status."""

from copy import deepcopy

from .knowledge import KnowledgeBase
from .puzzle import Puzzle
from .schemas import failure, parse_request


class Controller:
    def __init__(self, board, max_actions):
        if type(max_actions) is not int or max_actions < 1:
            raise ValueError("Action limit must be a positive integer.")
        self._puzzle = Puzzle(board)
        self._knowledge = KnowledgeBase()
        self._max_actions = max_actions
        self._actions_used = 0
        self._status = "running"
        self._terminal_reason = None
        self._trace = []
        self._events = []

    def snapshot(self):
        inspection = self._puzzle.inspect("board")["data"]
        return deepcopy({
            "board": inspection["values"], "givens": inspection["givens"],
            "status": self._status, "terminal_reason": self._terminal_reason,
            "actions_used": self._actions_used,
            "actions_remaining": self._max_actions - self._actions_used,
            "trace": self._trace, "events": self._events,
        })

    def _observe(self, result):
        return {**result, "actions_used": self._actions_used,
                "actions_remaining": self._max_actions - self._actions_used,
                "status": self._status, "terminal_reason": self._terminal_reason}

    def step(self, raw_request):
        if self._status != "running":
            return self._observe(failure("session_terminal", "Session has already terminated."))
        self._actions_used += 1
        parsed = parse_request(raw_request)
        tool = None
        if not parsed["ok"]:
            result = parsed
        else:
            request = parsed["data"]["request"]
            tool, arguments = request["tool"], request["arguments"]
            operations = {
                "inspect": self._puzzle.inspect, "place": self._puzzle.place,
                "undo": self._puzzle.undo, "submit": self._puzzle.validate_solution,
                "add_fact": self._knowledge.add_fact, "add_rule": self._knowledge.add_rule,
                "query": self._knowledge.query,
            }
            result = operations[tool](**arguments)
        if tool == "submit" and result["ok"]:
            self._status, self._terminal_reason = "success", "solution_accepted"
        elif self._actions_used == self._max_actions:
            self._status = self._terminal_reason = "action_limit"
        observation = self._observe(result)
        self._trace.append(deepcopy({"action": self._actions_used,
                                    "request": raw_request, "observation": observation}))
        return observation

    def fail_model(self):
        if self._status == "running":
            self._status = self._terminal_reason = "model_error"
            self._events.append({"code": "model_error", "reason": "Model request failed."})
