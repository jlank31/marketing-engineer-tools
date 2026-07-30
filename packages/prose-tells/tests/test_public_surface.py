"""Tests a stranger would write. Deliberately not a copy of the upstream suite.

The detector logic is already covered by ~1,400 lines of tests in the private
repo, and those port over separately. What those tests do NOT cover is the thing
most likely to break for someone who just ran `pip install`:

  - does importing the package work with no environment at all?
  - does the CLI run, and are its exit codes usable in CI?
  - do the presets round-trip through JSON?
  - is the "zero dependencies" claim actually true?

That last one is the product claim, so it gets a mechanical check rather than a
promise in a README.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import prose_tells
import pytest
from prose_tells import Profile, check_text
from prose_tells.cli import main as cli_main
from prose_tells.profiles import PRESETS, from_dict, to_dict

SRC = Path(prose_tells.__file__).parent


# ---------------------------------------------------------------- import surface

def test_imports_with_no_environment():
    """No API key, no config file, no env var should be required to import."""
    assert prose_tells.__version__
    assert callable(check_text)


def test_advertised_names_are_exported():
    for name in prose_tells.__all__:
        assert hasattr(prose_tells, name), f"__all__ promises {name} but it is missing"


# ---------------------------------------------------------------- the core claim

def test_package_has_zero_third_party_imports():
    """"Zero dependencies" is the product claim, so verify it rather than assert it.

    Walks the whole AST, not just module-level nodes: an import inside a function
    body breaks the contract exactly as hard and is far easier to miss in review.
    """
    offenders: list[str] = []
    for py in sorted(SRC.rglob("*.py")):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # relative import, within the package
                    continue
                names = [node.module] if node.module else []
            else:
                continue
            for n in names:
                root = n.split(".")[0]
                if root not in sys.stdlib_module_names and root != "prose_tells":
                    offenders.append(f"{py.name}: {n}")
    assert not offenders, "third-party imports found: " + ", ".join(offenders)


# ---------------------------------------------------------------- detection

def test_flags_a_known_tell():
    result = check_text("In today's fast-paced landscape, brands must adapt.", Profile())
    assert result.issues


def test_clean_text_passes():
    text = "We shipped the change on Tuesday. Two clients noticed within a day."
    assert not check_text(text, Profile()).issues


@pytest.mark.parametrize(
    "text",
    [
        "It's not a tooling problem. It's a distance problem.",
        "That's not the issue. It's the process.",
        "The gap isn't talent. It's distance.",
    ],
)
def test_reversal_pattern_including_contracted_auxiliary(text):
    """The contracted form ("It's not X. It's Y.") was missed until 2026-07-29.

    Found by running this very package over sample copy while packaging it, which
    is a decent argument for shipping your own tools.
    """
    assert check_text(text, Profile()).issues


# ---------------------------------------------------------------- profiles

@pytest.mark.parametrize("name", sorted(PRESETS))
def test_presets_round_trip_through_json(name):
    original = PRESETS[name]
    restored = from_dict(json.loads(json.dumps(to_dict(original))))
    assert to_dict(restored) == to_dict(original)


def test_unknown_profile_key_is_loud():
    """A typo that silently disables a detector is the worst kind of quiet."""
    with pytest.raises(ValueError, match="unknown profile key"):
        from_dict({"rythm_floor": 0.5})  # deliberate misspelling


# ---------------------------------------------------------------- CLI contract

def test_cli_exit_codes(tmp_path, capsys):
    clean = tmp_path / "clean.md"
    clean.write_text("We shipped the change on Tuesday. Two clients noticed.")
    assert cli_main(["scan", str(clean)]) == 0

    dirty = tmp_path / "dirty.md"
    dirty.write_text("In today's fast-paced landscape, we must delve deeper.")
    assert cli_main(["scan", str(dirty)]) == 1

    assert cli_main(["scan", str(tmp_path / "nope.md")]) == 2


def test_cli_json_is_parseable(tmp_path, capsys):
    f = tmp_path / "d.md"
    f.write_text("In today's fast-paced landscape, brands must adapt.")
    cli_main(["scan", str(f), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["results"][0]["issues"]
    assert payload["profile"] == "generic"


def test_cli_reads_stdin():
    """`cat draft.md | prose-tells scan -` is the documented pipe form."""
    proc = subprocess.run(
        [sys.executable, "-m", "prose_tells.cli", "scan", "-"],
        input="In today's fast-paced landscape, brands must adapt.",
        capture_output=True, text=True,
    )
    assert proc.returncode == 1
    assert "hollow opener" in proc.stdout.lower()


def test_warnings_alone_do_not_fail_the_run(tmp_path):
    """A linter that blocks on soft signals gets switched off. Codified here."""
    f = tmp_path / "w.md"
    f.write_text("We shipped the change on Tuesday. What's your take?")
    rc = cli_main(["scan", str(f)])
    assert rc == 0


# ---------------------------------------------------------------- corpus command

def test_corpus_finds_verbatim_reuse_and_never_fails(tmp_path):
    """Corpus findings are descriptive, so the command always exits 0.

    Repetition is sometimes a positioning line you want consistent and sometimes
    a rut, and no threshold distinguishes them. Exiting non-zero would make this
    unusable as anything but a gate.
    """
    shared = ("We shipped the review gate on Tuesday and two clients "
              "noticed the difference within a day.")
    (tmp_path / "a.md").write_text(f"First piece.\n\n{shared}\n")
    (tmp_path / "b.md").write_text(f"Second piece.\n\n{shared}\n")

    from prose_tells.corpus import analyze, load_corpus
    report = analyze(load_corpus(tmp_path))
    assert report.verbatim, "identical sentence across two files should be found"
    assert cli_main(["corpus", str(tmp_path)]) == 0


def test_corpus_handles_a_single_file_without_crashing(tmp_path):
    (tmp_path / "only.md").write_text("One document, nothing to compare against.\n")
    assert cli_main(["corpus", str(tmp_path)]) == 0


def test_corpus_bad_directory_is_usage_error(tmp_path):
    assert cli_main(["corpus", str(tmp_path / "nope")]) == 2


def test_corpus_excludes_matching_sections(tmp_path):
    """Production metadata repeats across every file and swamps real findings.

    On a real 10-document archive, a boilerplate image-prompt block produced
    three of the top verbatim hits before this existed.
    """
    boiler = "## Cover Image Prompt\n\nrisograph print in a single bold ink color on cream stock\n"
    (tmp_path / "a.md").write_text(f"Distinct opening for A.\n\n{boiler}")
    (tmp_path / "b.md").write_text(f"Entirely different opening for B.\n\n{boiler}")

    from prose_tells.corpus import analyze, load_corpus
    assert analyze(load_corpus(tmp_path)).verbatim, "boilerplate should match with no exclusion"
    filtered = analyze(load_corpus(tmp_path, exclude_section="image prompt"))
    assert not filtered.verbatim, "excluded section should not count as reuse"


def test_opening_line_skips_metadata_and_headings():
    """Regression: openers were compared as metadata, not prose.

    Every file starting "SEO TITLE: ..." reported as echoing every other one,
    because the compared openers were all the same metadata key — six false pairs
    out of six on a real archive.
    """
    from prose_tells.repetition import opening_line

    doc = ("SEO TITLE: Why Copy Falls Flat\n\n"
           "META DESCRIPTION: Something about copy.\n\n"
           "# The Heading\n\n"
           "Most copy falls flat for one reason.\n")
    assert opening_line(doc) == "Most copy falls flat for one reason."
    assert opening_line("---\ntitle: X\n---\n\nThe real opener.") == "The real opener."


def test_siblings_flag_does_not_crash(tmp_path):
    """Regression: the --siblings path raised TypeError from three wrong signatures."""
    (tmp_path / "old.md").write_text("An earlier piece about review gates.\n")
    target = tmp_path / "new.md"
    target.write_text("A newer piece about review gates.\n")
    assert cli_main(["scan", str(target), "--siblings", str(tmp_path)]) in (0, 1)
