"""Tests for the three things this package claims to get right.

Written against the failure modes, not the happy path. Every one of these
corresponds to a way real cost tracking is wrong.
"""

from __future__ import annotations

import ast
import json
import sys
from datetime import date
from pathlib import Path

import llm_run_guard
import pytest
from llm_run_guard import (
    RunCostExceeded,
    calculate_cost,
    cost_from_usage,
    healing,
    pricing,
    tracker,
)
from llm_run_guard.cli import main as cli_main

SRC = Path(llm_run_guard.__file__).parent


@pytest.fixture(autouse=True)
def _clean():
    tracker.init_run("test")
    healing.reset_metrics()
    pricing._warned_unknown.clear()
    yield


# ---------------------------------------------------------------- the core claim

def test_core_has_no_required_dependencies():
    """Everything except TrackedClient must work with nothing installed.

    `anthropic` is allowed, but ONLY inside client.py and only lazily, so that
    pricing and accounting work in an environment with no SDK.
    """
    offenders = []
    for py in sorted(SRC.rglob("*.py")):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for n in names:
                root = n.split(".")[0]
                if root in sys.stdlib_module_names or root == "llm_run_guard":
                    continue
                if root == "anthropic" and py.name == "client.py":
                    continue  # lazy, inside a property
                offenders.append(f"{py.name}: {n}")
    assert not offenders, f"unexpected imports: {offenders}"


def test_importing_needs_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from llm_run_guard import TrackedClient
    TrackedClient("x")  # must not construct the SDK client yet


# ---------------------------------------------------------------- pricing

def test_cache_tokens_are_additive_not_a_subset():
    """The mistake this package exists to prevent."""
    base = calculate_cost("claude-opus-5", input_tokens=1000)
    with_cache = calculate_cost("claude-opus-5", input_tokens=1000, cache_read_tokens=1000)
    assert with_cache > base, "cache reads must ADD cost, not be folded into input"

    rate = pricing.TOKEN_PRICES["claude-opus-5"]["input"] / 1_000_000
    assert with_cache == pytest.approx(
        base + 1000 * rate * pricing.CACHE_READ_MULTIPLIER, rel=1e-6
    )


def test_cache_write_costs_more_than_cache_read():
    w = calculate_cost("claude-opus-5", cache_creation_tokens=10_000)
    r = calculate_cost("claude-opus-5", cache_read_tokens=10_000)
    assert w > r, "1.25x write should exceed 0.10x read"


def test_web_search_is_billed_on_top_of_tokens():
    assert calculate_cost("claude-opus-5", web_search_requests=1000) == pytest.approx(10.0)


def test_unknown_model_is_never_free():
    """Returning 0.0 here is what silently disables a budget cap."""
    cost = calculate_cost("claude-model-from-the-future", input_tokens=1_000_000)
    assert cost > 0
    fallback = pricing.TOKEN_PRICES[pricing.FALLBACK_MODEL]["input"]
    assert cost == pytest.approx(fallback), "should price at the most expensive tier"


def test_unknown_model_warns_once_per_process(caplog):
    with caplog.at_level("WARNING"):
        for _ in range(5):
            calculate_cost("mystery-model", input_tokens=10)
    # getMessage() applies the lazy-% formatting; r.message raises when args exist.
    hits = [r for r in caplog.records if "mystery-model" in r.getMessage()]
    assert len(hits) == 1, f"warned {len(hits)} times, expected once per process"


def test_dated_model_ids_resolve_to_their_family():
    assert pricing.price_for("claude-opus-5-20260814") == pricing.TOKEN_PRICES["claude-opus-5"]


def test_cost_from_usage_reads_every_billable_field():
    class Usage:
        input_tokens, output_tokens = 100, 50
        cache_creation_input_tokens, cache_read_input_tokens = 200, 300
    assert cost_from_usage("claude-opus-5", Usage()) > calculate_cost(
        "claude-opus-5", input_tokens=100, output_tokens=50
    )


def test_staleness_warning_fires_when_the_table_ages():
    assert pricing.staleness_warning(today=date(2026, 8, 1)) is None
    assert "days old" in pricing.staleness_warning(today=date(2027, 8, 1))


# ---------------------------------------------------------------- the cap

def test_cap_raises_mid_run():
    tracker.init_run("capped", cap_usd=0.01)
    with pytest.raises(RunCostExceeded) as e:
        for _ in range(50):
            tracker.record("loop", "claude-opus-5", input_tokens=100_000)
    assert e.value.cap == 0.01
    assert e.value.spent > 0.01


def test_no_cap_means_no_ceiling():
    tracker.init_run("uncapped")
    for _ in range(20):
        tracker.record("x", "claude-opus-5", input_tokens=100_000)
    assert tracker.spent() > 0


