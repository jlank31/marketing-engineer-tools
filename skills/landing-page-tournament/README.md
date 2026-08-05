# Landing Page Copy Tournament

A Claude Code skill. Rewrites a landing page 8 ways, then makes all 9 versions
compete, including the one you already have.

```bash
git clone https://github.com/jlank31/marketing-engineer-tools
cd marketing-engineer-tools && ./tools/install_skills.sh
```

Then, in Claude Code:

```
run the tournament on https://yoursite.com/pricing
```

## What it does

Eight rewrites, each from a distinct strategy angle, plus your live copy entered
as a baseline. All nine go to a 5-persona judging panel:

| Judge | Reads it as |
|---|---|
| Skeptical CFO | Is this worth money, and where's the proof |
| Midnight founder | Tired, scrolling, gives it 4 seconds |
| Competitor | Where is this weak, what would I attack |
| Ideal customer | Is this for someone like me |
| Conversion copywriter | Does the structure actually do work |

Winners get merged per section, so the final sheet can take the headline from
one entrant and the proof block from another. Then the merged copy goes through
an adversarial brand-compliance gate before you see it.

## Two things worth knowing

**Your current copy can win, and it says so.** If the live page beats all 8
rewrites on a section, the report tells you to keep it instead of inventing a
change to justify the exercise.

**It never auto-ships.** Output is a scored report plus a recommended copy
sheet. Applying it is your call.

## Where to use it

Before a redesign, or to settle an argument about a headline that has been going
round for two weeks.

Part of [marketing-engineer-tools](https://github.com/jlank31/marketing-engineer-tools).
MIT licensed.
