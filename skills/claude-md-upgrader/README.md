# CLAUDE.md Upgrader

A Claude Code skill. Rewrites a project's `CLAUDE.md` so the assistant behaves
like a teammate who knows the project instead of a stranger reading it fresh.

```bash
git clone https://github.com/jlank31/marketing-engineer-tools
cd marketing-engineer-tools && ./tools/install_skills.sh
```

Then, in Claude Code:

```
upgrade claude.md
```

## What it changes

Most `CLAUDE.md` files are a list of facts. That produces an assistant that
answers exactly what you asked and stops. This rewrites the file around a
behavioral pattern instead:

- **How to operate**: what to do after finishing a task, when to flag a problem
  it noticed on the way past, what never to do without asking
- **Content quality rules**: the specific things that make output wrong for
  *this* project, written as rules rather than preferences
- **Process rules**: when to stop and ask, when to just act

The pattern came out of 8+ production projects, and the parts that survived are
the parts that changed behavior rather than the parts that sounded good.

## When to use it

When you're setting up a new project, or when you notice you keep giving the
same correction twice.

Part of [marketing-engineer-tools](https://github.com/jlank31/marketing-engineer-tools).
MIT licensed.
