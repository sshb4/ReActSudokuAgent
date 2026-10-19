"""Runtime-independent model interface; no external service is assumed."""

from typing import Any, Protocol


class Model(Protocol):
    """Adapters constrain output to the supplied schema and decode one request.

    Adapters must apply a finite runtime timeout and keep authentication config
    out of messages, returned requests, and errors surfaced to the run trace.
    Invalid decoded responses are returned for controller rejection. Transport
    failures raise exceptions; the loop records a generic failure event.
    """

    def next_request(self, messages: list[dict[str, str]], tool_schemas: dict) -> Any:
        ...
