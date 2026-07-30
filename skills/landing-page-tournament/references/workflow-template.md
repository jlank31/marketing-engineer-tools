# Workflow script template: landing-page copy tournament

Pass `args` as: `{ copySheet: "<full copy-sheet.md text>", brandBrief: "<full brand-brief.md text>" }`.
The script is self-contained JavaScript (no TS annotations, no Date.now/Math.random).

```javascript
export const meta = {
  name: 'copy-tournament',
  description: 'Landing page copy tournament: 8 writers + baseline, 5-judge panel, merge, compliance gate',
  phases: [
    { title: 'Write', detail: '8 strategy-angle rewrites in parallel' },
    { title: 'Judge', detail: '5 personas rank all versions comparatively' },
    { title: 'Merge', detail: 'per-section winners + grafted keep-lines' },
    { title: 'QC', detail: 'adversarial brand-compliance gate' },
  ],
}

const { copySheet, brandBrief } = args

const ANGLES = [
  { key: 'pain-led', brief: 'Lead with the reader\'s pain. Make the cost of the status quo vivid and specific before any promise. The hero should make the right founder wince in recognition.' },
  { key: 'outcome-led', brief: 'Lead with the concrete outcome and the speed to it. Every section answers "what do I get and how fast". Numbers where verified facts allow.' },
  { key: 'proof-led', brief: 'Lead with operator credibility and built-not-advised proof. The page should feel like hiring a senior operator, not buying a service.' },
  { key: 'objection-led', brief: 'Name and disarm the top objections head-on (another agency? another AI tool? will it sound like me? is the free thing a sales trap?). Honesty as the selling mechanism.' },
  { key: 'icp-mirror', brief: 'Mirror the ICP\'s own language back at them. Write like their inner monologue. They should feel the page was written about them specifically.' },
  { key: 'radical-brevity', brief: 'Fewest words that still sell. Cut every line that does not earn its place. White space is a feature. Aim for roughly half the baseline word count.' },
  { key: 'category-pov', brief: 'A confident point of view on how growth works now (one senior operator with AI tooling vs the old agency/hire model), expressed as direct observation. NO contrarian-reversal phrasing.' },
  { key: 'competitor-fear', brief: 'Write the page a competitor would hate to see: the sharpest honest differentiation, claims only this brand can make, positioning that is hard to copy overnight.' },
]

const JUDGES = [
  { key: 'cfo', persona: 'You are a skeptical CFO reviewing this vendor\'s page before approving spend. You kill unprovable claims, vague ROI language, and fluff. Cross-check EVERY factual claim against the verified proof list in the brand brief; flag anything unverifiable as a kill-line.' },
  { key: 'midnight-founder', persona: 'You are a founder of a 15-person vertical SaaS company scrolling LinkedIn at midnight, tired and skeptical, who lands on this page. You judge purely on: does the hero stop the scroll, do you keep reading, would you actually book the free audit before bed. Attention is your only currency.' },
  { key: 'competitor', persona: 'You are a rival growth consultant studying this page to compete against it. Identify what is generic (you could ship the same line tomorrow), what is copyable, and what genuinely worries you because you cannot match it. Score versions by how hard they would be to compete with.' },
  { key: 'icp-customer', persona: 'You are the ideal customer described in the brand brief\'s ICP section. Judge whether the page sounds like it was written for you specifically, whether you trust it, and whether anything feels off, salesy, or like AI-generated agency copy.' },
  { key: 'copywriter', persona: 'You are a senior conversion copywriter auditing structure: message hierarchy, one idea per section, message match between sections and CTAs, friction, CTA strength, and whether each section moves the reader to the next. Judge craft, not taste.' },
]

const VERSION_SCHEMA = {
  type: 'object',
  properties: {
    copy: { type: 'string', description: 'The complete filled copy sheet in the exact same markdown structure and field labels as the baseline' },
    rationale: { type: 'string', description: '3-5 sentences on the strategic bet this version makes' },
  },
  required: ['copy', 'rationale'],
}

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    rankings: { type: 'array', items: { type: 'object', properties: {
      versionKey: { type: 'string' }, score: { type: 'number', description: '1-10 overall' }, note: { type: 'string' } },
      required: ['versionKey', 'score'] } },
    sectionWinners: { type: 'array', items: { type: 'object', properties: {
      section: { type: 'string' }, versionKey: { type: 'string' }, why: { type: 'string' } },
      required: ['section', 'versionKey', 'why'] } },
    killLines: { type: 'array', items: { type: 'object', properties: {
      versionKey: { type: 'string' }, line: { type: 'string' }, reason: { type: 'string' } },
      required: ['versionKey', 'line', 'reason'] } },
    keepLines: { type: 'array', items: { type: 'object', properties: {
      versionKey: { type: 'string' }, line: { type: 'string' }, reason: { type: 'string' } },
      required: ['versionKey', 'line', 'reason'] } },
    verdict: { type: 'string', description: '2-4 sentence overall take from this persona' },
  },
  required: ['rankings', 'sectionWinners', 'killLines', 'keepLines', 'verdict'],
}

const MERGE_SCHEMA = {
  type: 'object',
  properties: {
    finalCopy: { type: 'string', description: 'Merged copy sheet, same structure and labels as the baseline' },
    rationale: { type: 'string', description: 'Per-section: which version won and why, and which keep-lines were grafted' },
    risks: { type: 'array', items: { type: 'string' } },
    beatBaseline: { type: 'boolean', description: 'Whether the merged page is a clear improvement over the baseline per the judge data' },
  },
  required: ['finalCopy', 'rationale', 'risks', 'beatBaseline'],
}

const QC_SCHEMA = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    violations: { type: 'array', items: { type: 'object', properties: {
      line: { type: 'string' }, rule: { type: 'string' }, fix: { type: 'string' } },
      required: ['line', 'rule'] } },
  },
  required: ['pass', 'violations'],
}

const writerPrompt = (angle) => `You are a senior direct-response copywriter rewriting a landing page.

