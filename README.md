# marketing-engineer

Production tooling extracted from a content pipeline that has published for real clients, every week, since April 2026.

Not a framework. Not a prompt collection. These are the guardrails that exist because something shipped wrong once — and most of them carry the date and the failure in a code comment, so you can judge for yourself whether the rule earns its place.

**By [Jared Castronova](https://www.linkedin.com/in/jaredcastronova/)** — VP of Content and AI Marketing, JAC Growth Marketing LLC.

---

## Scope, stated up front

**12 drops, one per week, Aug 3 – Sep 21 2026. Then maintenance mode.** This is a deliberate run with an ending, not an abandoned project. When the drops stop, that's the plan working.

## What's here

| Wk | Drop | Status |
|---|---|---|
| 1 | [`prose-tells`](packages/prose-tells) — find the lines that read as machine-written | Aug 3 |
| 2 | [Landing Page Copy Tournament](skills) — 8 rewrites, 5 judges, your live page competes | Aug 10 |
| 3 | `prose-tells fix` — deterministically repair the tells | Aug 17 |
| 4 | CLAUDE.md Upgrader + Project Overlay | Aug 24 |
| 5 | `llm-run-guard` — a cost meter that doesn't lie, and a circuit breaker | Aug 31 |
| 6 | `llm-run-guard` self-healing | Sep 7 |
| 7 | `edit-digest` — learn your editor's style from their edits | Sep 14 |
| 8 | The AEO Retractions + B2B email sequences | Sep 21 |

Bonus, slotting in where a week allows: `prose-tells corpus` (read a whole archive for self-repetition), a pitch deck builder, a marketing-folklore claim registry, an email deliverability checklist.

## Install

```bash
pip install prose-tells          # available Aug 3
prose-tells scan draft.md
```

Skills are copied, not installed:

```bash
./tools/install_skills.sh        # → ~/.claude/skills/
```

## Why the provenance matters more than the rules

Anyone can publish a list of AI writing tells. The list is not the hard part; knowing which rules survive contact with real publishing is.

So every detector here records *why it exists*. A regex with a note saying "this shipped once, on this date, and here's the false positive I deliberately allowed" is a rule you can evaluate. A regex without one is a guess. Where a rule turned out to be wrong, it's retracted in public rather than quietly deleted — see [docs/essays](docs/essays) for three SEO rules I taught and now know were folklore.

Two honest limits:

- **These catch tells, not badness.** Clean output isn't good writing. Every one of these is a floor, and in the pipeline they came from, a human still reads everything before it ships.
- **The detectors are deliberately conservative.** They're tuned to miss rather than to false-positive, because a linter that cries wolf gets switched off. Expect it to under-report.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Contributions: please read [CONTRIBUTING.md](CONTRIBUTING.md) first — some files here are mirrored from a private upstream and can't be edited directly. Price-table updates are the one contribution actively wanted.
