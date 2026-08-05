"""Tests for editor-rules, written against the ways this goes wrong."""

from __future__ import annotations

import json

import pytest
from editor_rules import compute, load, normalize, render_prompt_block, render_report
from editor_rules.cli import main as cli_main


def pairs(before, after, n):
    return [{"original_text": before, "edited_text": after} for _ in range(n)]


def test_finds_a_recurring_substitution():
    d = compute(pairs("we utilize vendors", "we use brands", 5))
    assert any(b == "utilize vendors" and a == "use brands" for b, a, _ in d.substitutions)


def test_finds_a_recurring_deletion():
    d = compute(pairs("it is very slow", "it is slow", 5))
    assert any(p == "very" for p, _ in d.deletions)


def test_a_one_off_is_not_a_pattern():
    """The threshold is the whole point. Two occurrences is a coincidence."""
    d = compute(pairs("we utilize vendors", "we use brands", 2), min_count=3)
    assert d.empty


def test_prompt_block_excludes_diff_artifacts():
    """The load-bearing filter.

    A heavy rewrite produces alignment artifacts like
    "aren't" -> "and founders are already". Those read as confident instructions
    and would teach the model something false, so the prompt block drops any swap
    where the replacement GREW.
    """
    # "aren't" -> "are already": short enough to survive compute(), but the
    # replacement GREW, which is the signature of a diff artifact.
    edits = pairs("founders aren't ready", "founders are already ready", 5)
    d = compute(edits)
    artifact = [(b, a) for b, a, _ in d.substitutions if len(a.split()) > len(b.split())]
    assert artifact, "fixture should produce a growing substitution"

    block = render_prompt_block(d)
    for before, after in artifact:
        assert after not in block, f"artifact {before!r} -> {after!r} leaked into the prompt"


def test_report_keeps_what_the_prompt_block_drops():
    """Conservative for the machine, permissive for the human."""
    d = compute(pairs("founders aren't ready", "founders are already ready", 5))
    assert "(report only)" in render_report(d)


def test_empty_prompt_block_beats_a_wrong_one():
    assert render_prompt_block(compute([])) == ""


def test_report_is_helpful_when_there_is_nothing_yet():
    out = render_report(compute(pairs("a b c", "a b d", 1)))
    assert "No recurring patterns yet" in out


@pytest.mark.parametrize("keys", [
    ("original_text", "edited_text"),
    ("before", "after"),
    ("old", "new"),
    ("original", "edited"),
])
def test_accepts_the_column_names_people_actually_use(keys):
    b, a = keys
    assert normalize([{b: "utilize", a: "use"}]) == [
        {"original_text": "utilize", "edited_text": "use"}
    ]


def test_rows_missing_a_side_are_skipped_not_fatal():
    assert normalize([{"before": "x"}, {"after": "y"}, {"before": "a", "after": "b"}]) == [
        {"original_text": "a", "edited_text": "b"}
    ]


def test_loads_jsonl_json_and_csv(tmp_path):
    rows = [{"original_text": "utilize", "edited_text": "use"}]

    j = tmp_path / "e.jsonl"
    j.write_text("\n".join(json.dumps(r) for r in rows))
    assert load(j) == rows

    js = tmp_path / "e.json"
    js.write_text(json.dumps(rows))
    assert load(js) == rows

    c = tmp_path / "e.csv"
    c.write_text("before,after\nutilize,use\n")
    assert load(c) == rows


def test_malformed_jsonl_lines_are_skipped(tmp_path):
    f = tmp_path / "e.jsonl"
    f.write_text('{"before":"a","after":"b"}\nNOT JSON\n\n{"before":"c","after":"d"}\n')
    assert len(load(f)) == 2


def test_unsupported_extension_is_a_clear_error(tmp_path):
    f = tmp_path / "e.txt"
    f.write_text("x")
    with pytest.raises(ValueError, match="unsupported file type"):
        load(f)


def test_determinism():
    edits = pairs("we utilize vendors", "we use brands", 5)
    assert compute(edits).substitutions == compute(edits).substitutions


# ---------------------------------------------------------------- CLI

def test_cli_json_output(tmp_path, capsys):
    f = tmp_path / "e.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in pairs("utilize x", "use x", 5)))
    assert cli_main([str(f), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["pairs_analyzed"] == 5


def test_cli_missing_file_is_usage_error(tmp_path):
    assert cli_main([str(tmp_path / "nope.jsonl")]) == 2


def test_cli_thin_corpus_explains_itself(tmp_path, capsys):
    f = tmp_path / "e.jsonl"
    f.write_text(json.dumps({"before": "a b", "after": "a c"}))
    rc = cli_main([str(f), "--prompt-block"])
    assert rc == 1
    assert "thin corpus" in capsys.readouterr().err


def test_cli_writes_to_a_file(tmp_path):
    f = tmp_path / "e.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in pairs("utilize x", "use x", 5)))
    out = tmp_path / "rules.md"
    assert cli_main([str(f), "--prompt-block", "--out", str(out)]) == 0
    assert "use" in out.read_text()
