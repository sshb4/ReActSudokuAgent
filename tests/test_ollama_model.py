"""M01–M04 adapter tests, written before adapter implementation.

Transport is replaced at the standard-library HTTP boundary. These are unit
tests of the adapter contract, not claims of an actual language-model run.
"""

from copy import deepcopy
import io
import json
from urllib.error import URLError

import pytest

from react_sudoku.agent import run
from react_sudoku.controller import Controller
from react_sudoku.ollama_model import OllamaModel
from react_sudoku.schemas import TOOL_SCHEMAS


def transport(monkeypatch, body=None, error=None):
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append((request, timeout))
            if error:
                raise error
            return io.BytesIO(body)

    def build(*handlers):
        calls.append(handlers)
        return Opener()

    monkeypatch.setattr("urllib.request.build_opener", build)
    return calls


def envelope(content):
    return json.dumps({"done": True, "message": {"content": content}}).encode()


@pytest.mark.parametrize("name,timeout", [
    ("", 60), (None, 60), ("has space", 60), (True, 60),
    ("local-model", 0), ("local-model", -1), ("local-model", True),
    ("local-model", float("nan")), ("local-model", float("inf")), ("local-model", "60"),
])
def test_m01_invalid_configuration(name, timeout):
    with pytest.raises(ValueError):
        OllamaModel(name, timeout)


def test_m02_translates_history_and_sends_schema_without_mutation(monkeypatch):
    expected = {"tool": "submit", "arguments": {}}
    calls = transport(monkeypatch, envelope(json.dumps(expected)))
    messages = [
        {"role": "developer", "content": "Instructions"},
        {"role": "assistant", "content": '{"tool":"inspect"}'},
        {"role": "tool", "content": '{"ok":true}'},
    ]
    original = deepcopy(messages)
    schema = deepcopy(TOOL_SCHEMAS)
    assert OllamaModel("local-model", 12.5).next_request(messages, schema) == expected
    request, timeout = calls[-1]
    assert request.full_url == "http://127.0.0.1:11434/api/chat"
    assert request.method == "POST"
    assert timeout == 12.5
    payload = json.loads(request.data)
    assert payload["model"] == "local-model"
    assert payload["format"] == schema
    assert payload["stream"] is False
    assert payload["options"]["temperature"] == 0
    assert {"role": "system", "content": "Instructions"} in payload["messages"]
    assert {"role": "user", "content": 'Tool observation: {"ok":true}'} in payload["messages"]
    assert any(json.dumps(schema) in m["content"] for m in payload["messages"])
    assert messages == original
    assert schema == TOOL_SCHEMAS


@pytest.mark.parametrize("content", [
    "not JSON", '{"tool":"submit","tool":"undo","arguments":{}}',
    '{"tool":"place","arguments":{"row":NaN}}',
])
def test_m03_malformed_content_is_a_counted_rejection(monkeypatch, solved, content):
    transport(monkeypatch, envelope(content))
    result = run(Controller(solved, 1), OllamaModel("local-model"))
    assert result["status"] == "action_limit"
    assert result["actions_used"] == 1
    assert result["trace"][0]["observation"]["ok"] is False


@pytest.mark.parametrize("body", [
    b"not JSON", b"{}", b"[]", b'{"done":false,"message":{"content":"{}"}}',
    b'{"done":true,"message":{"content":null}}', b"x" * (1024 * 1024 + 1),
])
def test_m03_bad_envelope_is_model_failure_without_tool_action(monkeypatch, solved, body):
    transport(monkeypatch, body)
    result = run(Controller(solved, 1), OllamaModel("local-model"))
    assert result["status"] == "model_error"
    assert result["actions_used"] == 0


@pytest.mark.parametrize("error", [TimeoutError("PRIVATE"), URLError("PRIVATE")])
def test_m03_transport_failure_has_no_details_and_no_retry(monkeypatch, error):
    calls = transport(monkeypatch, error=error)
    with pytest.raises(RuntimeError) as caught:
        OllamaModel("local-model").next_request([], TOOL_SCHEMAS)
    assert "PRIVATE" not in str(caught.value)
    assert len([c for c in calls if len(c) == 2 and isinstance(c[1], (int, float))]) == 1


def test_m03_redirects_are_refused(monkeypatch):
    calls = transport(monkeypatch, envelope('{}'))
    OllamaModel("local-model").next_request([], TOOL_SCHEMAS)
    handlers = calls[0]
    redirect = next(h for h in handlers if hasattr(h, "redirect_request"))
    with pytest.raises(RuntimeError):
        redirect.redirect_request(None, None, 302, "Found", {}, "https://example.com")
