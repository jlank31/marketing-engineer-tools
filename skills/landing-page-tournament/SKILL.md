---
name: landing-page-tournament
description: >
  Run a copy tournament on any landing page: 8 rewrites from distinct strategy angles
  plus the live copy as a baseline entrant, judged comparatively by a 5-persona panel
  (skeptical CFO, midnight founder, competitor, ideal customer, conversion copywriter),
  merged per-section, then passed through an adversarial brand-compliance gate.
  Output is a scored report and a recommended final copy sheet. Never auto-ships.
  Use when the user says "copy tournament", "tournament this page", "run the tournament
  on <page/url>", or wants multi-perspective stress-testing of landing page copy.
---

# Landing Page Copy Tournament

Multi-agent stress test for landing page copy, adapted from the "write it 8 ways, judge it 5 ways" tournament pattern. Three deliberate upgrades over the naive version:

1. **The live copy competes.** The current page enters as the baseline. If no rewrite beats it, that is a valid, cheap outcome, and you know the page is already strong.
2. **Comparative judging, not isolated scores.** Each judge reads ALL versions in one call and ranks them per-section. Isolated 1-per-call scoring produces halo-effect score compression and costs 9x more.
3. **Grounded judges.** Writers and judges receive the brand brief as hard constraints. Ungrounded judges reward generic punchy copy that violates brand guardrails.

**Hard rule: the tournament never auto-ships.** The output is a recommendation report. Applying the winning copy to the site is a separate, human-approved step.

## Inputs

- **Target page**: file path(s) or URL. For component-based sites (Astro/Next), read the section components and data files, not the rendered HTML.
- **Brand context**: auto-detect in this order: a brand guide (e.g. `marketing/brand-guide/BRAND-GUIDE.md`), copy/messaging rules in the project's CLAUDE.md, an existing copywriting skill. If none found, ask the user for positioning, ICP, voice rules, and verified proof points before proceeding. Never run ungrounded.
- **N versions** (default 8) and judge panel (default 5, below).

## Process

### Step 1: Extract the copy sheet (inline, no agents)
Read the page source and produce a structured section-by-section copy sheet: every headline, subhead, card, list item, CTA label, with its structural limit noted (e.g. "h1, max 8 words"). Fixed facts (offer names, prices, deliverables) are marked FIXED and excluded from rewriting. FAQ/schema copy is out of scope by default (different job than persuasion copy). This sheet is the shared skeleton: every version fills the same fields so judging and merging work at section granularity.

### Step 2: Build the brand brief (inline)
Condense the brand context into one grounding doc: positioning, ICP, voice do/don'ts, structural limits, the banned-patterns list, and the list of VERIFIED proof points with the explicit rule that any other claim is fabrication and disqualifies a version.

Save both artifacts to the run directory (see Output) before launching agents.

### Step 3: Run the tournament (Workflow tool)
Use the script in `references/workflow-template.md`. Shape:

- **Write phase** (parallel): N writer agents, one per strategy angle (pain-led, outcome-led, proof-led, objection-led, ICP-language-mirror, radical-brevity, category-POV, competitor-fear). Each gets copy sheet + brand brief and returns a complete filled copy sheet plus strategy rationale. Baseline joins the pool unmodified.
- **Judge phase** (parallel, after all writers; the barrier is correct because judges need every version): 5 personas, each ranks all versions overall AND names a winner per section, plus explicit kill-lines and keep-lines with reasons. Default panel:
  - **Skeptical CFO**: hunts unprovable claims, vague ROI, fluff. Cross-checks every claim against the verified proof list.
  - **Founder scrolling at midnight**: tired, skeptical, thumb hovering. Does the hero stop the scroll? Would they actually book?
  - **Competitor**: a rival agency/consultant. What is generic, what is copyable overnight, what is actually defensible?
  - **Ideal customer**: parameterized from the ICP in the brand brief. Does this sound like it is for me? Do I trust it?
  - **Conversion copywriter**: hierarchy, one idea per section, message match, friction, CTA strength.
- **Merge phase** (1 agent): aggregates the score matrix, picks the per-section winner, grafts judge-flagged keep-lines, returns merged copy sheet + rationale + risks.
- **Compliance gate** (1 agent, adversarial): tries to FAIL the merged sheet against the banned list, structural limits, and claim verifiability. One repair loop if it fails; if it fails twice, ship the report with violations flagged for the human.

### Step 4: Report
Write to the run directory:
- `report.md`: executive summary, judge-by-judge verdicts, score matrix, per-section winner + why, kill-line highlights, risks, recommendation.
- `versions.md`: all entrant copy sheets with strategy rationales.
- `final-copy.md`: the merged, compliance-passed copy sheet, diffed against the baseline.

## Output location

- Default: `docs/copy-tournament-<date>/`.
- If the project already has a decisions/artifacts convention, follow it instead.

## Quality gates

- Every version fills every copy-sheet field. Partial versions are disqualified before judging.
- Any fabricated claim, banned pattern, or structural-limit violation is a kill, not a deduction.
- The report must state clearly whether the merged copy actually beat the baseline, and by how much, per judge.
- If the baseline wins overall, say so plainly. Do not manufacture a rewrite to justify the run.

## References

- `references/workflow-template.md`: the Workflow script skeleton, writer-angle roster, judge persona prompts, and JSON schemas.
