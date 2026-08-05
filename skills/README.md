# Skills

Claude Code skills. Copied into place rather than pip-installed:

```bash
./tools/install_skills.sh
```

It copies rather than symlinks, so a `git pull` here can never silently change
how your agent behaves. Re-run it when you want updates.

Three are here now:

| Skill | What it does |
|---|---|
| [`landing-page-tournament`](landing-page-tournament) | Rewrites a landing page 8 ways, then judges all 9 versions (yours competes) against a 5-person panel. Says so if your current page wins. |
| [`claude-md-upgrader`](claude-md-upgrader) | Rewrites a project's `CLAUDE.md` so the assistant behaves like a teammate instead of a stranger. |
| [`project-cheat-sheet`](project-cheat-sheet) | Writes a permanent project cheat sheet so your assistant stops re-learning the same codebase every session. |

If you already installed an older copy, the script skips anything that exists
rather than overwriting it. Remove the old directory first, then re-run.
