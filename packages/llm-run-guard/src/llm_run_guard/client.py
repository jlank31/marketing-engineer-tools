"""A drop-in Anthropic client that records what every call costs.

    from llm_run_guard import TrackedClient
    client = TrackedClient("summarizer")
    response = client.messages.create(...)   # unchanged

Everything else about the SDK stays the same. The wrapper only intercepts
`messages.create` to time the call and record its usage.

Two defaults here are deliberate and worth knowing:

**A bounded timeout.** The SDK default is 600 seconds, with 2 internal retries,
so a single blocking call can hang for 30 minutes during an overloaded-API window
while looking like a slow response. Capped at 150s here, env-overridable. The
retry count is set explicitly too, because leaving it implicit means the real
worst case is `timeout x (retries + 1)` and nobody realises.

**Lazy construction.** The underlying client is built on first use, not in
`__init__`. Constructing eagerly means merely IMPORTING a module that defines a
client at module scope raises without an API key, which turns "no key set" into
an import error three files away from the cause.
"""

from __future__ import annotations

import os
import time

from . import tracker

DEFAULT_TIMEOUT_SECONDS = 150.0
DEFAULT_MAX_RETRIES = 2


class _TrackedMessages:
    def __init__(self, owner: TrackedClient) -> None:
        self._owner = owner

    def create(self, **kwargs):
        model = kwargs.get("model", "unknown")
        started = time.time()
        response = self._owner.raw.messages.create(**kwargs)
        latency_ms = int((time.time() - started) * 1000)

        searches = 0
        server_tool = getattr(getattr(response, "usage", None), "server_tool_use", None)
        if server_tool is not None:
            searches = int(getattr(server_tool, "web_search_requests", 0) or 0)

        tracker.record(
            self._owner.label,
            model,
            usage=getattr(response, "usage", None),
            web_search_requests=searches,
            latency_ms=latency_ms,
        )
        return response

    def __getattr__(self, name):
        # Anything not intercepted (stream, count_tokens, batches) passes through.
        return getattr(self._owner.raw.messages, name)


class TrackedClient:
    """`anthropic.Anthropic` with per-call cost recording.

    `label` is how the call shows up in `summary()["by_label"]`. Use the name of
    the step, not the model: "summarizer", "classifier", "draft". That is what
    makes the summary answer "which part of my pipeline is expensive".
    """

    def __init__(
        self,
        label: str = "default",
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
        **client_kwargs,
    ) -> None:
        self.label = label
        self._timeout = timeout if timeout is not None else float(
            os.getenv("ANTHROPIC_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
        )
        self._max_retries = max_retries if max_retries is not None else int(
            os.getenv("ANTHROPIC_MAX_RETRIES", DEFAULT_MAX_RETRIES)
        )
        self._client_kwargs = client_kwargs
        self._raw = None
        self._messages = _TrackedMessages(self)

    @property
    def raw(self):
        """The underlying Anthropic client, built on first use."""
        if self._raw is None:
            try:
                from anthropic import Anthropic
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "TrackedClient needs the anthropic SDK: "
                    "pip install 'llm-run-guard[anthropic]'"
                ) from e
            self._raw = Anthropic(
                timeout=self._timeout,
                max_retries=self._max_retries,
                **self._client_kwargs,
            )
        return self._raw

    @property
    def messages(self):
        return self._messages

    def __getattr__(self, name):
        # Everything else on the SDK client passes straight through.
        return getattr(self.raw, name)
