# marketing-engineer-tools

**Purpose:** Free Python tools for people who publish with AI. Three packages:
`robot-check` (writing-quality detectors), `llm-cost` (price tables and cost math),
`editor-rules` (editor config). Plus `skills/` for Claude Code.

**Public repo, MIT, real users.** Every guardrail here exists because something went wrong
once in a production pipeline. Rules carry the date and the failure in a comment. That is
the standard for adding one, and it is why most new-detector proposals are declined.

**Stated scope:** 8 drops across Aug to Sep 2026, then maintenance. Maintenance means bugs
and price updates, not new surface area.

Key docs: `CONTRIBUTING.md` | `SECURITY.md` | `ROADMAP.md`

---

## How to Operate

## Done means done

Not half done. Not done except for the part you decided to skip. Not a report about how it
will be done.

Five things asked means five things delivered, however long they take. If the fifth is
genuinely blocked, finish the other four and name the blocker in one sentence. The specific
blocker, not "this needs more investigation."

| Surface | Done means |
|---|---|
| Any code change | `make check` passes. That is lint, tests, leak scan and mirror integrity, the same four things CI runs |
| A detector change | Two tests: one for what it now catches, one for ordinary prose that must keep passing. **The second matters more** |
| A price-table change | Sourced from the vendor's published page, and the source is in the diff |
| A docs change | Every path and command in it actually exists |

If you skipped a gate, say which one and why, in the same message. A skipped gate reported
later is a gate that did not exist.

## Act. Don't ask.

Reversible and cheap? Do it, then tell me. Research, reading the code, drafts, refactors,
running `make check`, writing tests, fixing docs. A question costs me more than a re-run
costs you.

Something is broken? Fix it. Reporting a problem you could have fixed turns your work into
my to-do list.

**Ask first only for these.** The gate is blast radius, not diff size. A twenty-file
refactor is `git checkout` away from undone. A release is public the moment it lands.

- **Reaches an audience.** Cutting a release (`release.yml`), publishing to PyPI, pushing
  to `main`, or anything that changes what an installed user gets.
- **Speaks to a real person.** Replying to an issue, a discussion, or a pull request.
  Community threads are people, and the response rate here is deliberately "best effort,
  usually weekends", not instant.
- **Loosens a detector.** These are tuned to under-report on purpose. Making one fire less
  is a product decision, not a bug fix.
- **Cannot be undone.** Force-push, history rewrite, deleting anything not in git,
  rotating a credential, publishing a version number.

## A question is a question

When I ask a question, answer it. Do not implement it. "Should we add a detector for X?"
is not "add the detector." Given that most new detectors are declined by policy, this one
matters here more than usual.

When in doubt, assume it is a question. Answer first. Act when I say go.

## Speed

Parallelize independent work; batch tool calls in one message. Delegate routine work
(search, bulk edits, verification) to a cheaper model and hard reasoning to a stronger one.
Keep working while subagents run. Never let two subagents touch the same files. Speed never
costs quality: same rigor, same verification, same "done means done."

---

## Three files cannot be edited here

`content_quality.py`, `repetition.py` and `post_validators.py` under
`packages/robot-check/src/robot_check/` are mirrored from a private upstream.
`packages/robot-check/VENDORED.sha256` records their hashes and CI fails on an in-place
edit. `make mirror` checks the same thing locally.

**Do not edit them to make a test pass.** The fix goes upstream, then `make promote`. A
contributor's patch to one of these is still welcome as a PR; it gets applied upstream and
lands here on the next sync.

## Process Rules

- `make install` before anything, then `make check` before pushing.
- Nothing private goes in this repo. `make leak` scans for credentials, identifiers and
  client references, and it is the reason it can stay public.
- Detectors keep the dated comment explaining what they caught. That comment is the
  argument for the rule; deleting it makes the rule unjustifiable later.
- Docs claim only what the code does. This repo's whole pitch is that none of it is
  theoretical.

## Self-Improvement

When you correct an error I make, propose a new rule for this file that would prevent it
recurring.
