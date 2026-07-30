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

[Optional: current state — "Pre-launch", "Live at URL", "200 pages published", etc.]

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
  1. **[Context-specific result summary]** — what was done, metrics, outcomes
  2. **[Context-specific quality check]** — flag issues, drift, or weak output
  3. **Next actions I can do right now** — be specific, not generic
  - 3-5 bullets max. No fluff.
- **Proactively [context-specific improvement behavior]** — don't wait to be asked
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
- Never use generic phrases like "Let me know if you need anything" — always be specific

### 3. Content Quality Rules

Non-negotiable rules for any generated output. Adapt to the project's output type.

**For projects that generate text/copy:**
```markdown
## Content Quality Rules

Non-negotiable for all [output type]:

- **No em dashes** in [context] — strong AI writing tell
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
- Before touching more than 3 files: describe your plan and wait for approval.
- When requirements are ambiguous: ask one focused clarifying question before proceeding.
- After making changes: state what changed and flag anything that could break.
- Never run destructive commands without explicit confirmation.
```

Add project-specific rules as needed (e.g., "Run `npm run build` before pushing").

### 5. Self-Improvement Footer

Always end with:

```markdown
## Self-Improvement
When you correct an error I make, propose a new rule to add to this file that would prevent it recurring.
```

## Execution Steps

1. **Read the existing CLAUDE.md** (if it exists)
2. **Read 2-3 project files** to understand what the project does and what its outputs are
3. **Identify the project type** (website, pipeline, content system, API, CLI tool, etc.)
4. **Draft the upgraded CLAUDE.md** applying all 5 sections above
5. **Preserve all existing rules** that aren't redundant — never delete domain-specific knowledge
6. **Show the user the result** and flag any rules you're unsure about

## Anti-Patterns to Avoid

- Do NOT add generic "How to Operate" text — every line must be customized to the project
- Do NOT remove existing technical rules, key commands, or architecture docs
- Do NOT add Content Quality Rules that don't apply (e.g., copy rules for a pure backend project)
- Do NOT make the file longer than ~80 lines unless the project genuinely needs it — concise is better
- Do NOT add the "Let me take more off your plate" exact phrasing — adapt the concept to the project's natural workflow
