# Contributing

Short version: bug reports are welcome, price-table updates are actively wanted, and some files here can't be edited directly. Details below so nothing wastes your time.

## Some files are mirrored from a private upstream

`packages/prose-tells/src/prose_tells/content_quality.py` and `repetition.py` are maintained in a private repository and copied here. `packages/prose-tells/VENDORED.sha256` records their hashes, and CI fails if either is edited in place.

This isn't gatekeeping. Those detectors run against live client content in a production pipeline, and that pipeline has to be able to fix a rule the same night something slips through — without waiting on a release here. Making the private copy authoritative is what buys that.

**A patch to a mirrored file is still welcome.** Open the PR normally. It gets applied upstream and lands here on the next sync, credited to you. It just won't merge as-is, and CI will say so rather than leaving you guessing.

Everything else in the repo — the CLI, profiles, tests, tooling, docs, skills — you can edit directly.

## What gets accepted

**Actively wanted:** price-table corrections in `llm-run-guard` (when it lands). A published price table goes stale within months, and a cost tool reporting stale numbers is worse than no cost tool. These are trivial to review and keep the package honest.

**Welcome:** false positives. A detector that fires on good writing is a real defect — these are deliberately tuned to under-report, so a rule that cries wolf undermines the whole set. Send the exact text.

**Welcome:** bugs, crashes, packaging problems, docs that are wrong.

**Usually declined:** new detectors and new features. Not because they're bad ideas — because every rule here earns its place by having caught something real in production, and I can't vouch for one that hasn't. Fork freely; that's what the license is for.

## If you send a detector change

Include two tests: one for the thing it now catches, and one for something that must keep passing. The second matters more. A regex that catches more is easy; a regex that catches more *without* flagging ordinary prose is the actual work.

## Running things locally

```bash
make install      # editable install + test deps
make check        # lint, tests, leak scan, mirror integrity — same as CI
```

## Support expectations

Best effort, usually on weekends. Issues need a minimal reproduction — there's a template. Questions go in [Discussions](https://github.com/jlank31/marketing-engineer/discussions) rather than Issues.

This repo has a stated scope: 12 drops across Aug–Sep 2026, then maintenance mode. Maintenance means bugs and price updates, not new surface area. Saying so up front seems better than going quiet in October and letting you wonder.

## Security

Don't open a public issue for a security problem — see [SECURITY.md](SECURITY.md).
