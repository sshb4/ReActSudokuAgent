"""Local scripted replay for inspecting tools and terminal behavior."""

import argparse
import json
from pathlib import Path
import sys

from .agent import run
from .controller import Controller


class _ReplayModel:
    def __init__(self, requests):
        self._requests = iter(requests)

    def next_request(self, messages, tool_schemas):
        return next(self._requests)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Replay scripted Sudoku tool requests (no language model).")
    parser.add_argument("--puzzle", required=True, type=Path)
    parser.add_argument("--replay", required=True, type=Path)
    parser.add_argument("--max-actions", type=int, default=200)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        board = json.loads(args.puzzle.read_text(encoding="utf-8"))
        requests = json.loads(args.replay.read_text(encoding="utf-8"))
        if not isinstance(requests, list):
            raise ValueError("Replay must be an array.")
        controller = Controller(board, args.max_actions)
    except (OSError, ValueError, UnicodeError):
        print("Cannot load valid puzzle/replay inputs and a positive action budget.", file=sys.stderr)
        return 2
    result = run(controller, _ReplayModel(requests))
    result["mode"] = "scripted_replay"
    text = json.dumps(result, indent=2) + "\n"
    if args.output is not None:
        try:
            args.output.write_text(text, encoding="utf-8")
        except (OSError, UnicodeError):
            print("Cannot write the result file.", file=sys.stderr)
            return 2
    else:
        print(text, end="")
    return 0 if result["status"] == "success" else 1
