# Support

**Status: active.** 12 drops shipping weekly Aug 3 – Sep 21 2026, then maintenance mode.

Maintenance mode means bugs and price-table updates get fixed. It does not mean new features. That's stated up front so October's quiet doesn't read as abandonment.

## Where to go

| You have | Go to |
|---|---|
| A bug, crash, or false positive | [Issues](https://github.com/jlank31/marketing-engineer/issues/new/choose) — needs a minimal reproduction |
| A question, or "how would I use this for X" | [Discussions](https://github.com/jlank31/marketing-engineer/discussions) |
| A security problem | [SECURITY.md](SECURITY.md) — not a public issue |
| A patch | [CONTRIBUTING.md](CONTRIBUTING.md) — read the mirrored-files note first |

Response is best effort, usually weekends.

## Before filing a false positive

That's the most useful report you can send, so it's worth making it land. Include the exact text, the preset you used, and what you'd have expected. These detectors are tuned to miss rather than over-flag, so a rule firing on ordinary prose is a defect worth fixing rather than a threshold you should just raise.

If you only want it quieter for your own work, `Profile` exists for that:

```bash
prose-tells profile --preset blog > profile.json   # edit, then --profile profile.json
```