STRATEGY ANGLE (your bet, commit to it fully): ${angle.brief}

BRAND BRIEF (hard constraints, violations disqualify you):
${brandBrief}

BASELINE COPY SHEET (this defines the exact structure you must fill; FIXED items stay fixed):
${copySheet}

Rewrite EVERY non-fixed field through your strategy angle. Respect every structural limit (word caps) and every banned pattern. Use ONLY verified proof points. Keep the same markdown structure and field labels exactly so versions can be compared field-by-field. Return the full copy sheet and your rationale.`

const judgePrompt = (judge, entrants) => `${judge.persona}

BRAND BRIEF (context for what this brand may and may not claim):
${brandBrief}

Below are ${entrants.length} versions of the same landing page, each as a structured copy sheet with identical field labels. Version "baseline" is the live page today.

${entrants.map(e => `=== VERSION: ${e.key} ===\n${e.copy}`).join('\n\n')}

Judge comparatively, in persona:
1. rankings: score every version 1-10 overall (differentiate; do not cluster everything at 7).
2. sectionWinners: for each major section (HERO, PROBLEM, OFFER LADDER, AUDIT STEPS, PROOF BAND, BEST FOR, MID-PAGE CTAs, SOCIAL PROOF, FINAL CTA), name the single version that wins it and why.
3. killLines: specific lines that must never ship (quote them exactly), with reasons.
4. keepLines: the standout lines that should survive into any merged page (quote exactly).
5. verdict: your overall take in persona.`

// ── Phase 1: Write ──────────────────────────────────────────────────────────
phase('Write')
const written = await parallel(ANGLES.map(a => () =>
  agent(writerPrompt(a), { label: `write:${a.key}`, phase: 'Write', schema: VERSION_SCHEMA })
    .then(v => v && { key: a.key, copy: v.copy, rationale: v.rationale })
))
const entrants = [
  { key: 'baseline', copy: copySheet, rationale: 'The live page as shipped.' },
  ...written.filter(Boolean),
]
log(`${entrants.length} entrants (including baseline)`)

// ── Phase 2: Judge (barrier correct: every judge needs every version) ───────
phase('Judge')
const judgments = await parallel(JUDGES.map(j => () =>
  agent(judgePrompt(j, entrants), { label: `judge:${j.key}`, phase: 'Judge', schema: JUDGE_SCHEMA })
    .then(r => r && { judge: j.key, ...r })
))
const validJudgments = judgments.filter(Boolean)
log(`${validJudgments.length}/5 judges reported`)

// ── Phase 3: Merge ──────────────────────────────────────────────────────────
phase('Merge')
const merged = await agent(`You are the head of merge for a landing-page copy tournament.