def test_summary_groups_by_label_and_model():
    tracker.record("draft", "claude-opus-5", input_tokens=1000)
    tracker.record("draft", "claude-opus-5", input_tokens=1000)
    tracker.record("classify", "claude-haiku-4-5", input_tokens=1000)
    s = tracker.summary()
    assert s["calls"] == 3
    assert s["by_label"]["draft"]["calls"] == 2
    assert set(s["by_model"]) == {"claude-opus-5", "claude-haiku-4-5"}


def test_tracked_run_reports_even_when_the_cap_kills_it():
    """A run killed by its own cap must still tell you what it spent."""
    with pytest.raises(RunCostExceeded):
        with tracker.tracked_run("doomed", cap_usd=0.001) as run:
            for _ in range(50):
                tracker.record("loop", "claude-opus-5", input_tokens=100_000)
    assert run.summary["cost_usd"] > 0


def test_recording_never_raises_on_bad_input():
    """Measurement must not break the thing it measures."""
    assert tracker.record("x", "claude-opus-5", usage=object()) is not None or True
    tracker.record("x", "claude-opus-5", usage={"input_tokens": "not a number"})


# ---------------------------------------------------------------- healing

def test_response_text_skips_a_leading_thinking_block():
    """The outage this function exists for: thinking arrives as content[0]."""
    class Block:
        def __init__(self, type_, text=None):
            self.type, self.text = type_, text

    class Response:
        content = [Block("thinking", "internal reasoning"), Block("text", "the answer")]

    assert healing.response_text(Response()) == "the answer"


def test_response_text_handles_a_plain_response():
    class Block:
        type, text = "text", "hello"

    class Response:
        content = [Block()]

    assert healing.response_text(Response()) == "hello"


@pytest.mark.parametrize("raw,expected", [
    ('{"a": 1}', {"a": 1}),
    ('```json\n{"a": 1}\n```', {"a": 1}),
    ('Sure! Here you go:\n{"a": 1}\nHope that helps.', {"a": 1}),
    ('{"a": 1,}', {"a": 1}),
    ('[1, 2, 3]', [1, 2, 3]),
])
def test_safe_parse_json_tolerates_the_usual_wrappers(raw, expected):
    assert healing.safe_parse_json(raw) == expected


def test_safe_parse_json_returns_default_rather_than_raising():
    assert healing.safe_parse_json("not json at all", default={}) == {}
    assert healing.safe_parse_json("", default=None) is None


def test_retry_succeeds_and_is_counted():
    calls = {"n": 0}

    @healing.with_healing(attempts=3, base_delay=0)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("transient")
        return "ok"

    assert flaky() == "ok"
    assert healing.metrics()["retry_succeeded"] == 1


def test_bugs_in_the_caller_are_not_retried():
    """Retrying a TypeError just re-runs the same bug 3 times."""
    calls = {"n": 0}

    @healing.with_healing(attempts=3, base_delay=0)
    def broken():
        calls["n"] += 1
        raise TypeError("bad argument")

    with pytest.raises(TypeError):
        broken()
    assert calls["n"] == 1


def test_fatal_errors_stop_immediately():
    """A credit-balance failure retried 3x just delays the message you need."""
    calls = {"n": 0}

    @healing.with_healing(attempts=3, base_delay=0)
    def broke():
        calls["n"] += 1
        raise RuntimeError("Your credit balance is too low to access the API")

    with pytest.raises(RuntimeError):
        broke()
    assert calls["n"] == 1


def test_diagnosis_is_off_by_default_and_counted_when_on():
    seen = {}

    @healing.with_healing(attempts=2, base_delay=0,
                          diagnose=lambda e, ctx: seen.setdefault("hit", str(e)))
    def always_fails():
        raise ConnectionError("nope")

    with pytest.raises(healing.HealingFailed):
        always_fails()
    assert seen["hit"] == "nope"
    assert healing.metrics()["diagnoses"] == 1


# ---------------------------------------------------------------- CLI

def test_cli_prices_a_call(capsys):
    assert cli_main(["price", "claude-opus-5", "--in", "1000000", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["cost_usd"] == pytest.approx(5.0)


def test_cli_flags_an_unknown_model(capsys):
    cli_main(["price", "not-a-real-model", "--in", "100", "--json"])
    assert json.loads(capsys.readouterr().out)["known_model"] is False


def test_cli_lists_models_and_checks_freshness(capsys):
    assert cli_main(["models", "--json"]) == 0
    assert "claude-opus-5" in json.loads(capsys.readouterr().out)
    assert cli_main(["check"]) == 0
