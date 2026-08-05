---
name: project-cheat-sheet
description: >
  Generate a project-specific Claude skill cheat sheet that encodes component inventory,
  data models, agent responsibilities, naming conventions, canonical file paths, and
  known gotchas into a ~/.claude/skills/[project]/SKILL.md. Future sessions auto-load
  this context instead of re-deriving it, reducing re-reading and repeated questions.
  Use when starting work on a project repeatedly, after a major refactor, or when
  Claude keeps asking questions it should already know. Triggers on: "create cheat sheet
  for", "project cheat sheet", "generate project skill", "encode project context",
  "make a skill for [project]", "project-specific skill", "stop re-reading files".
---

# Project Cheat Sheet Generator

Encodes a project's architecture, conventions, and gotchas into a reusable skill so
every future session starts with full context pre-loaded: no re-reading, no re-asking.

## When to Use
- Claude repeatedly reads the same files across sessions to derive context it should already have
- Starting regular work on a project that doesn't yet have a cheat sheet
- After a major refactor that obsoletes the existing cheat sheet
- When Claude asks questions it should already know (agent names, file paths, DB schema, component names)

---

## Process

### Step 1: Identify the Project
Ask (or infer from context): which project? Confirm the root path.

### Step 2: Gather Context
Read in this order, stopping when you have enough to fill all sections:

1. `[project]/CLAUDE.md`: conventions, rules, stack, model routing
2. `[project]/README.md`: overview if exists
3. For Python agent projects: all files in `agents/`, `workflows/`, `utils/`, `prompts/`
4. For Astro/frontend projects: `src/components/`, `src/content/`, `src/styles/global.css`, `src/pages/`
5. For knowledge/strategy projects: `INDEX.md`, top-level `.md` files
6. Any `requirements.txt`, `package.json`, or config files for stack/dependency context

### Step 3: Extract by Project Type

**Python agent projects** (marketing-ai, seo-ai, website-auditor, social-reel-scraper):
- Agent names, one-sentence responsibilities, model assignments
- Workflow order: which agent calls which, in what sequence
- Tool/function inventory per agent
- Data models: Pydantic classes, SQLite tables, Google Sheets columns, JSON schemas
- Key file paths: input dirs, output dirs, credentials, state files (never delete list)
- Environment variables required (names only, not values)
- Run commands for common tasks
- Known failure modes: API limits, encoding issues, auth quirks, common errors

**Astro/frontend projects** (another-project, your-website):
- Component inventory: name, path, what it renders
- Content collection schemas: collection name, required fields, optional fields
- Design tokens: color names from `@theme`, typography scale, spacing scale
- Page/route inventory: all existing routes and their purpose
- Key layout/template components
- Build gotchas: things that break `npm run build` silently
- Run commands

**Strategy/knowledge projects** (co-founder, social-reel-scraper KB):
- What the knowledge base covers and how it's organized
- Which files to load for which use case
- Current state summary (decision already made, active workstreams)
- Files that must always be loaded together

### Step 4: Write the Cheat Sheet

Write to: `~/.claude/skills/[project-name]/SKILL.md`

Use this template:

```markdown
---
name: [project-name]
description: >
  Project-specific cheat sheet for [project name]. [One sentence: what it does].
  Auto-load for any work in this project. Triggers on: "[project name]", "[key agent
  or component names]", "[main workflow keywords]", "[key file names]".
---

# [Project Name]: Project Context

[One sentence: what this project does and why it exists.]

**Path:** `[root path relative to ~/projects/Claude/]`
**Stack:** [e.g., Python 3.11 + Anthropic SDK + SQLite, or Astro 5 + Tailwind v4]
**Run:** `[most common command]`

---

## [Section based on type, see Step 3 above]

[Fill in extracted content. Be specific. Generic descriptions defeat the purpose.]

---

## Known Gotchas
- [Concrete thing Claude should never re-ask or re-derive]
- [e.g., "Never delete data/processed.json, it tracks pipeline state"]
- [e.g., "mdx fences (```mdx) break the Astro build, use plain content blocks"]
```

### Step 5: Confirm
Report:
- File written to (exact path)
- How many sections filled
- Top 3 trigger phrases that will activate it
- Whether it replaced an existing cheat sheet

---

## Quality Bar

A good cheat sheet makes a cold session feel like a warm one. Test it mentally:
if someone opened a new Claude Code session, mentioned the project name, and asked
a routine task. Would they need to read any files first? If yes, the cheat sheet is
missing something.

Bad cheat sheet: "The project has agents that do research and email writing."
Good cheat sheet: "Maya (Sonnet 4.6) does prospect research via Google Places API +
Perplexity. Jake (Sonnet 4.6) writes HVAC cold emails from Maya's output. Dana
(Haiku 4.5) runs a 7-point QC checklist before emails go to the Sheet."