BRAND BRIEF:
${brandBrief}

ENTRANTS:
${entrants.map(e => `=== VERSION: ${e.key} (bet: ${e.rationale}) ===\n${e.copy}`).join('\n\n')}

JUDGE PANEL RESULTS (5 personas, comparative):
${JSON.stringify(validJudgments, null, 2)}

Build the single best page: for each section take the version the judge data supports, graft in keepLines where they beat the section winner's line, and never include any killLine. Resolve conflicts by favoring (a) claims verifiability, (b) the ideal-customer and midnight-founder judges for the hero, (c) the copywriter judge for structure. Respect all brand-brief constraints and word caps. If the data says the baseline wins a section, keep the baseline copy for that section. Set beatBaseline honestly.`,
  { label: 'merge', phase: 'Merge', schema: MERGE_SCHEMA })

// ── Phase 4: Compliance gate (adversarial, one repair loop) ─────────────────
phase('QC')
let finalCopy = merged.finalCopy
let qc = null
for (let attempt = 0; attempt < 2; attempt++) {
  qc = await agent(`You are an adversarial brand-compliance auditor. Your job is to FAIL this copy if you possibly can.

BRAND BRIEF (the law):
${brandBrief}

COPY UNDER AUDIT:
${finalCopy}

Check character by character for: every banned pattern (including the em dash character —), every structural word cap, every factual claim against the verified proof list, fixed facts still true. Quote each violation exactly. Pass ONLY if you found nothing.`,
    { label: `qc:attempt-${attempt + 1}`, phase: 'QC', schema: QC_SCHEMA })
  if (!qc || qc.pass) break
  log(`QC found ${qc.violations.length} violations, repairing`)
  const repaired = await agent(`Repair this landing-page copy sheet. Fix ONLY the listed violations, changing as little as possible. Keep structure and labels identical.

BRAND BRIEF:
${brandBrief}

COPY:
${finalCopy}

VIOLATIONS TO FIX:
${JSON.stringify(qc.violations, null, 2)}`,
    { label: 'qc:repair', phase: 'QC', schema: VERSION_SCHEMA })
  if (repaired) finalCopy = repaired.copy
}

return {
  entrants,
  judgments: validJudgments,
  merge: { rationale: merged.rationale, risks: merged.risks, beatBaseline: merged.beatBaseline },
  finalCopy,
  qc,
}
```

## Notes for reuse

- **KNOWN BUG (observed 2026-07-13, run wf_8fb3fd96-5a2):** args-interpolated strings (`${copySheet}`, `${brandBrief}`) reached the phase-1 writer agents correctly but arrived as `undefined` in later-phase judge/merge/QC prompts. Mitigation: ALWAYS save copy-sheet.md and brand-brief.md to the run directory before launching the workflow, and include their absolute file paths in every agent prompt ("If the text above reads 'undefined', Read <path> instead") — subagents have file access and recover cleanly. Additionally, run a separate blind head-to-head validation (baseline vs merged, texts embedded directly via the Agent tool) before claiming the merge beat the baseline.

- Adapt `ANGLES` and the `icp-customer` / `midnight-founder` personas to the brand brief's actual ICP; everything else is brand-agnostic.
- The section list inside `judgePrompt` step 2 should match the copy sheet's actual `##` headings.
- Keep the barrier before judging; do NOT pipeline writers into judges (judges need the full field).
- The workflow returns everything needed for the report; write `report.md`, `versions.md`, and `final-copy.md` from the return value in the main loop.
