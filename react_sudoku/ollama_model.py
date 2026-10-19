"""Schema-constrained requests to a separately installed local Ollama runtime."""

from copy import deepcopy
import json
import math
import urllib.request


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        raise RuntimeError("Local model redirects are not supported.")


def _strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key.")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("Non-finite JSON constant.")

    def number(value):
        decoded = float(value)
        if not math.isfinite(decoded):
            raise ValueError("Non-finite JSON number.")
        return decoded

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)


class OllamaModel:
    def __init__(self, model, timeout=60):
        if not isinstance(model, str) or not model or any(c.isspace() for c in model):
            raise ValueError("A nonempty model name without whitespace is required.")
        try:
            valid_timeout = (type(timeout) in (int, float)
                             and math.isfinite(timeout) and timeout > 0)
        except OverflowError:
            valid_timeout = False
        if not valid_timeout:
            raise ValueError("Timeout must be a positive finite number.")
        self._model = model
        self._timeout = timeout

    def next_request(self, messages, tool_schemas):
        translated = []
        for message in messages:
            item = dict(message)
            if item["role"] == "developer":
                item["role"] = "system"
            elif item["role"] == "tool":
                item["role"] = "user"
                item["content"] = "Tool observation: " + item["content"]
            translated.append(item)
        translated.insert(0, {"role": "system", "content":
                             "Return exactly one JSON tool request matching this schema: "
                             + json.dumps(tool_schemas)})
        payload = {"model": self._model, "messages": translated,
                   "format": deepcopy(tool_schemas), "stream": False,
                   "options": {"temperature": 0}}
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
            with opener.open(request, timeout=self._timeout) as response:
                body = response.read(1024 * 1024 + 1)
            if len(body) > 1024 * 1024:
                raise ValueError("Response too large.")
            envelope = _strict_json(body)
            if not isinstance(envelope, dict) or envelope.get("done") is not True:
                raise ValueError("Expected a completed response.")
            message = envelope.get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                raise ValueError("Expected message content.")
            content = message["content"]
        except Exception:
            raise RuntimeError("Local model request failed.") from None
        try:
            return _strict_json(content)
        except (ValueError, RecursionError):
            # A model-output mistake counts as a rejected action, not a retry.
            return content
