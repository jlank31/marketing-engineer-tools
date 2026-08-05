# Project Cheat Sheet

A Claude Code skill. Writes a permanent cheat sheet for a codebase so your
assistant stops re-deriving the same context every session.

```bash
git clone https://github.com/jlank31/marketing-engineer-tools
cd marketing-engineer-tools && ./tools/install_skills.sh
```

Then, in Claude Code:

```
create a cheat sheet for this project
```

## The problem it solves

Every new session starts cold. The assistant re-reads the same files, re-derives
the same architecture, and asks you the same question it asked on Tuesday. You
pay for that in tokens and in patience.

This writes what it learned into a skill at `~/.claude/skills/[project]/SKILL.md`,
which future sessions load automatically.

## What goes in it

- Component inventory and what each piece is responsible for
- Data models and their real shapes
- Naming conventions the codebase actually follows
- Canonical file paths, so nothing gets guessed
- Known gotchas, which is usually the most valuable section

## The test for a good one

A cold session should feel like a warm one. Imagine handing the cheat sheet to
someone who has never seen the repo and asking for a routine task. If they would
still need to open files first, it isn't specific enough.

Bad: "The project has agents that do research and email writing."

Good: names the agent, the model it runs on, the API it calls, and the file it
lives in.

## When to use it

Starting repeated work on a project, or after a refactor that made the existing
cheat sheet wrong.

Part of [marketing-engineer-tools](https://github.com/jlank31/marketing-engineer-tools).
MIT licensed.
