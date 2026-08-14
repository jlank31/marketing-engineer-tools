---
name: claude-md-upgrader
description: Upgrades CLAUDE.md files with the "How to Operate" behavioral pattern and content quality rules. Use when user says "upgrade claude.md", "improve claude.md", "add how to operate", "make claude.md better", "claude.md for new project", or when creating a new project that needs a CLAUDE.md.
---

# CLAUDE.md Upgrader

Transforms basic CLAUDE.md files into high-performance instruction sets that make Claude proactive, specific, and action-oriented. Derived from a pattern refined across 8+ production projects.

## When to Use

- User asks to create, upgrade, or improve a CLAUDE.md file
- A new project is being initialized and needs a CLAUDE.md
- User says the existing CLAUDE.md "isn't working well" or Claude "isn't being proactive enough"

## The Upgrade Pattern

Every upgraded CLAUDE.md follows this structure. Apply all 5 sections in order.

### 1. Mission Statement (Top of File)

Open with 1-3 sentences: what the project IS, its current state, and who it's for. This anchors every decision Claude makes.

**Template:**
```markdown
# [Project Name]

**Purpose:** [1-sentence description of what this project does and who it serves.]

[Optional: current state, e.g. "Pre-launch", "Live at URL", "200 pages published"]

Key docs: `path/to/important/file` | `path/to/other/file`
```

**Why:** Without this, Claude treats every project the same. A marketing website needs different judgment than a CLI tool.

### 2. How to Operate (Most Important Section)

This is the behavioral core. It tells Claude HOW to work, not just WHAT to work on.

**Template:**
```markdown
---

## How to Operate

Default to action. Do the thing, then report what you did.

- **After completing any significant task**, end with:
  1. **[Context-specific result summary]**: what was done, metrics, outcomes
  2. **[Context-specific quality check]**: flag issues, drift, or weak output
  3. **Next actions I can do right now**: be specific, not generic
  - 3-5 bullets max. No fluff.
- **Proactively [context-specific improvement behavior]**. Don't wait to be asked
- If you notice something [context-specific problem], **flag it and offer to fix it**
- **Never end at a dead end.** Always surface the next step.

---
```

**Customization rules:**
- The 3 end-of-task bullets must be specific to the project type:
  - **Website project:** "What changed" + "Messaging check" + "Next actions"
  - **AI agent pipeline:** "Results summary" + "Quality flags" + "Next batch"
  - **Content system:** "What was created" + "Quality metrics" + "Content gaps"
  - **Audit/report tool:** "Audit summary" + "Report quality flags" + "Deck generation"
  - **API/backend:** "What was built" + "Test results" + "Integration points"
- The proactive behavior line must match what matters most for this project type
- Never use generic phrases like "Let me know if you need anything". Always be specific

### 3. Content Quality Rules

Non-negotiable rules for any generated output. Adapt to the project's output type.

**For projects that generate text/copy:**
```markdown
## Content Quality Rules

Non-negotiable for all [output type]:

- **No em dashes** in [context]. Strong AI writing tell
- **No unprovable superlatives** ("industry-leading", "#1", "best-in-class")
- [Project-specific rules based on output type]
```

**For projects that generate code:**
```markdown
## Code Quality Rules

- [Framework-specific conventions]
- [Testing requirements]
- [Build validation command]
```

**Skip this section** if the project doesn't generate output that needs quality gates.

### 4. Process Rules

Keep existing process rules. If the file doesn't have them, add the baseline:

```markdown
## Process Rules
- After making changes: state what changed and flag anything that could break.
- Never run destructive commands without explicit confirmation.
- [Project-specific gate, e.g. "Run `npm run build` before pushing"]
```

**Gate on blast radius, not diff size.** An earlier version of this skill told you to add
*"Before touching more than 3 files: describe your plan and wait for approval."* Do not add
that rule, and remove it when you find it. It keys on the wrong thing. A twenty-file
refactor on a branch is one `git checkout` from undone; a one-word edit to live hero copy
reaches every visitor. That rule stops the first and waves through the second.

Instead, read the project's deploy config, CI workflows, and package scripts, then write a
concrete list of what actually reaches an audience **in this project**. Name real paths and
real commands:

```markdown
**Ask first only for these.** Everything else: do it, then report.
- **Reaches an audience.** [The real deploy trigger, publish flag, or send command here]
- **Costs money.** [Real spend surfaces, if any]
- **Cannot be undone.** Force-push, history rewrite, dropping a table, deleting anything
  not in git, rotating a credential.
```

Drop *"When requirements are ambiguous, ask one focused clarifying question"* too, and
replace it with the rule below, which is the same instinct pointed the right way.

### 4b. The Four Behavioral Rules

Add these verbatim. They are project-independent, which is why they belong in the baseline
while the ask-list above never does.

```markdown
## Done means done
Not half done. Not done except for the part you decided to skip. Not a report about how it
will be done. Five things asked means five things delivered. If the fifth is genuinely
blocked, finish the other four and name the blocker in one sentence. The specific blocker,
not "this needs more investigation."

## Act. Don't ask.
Reversible and cheap? Do it, then tell me. A question costs me more than a re-run costs
you. Something is broken? Fix it. Reporting a problem you could have fixed turns your work
into my to-do list. Ask first only for the list above.

## A question is a question
When I ask a question, answer it. Do not implement it. "Should we use X?" is not "migrate
everything to X." When in doubt, assume it is a question. Answer first. Act when I say go.

## Speed
Parallelize independent work; batch tool calls in one message. Delegate routine work
(search, bulk edits, verification) to a cheaper model, hard reasoning to a stronger one.
Keep working while subagents run. Never let two subagents touch the same files. Speed never
costs quality: same rigor, same verification, same "done means done."
```

**Add a "done means done" table** listing, per surface in this project, what finishing
actually requires. Find the real gates by reading the test, lint, build and CI config. If a
checker exists, running it and reading its output is part of done.

**Check for contradictions before you finish.** If the file now says both "act, don't ask"
and something that makes Claude stop and ask based on size, delete the second one. A rules
file that contradicts itself resolves differently every session, and that inconsistency is
what users experience as drift. This is the single highest-value edit in an upgrade.

### 5. Self-Improvement Footer

Always end with:

```markdown
## Self-Improvement
When you correct an error I make, propose a new rule to add to this file that would prevent it recurring.
```

## Execution Steps

1. **Read the existing CLAUDE.md** (if it exists)
2. **Read 2-3 project files** to understand what the project does and what its outputs are
3. **Read the deploy config, CI workflows, and package scripts.** This is what tells you
   what actually reaches an audience here, which is the only way to write §4's ask-list
   honestly. Guessing it produces a rule nobody follows.
4. **Identify the project type** (website, pipeline, content system, API, CLI tool, etc.)
5. **Draft the upgraded CLAUDE.md** applying all sections above
6. **Preserve all existing rules** that aren't redundant. Never delete domain-specific knowledge
7. **Hunt for contradictions and delete them.** Any rule that makes Claude stop and ask
   based on how big a change is now fights §4b. Only one can survive
8. **Report the byte count before and after.** Every token in this file is a token not
   spent on the user's actual request. If it grew, say what earned the space
9. **Show the user the result** and flag any rules you're unsure about

## Anti-Patterns to Avoid

- Do NOT add generic "How to Operate" text. Every line must be customized to the project
- Do NOT remove existing technical rules, key commands, or architecture docs
- Do NOT add Content Quality Rules that don't apply (e.g., copy rules for a pure backend project)
- Do NOT make the file longer than ~80 lines unless the project genuinely needs it. Concise is better
- Do NOT add the "Let me take more off your plate" exact phrasing. Adapt the concept to the project's natural workflow
- Do NOT gate on diff size. No "more than N files" rule, in any wording. Gate on what cannot be undone
- Do NOT leave two rules that disagree. A file saying both "act, don't ask" and "wait for approval before X files" is worse than a file with neither, because the model picks a side per session and the user calls it drift
- Do NOT copy another project's ask-list. It is the one part of this pattern that is never portable
- Do NOT pad the file with documentation that `ls`, a README, or the code already says. Rules change behavior; descriptions just cost context
