"""Run local-model Sudoku sessions or diagnostic scripted tool replays."""

import argparse
import json
from pathlib import Path
import sys

from .agent import run
from .controller import Controller
from .ollama_model import OllamaModel


class _ReplayModel:
    def __init__(self, requests):
        self._requests = iter(requests)

    def next_request(self, messages, tool_schemas):
        return next(self._requests)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a local Sudoku model or replay scripted tool requests.")
    parser.add_argument("--puzzle", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--replay", type=Path)
    mode.add_argument("--model", help="Name of a model installed in local Ollama.")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--max-actions", type=int, default=200)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        board = json.loads(args.puzzle.read_text(encoding="utf-8"))
        if args.replay is not None:
            requests = json.loads(args.replay.read_text(encoding="utf-8"))
            if not isinstance(requests, list):
                raise ValueError("Replay must be an array.")
            model = _ReplayModel(requests)
        else:
            model = OllamaModel(args.model, args.timeout)
        controller = Controller(board, args.max_actions)
    except (OSError, ValueError, UnicodeError):
        print("Cannot load valid inputs and model/budget configuration.", file=sys.stderr)
        return 2
    result = run(controller, model)
    result["mode"] = "scripted_replay" if args.replay is not None else "local_model"
    if args.model is not None:
        result["model"] = args.model
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
