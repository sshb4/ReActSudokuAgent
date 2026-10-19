"""M04 model-mode CLI tests written before the CLI model-mode change."""

import json

import pytest

from react_sudoku.cli import main


def test_m04_cli_calls_adapter_and_labels_result(tmp_path, solved, monkeypatch, capsys):
    path = tmp_path / "board.json"
    path.write_text(json.dumps(solved))
    seen = []

    class Model:
        def __init__(self, name, timeout):
            seen.append((name, timeout))

        def next_request(self, messages, tool_schemas):
            return {"tool": "submit", "arguments": {}}

    monkeypatch.setattr("react_sudoku.cli.OllamaModel", Model)
    assert main(["--puzzle", str(path), "--model", "local-model", "--timeout", "3.5"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert seen == [("local-model", 3.5)]
    assert result["mode"] == "local_model"
    assert result["model"] == "local-model"
    assert result["status"] == "success"


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_m04_invalid_timeout_returns_input_error(tmp_path, solved, capsys, timeout):
    path = tmp_path / "board.json"
    path.write_text(json.dumps(solved))
    assert main(["--puzzle", str(path), "--model", "local-model", "--timeout", timeout]) == 2
    assert capsys.readouterr().err


def test_m04_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit) as caught:
        main(["--puzzle", "unused.json", "--model", "local-model", "--replay", "unused.json"])
    assert caught.value.code == 2
