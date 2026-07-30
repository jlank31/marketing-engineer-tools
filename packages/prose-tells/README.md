# prose-tells

Find the lines that make copy read as machine-written — and get told *why* each one is a problem, not just a probability score.

**Zero dependencies. No API key. No network calls.** Pure functions over strings.

```bash
pip install prose-tells
prose-tells scan draft.md
```

```
FAIL  draft.md  (3 issues, 2 warnings)
    [issue] reversal pattern: "It's not a tooling problem. It's a distance problem."
    [issue] hollow opener: "In today's fast-paced landscape"
    [issue] banned phrase: "that's the whole game"
    [warning] paragraph rhythm variance 0.12 (floor 0.30) — every paragraph is
              nearly the same length, which reads as generated
    [warning] 1 distinct citation domain (floor 3)
```

## How this differs from an AI detector

AI detectors answer *"was this written by a model?"* with a confidence score. That's a useful question for an academic-integrity check and close to useless for an editor, because a score doesn't tell you what to change.

This answers a different question: **"which specific lines read as machine-written, and what should they say instead?"** Every finding quotes the offending text back at you.

It also means this tool doesn't care whether a human or a model wrote the draft. Humans write hollow openers too.

## What it checks

**Lexical** — banned phrases, the "it's not X, it's Y" reversal pattern in both its period and comma-joined forms, hollow openers, essay-scaffold transitions, vague quantifiers, filler intensifiers, engagement-bait closers, AI-tell verbs, placeholder tokens left in copy, chatbot artifacts, false agency, copula avoidance, meta-commentary.

**Statistical** — paragraph rhythm variance (generated prose tends to a uniform paragraph length), sentence-length ceilings, bold-span and all-caps limits.

**Link graph** — count of *distinct* citation domains, excluding your own host.

**Corpus-level**, via `--siblings` — verbatim runs shared with earlier work, opening lines that echo a previous piece, and recycled statistic blocks. This layer exists because the per-text checks structurally cannot see convergence: every piece passes on its own while a library slowly becomes one voice telling one anecdote.

## Usage

```bash
prose-tells scan draft.md                          # one file
prose-tells scan posts/*.md --preset social        # tighter limits for short copy
cat draft.md | prose-tells scan -                  # stdin
prose-tells scan article.md --preset blog --siblings ./published
prose-tells scan drafts/*.md --json                # for CI
prose-tells profile --preset blog > profile.json   # then edit and pass --profile
```

Presets are `generic`, `blog`, and `social`. They're starting points, not recommendations — the honest way to calibrate is to run the scanner over work you already consider good and loosen whatever fires on it.

Exit codes: `0` clean, `1` issues found, `2` bad usage. **Warnings never fail the run.** A linter that blocks a publish on a soft signal gets switched off within a week, and then it protects nothing.

### As a library

```python
from prose_tells import check_text, Profile

result = check_text(draft, Profile())
result.passed        # bool
result.issues        # list[str] — each quotes the offending text
result.warnings      # list[str]
result.stats         # dict
```

Every brand-specific value lives on `Profile`. Nothing in the package hardcodes a house style.

## Provenance

These detectors were extracted from a content pipeline that has published for real clients, every week, since April 2026. Nearly every rule carries a comment recording the specific failure that produced it, including the false positives that were deliberately allowed and why.

That matters more than the rule list. Anyone can publish a list of AI writing tells; knowing which rules survive contact with real publishing is the hard part. Where a rule turned out to be wrong, it gets retracted in public — see the [essays](https://github.com/jlank31/marketing-engineer/tree/main/docs/essays) for three SEO rules I taught and now know were folklore.

## Two honest limits

**This catches tells, not badness.** Clean output is a floor, not a finished piece. In the pipeline these came from, a human still reads everything before it ships.

**The detectors are deliberately conservative** — tuned to miss rather than to false-positive, because a linter that cries wolf gets ignored. Expect under-reporting. If you want a rule to be stricter, that's what `Profile` is for.

## License

MIT. Part of [marketing-engineer](https://github.com/jlank31/marketing-engineer).

Note: `content_quality.py` and `repetition.py` are mirrored from a private upstream and can't be edited directly here — see [CONTRIBUTING.md](https://github.com/jlank31/marketing-engineer/blob/main/CONTRIBUTING.md). Patches are welcome; they get replayed upstream.
