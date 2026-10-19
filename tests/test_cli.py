"""L01–L02 tests written before the CLI and replay adapter bodies."""

import json

import pytest

from react_sudoku.cli import main


def inputs(tmp_path, board, requests):
    puzzle = tmp_path / "board.json"
    replay = tmp_path / "requests.json"
    puzzle.write_text(json.dumps(board))
    replay.write_text(json.dumps(requests))
    return ["--puzzle", str(puzzle), "--replay", str(replay)]


def test_l01_replay_validates_solution_and_labels_mode(tmp_path, one_empty, capsys):
    args = inputs(tmp_path, one_empty, [
        {"tool": "place", "arguments": {"row": 1, "col": 3, "digit": 4}},
        {"tool": "submit", "arguments": {}},
    ])
    assert main(args + ["--max-actions", "2"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "scripted_replay"
    assert result["status"] == "success"
    assert result["actions_used"] == 2


def test_l02_result_file_and_budget_failure(tmp_path, solved, capsys):
    args = inputs(tmp_path, solved, [{"tool": "inspect", "arguments": {"scope": "board"}}])
    output = tmp_path / "result.json"
    assert main(args + ["--max-actions", "1", "--output", str(output)]) == 1
    assert json.loads(output.read_text())["status"] == "action_limit"
    assert capsys.readouterr().out == ""


def test_l01_exhausted_replay_is_model_failure(tmp_path, solved, capsys):
    assert main(inputs(tmp_path, solved, [])) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "model_error"
    assert result["actions_used"] == 0


@pytest.mark.parametrize("kind", ["missing_file", "bad_json", "bad_board", "not_array", "bad_output", "bad_budget"])
def test_l02_input_and_output_errors_are_safe(tmp_path, solved, capsys, kind):
    args = inputs(tmp_path, solved, [{"tool": "submit", "arguments": {}}])
    if kind == "missing_file":
        (tmp_path / "board.json").unlink()
    elif kind == "bad_json":
        (tmp_path / "requests.json").write_text("SECRET_INVALID_CONTENT")
    elif kind == "bad_board":
        (tmp_path / "board.json").write_text("[]")
    elif kind == "not_array":
        (tmp_path / "requests.json").write_text("{}")
    elif kind == "bad_output":
        args += ["--output", str(tmp_path / "missing" / "result.json")]
    else:
        args += ["--max-actions", "0"]
    assert main(args) == 2
    captured = capsys.readouterr()
    assert captured.err
    assert captured.out == ""
    assert "SECRET_INVALID_CONTENT" not in captured.err
    assert "Traceback" not in captured.err
