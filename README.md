# marketing-engineer-tools

![Marketing tooling](docs/assets/marketing-dashboard.jpeg)

Free tools for people who publish a lot and can't afford for it to read like a robot wrote it.

Everything here was pulled out of a content pipeline that has shipped work for real clients, every single week, since April 2026. None of it is theoretical. Each guardrail exists because something went wrong once and I didn't want it to happen twice.

Most of them still carry the date and the failure in a code comment, so you can decide for yourself whether the rule earns its place.

**By [Jared Castronova](https://www.linkedin.com/in/jaredcastronova/)**, Founder of JAC Growth Marketing

---

## Who this is for

**Marketers and writers using AI to draft.** You're shipping more than you used to, and you've got a quiet worry that some of it reads generic. These tools name the exact lines and tell you why, instead of handing you a percentage.

**Agencies and content teams.** You need one consistent bar across writers, freelancers, and whatever the model produced today. A shared checker beats a style guide nobody opens.

**Developers building on the Claude API.** Two of the packages are for you specifically: real cost tracking, and a pipeline that survives being left alone overnight.

**Anyone using Claude Code.** Several drops are skills you drop into `~/.claude/skills/` and forget about.

You don't need to write code to use most of this. If you can copy one line into a terminal, you can run it.

---

## How to use it

**The 30-second version.** Install it, point it at something you wrote, read what comes back:

```bash
pip install prose-tells
prose-tells scan your-draft.md
```

The other two packages:

```bash
pip install "llm-run-guard[anthropic]"   # real API cost tracking + a budget cap
pip install edit-digest                  # learn an editor's style from their edits
```

You'll get a list like this, quoting your own lines back at you:

```
FAIL  your-draft.md  (3 issues, 2 warnings)
    [issue] Hollow opener: "In today's fast-paced landscape"
    [issue] Manufactured rapport: "You're not alone"
    [issue] Empty intensifier: "actually" (x9)
    [warning] Low sentence-length variance (0.12, target >0.30) - every
              paragraph is nearly the same length, which reads as generated
```

**Three ways people use it:**

1. **Last pass before publishing.** Run it on the finished draft. Fix what you agree with, ignore what you don't.
2. **As an edit brief.** Send a writer the output instead of marking up their doc.
3. **Automatically, on every draft.** It runs as a GitHub check from drop 3, so if your team keeps content in a repo, nobody has to remember.

**Claude Code skills** get copied into place rather than installed:

```bash
./tools/install_skills.sh
```

**Not a developer?** The install line above works on any Mac or Linux machine with Python. If that sentence didn't mean anything to you, send this repo to whoever handles your website. It's a 2 minute job for them.

---

## Everything in here

12 tools, one released each week. Plain English on what each one does and when you'd reach for it.

**Everything is available right now.** Nothing is gated behind its announcement
date. The weekly schedule is when each tool gets *written about*, not when it
becomes downloadable, so if you found this in week 1 you can take all of it today.

The dates are there so the announcements make sense, and so you know when to
expect a writeup on the thinking behind each one.

### Shipping weekly, Wednesdays 3:45pm ET

| # | Date | Tool | Status | What it does, and when you'd use it |
|---|---|---|---|---|
| 1 | Aug 5 | [**prose-tells**](packages/prose-tells) | **Ready** | A spell-checker for AI writing tells. Reads a draft and names the exact lines that read as machine-written: the "it's not X, it's Y" reversal, em dashes, stock openers, 25 overused phrases. It also catches things no other tool looks at, like whether every paragraph is the same length (a robot rhythm) or whether an article cites 3 real sources or just gestures at authority. **Use it** on anything before it goes live. |
| 2 | Aug 12 | **Landing Page Copy Tournament** | **Ready** | Rewrites your landing page 8 different ways, then puts all 9 versions (yours competes as the 10th) in front of a 5-person judging panel: a skeptical CFO, a tired founder scrolling at midnight, a competitor, your ideal customer, and a conversion copywriter. **Use it** before a redesign, or to settle an argument about a headline. If your current page wins, it says so instead of inventing a rewrite. |
| 3 | Aug 19 | **prose-tells `fix`** | **Ready** | Same tool, but it edits instead of complaining. Strips em dashes, contracts "do not" to "don't", turns "52 percent" into "52%", and cuts empty words, repairing the punctuation around each cut so the sentence still reads. **Use it** as a final cleanup pass, or wire it into your repo so every content update gets checked automatically. |
| 4 | Aug 26 | **CLAUDE.md Upgrader** + **Project Overlay** | **Ready** | Two tools for anyone using an AI coding assistant. One rewrites your project's instruction file so the AI behaves like a teammate. The other writes a permanent cheat sheet so it stops re-learning your project every session. **Use them** if you've ever answered the same question from your AI twice. |
| 5 | Sep 2 | [**llm-run-guard**](packages/llm-run-guard) | **Ready** | A spend meter and an emergency brake for anyone building on the Claude API. Most cost tracking is quietly wrong: it misses cached tokens, misses web search charges, and reports $0 for any model it doesn't recognize, which silently switches off your budget cap. **Use it** if you've ever been surprised by an API bill. |
| 6 | Sep 9 | **llm-run-guard: self-healing** | **Ready** | The layer that keeps an AI pipeline running while you sleep. Retries failures, repairs malformed AI output, and escalates to a smarter model as a last resort. It also counts whether those expensive rescue calls were worth it, which most people never check. **Use it** on anything that runs unattended. |
| 7 | Sep 16 | [**edit-digest**](packages/edit-digest) | **Ready** | Learns your editor's style from their edits. Feed it before-and-after pairs and it tells you the pattern: *Write "brands", not "vendors" (7x). Cut "very" (5x), the editor removes it every time.* Paste that into your AI prompt and the drafts stop repeating the mistakes. Costs nothing to run, no API call. **Use it** monthly and watch your drafts need less editing each cycle. |
| 8 | Sep 23 | [**The AEO Retractions**](docs/essays/aeo-retractions.md) | **Ready** | An essay retracting 3 SEO rules I taught clients and now know are wrong, with every remaining rule labeled Confirmed, Plausible, or Folklore. **Use it** to stop doing 3 things that don't work, and to set honest expectations before someone quotes you a traffic number that doesn't survive checking. |

### Bonus tools

These don't get their own launch week. `corpus` ships inside prose-tells from day
one, so if you install drop 1 you already have it. The rest land whenever they're
done.

| Tool | Status | What it does, and when you'd use it |
|---|---|---|
| **prose-tells `corpus`** | **Ready** | Reads your *entire* published archive at once and shows where you've started repeating yourself: the anecdote you've told word for word 3 times, the same 5 statistics recycled across 4 posts, the same opening move in 5 of your last 6 articles. Each post looks fine alone. The sameness only shows up across the whole library. **Use it** once a quarter. Expect it to be uncomfortable. |
| **Pitch Deck Builder** | Building | Builds an investor, partner, or client deck slide by slide with speaker notes, blending 5 proven narrative frameworks and adapting the mix to who's in the room. Output pastes straight into Gamma or Google Slides. **Use it** when you're staring at slide 1. |
| **Marketing Folklore Registry** | Building | A running list of marketing statistics that get repeated everywhere and are provably wrong, plus a checker that flags them in your draft. **Use it** before your next strategy deck, so you don't cite something that falls apart when someone checks. |
| **Email Deliverability Checklist** | Building | A one-page pre-send checklist covering the technical setup that decides whether your campaign lands in the inbox or in spam. **Use it** before every send. The most boring thing here and probably the most useful. |

---

## Why the stories matter more than the rules

Anyone can publish a list of AI writing tells. The list isn't the hard part. Knowing which rules survive contact with real publishing is.

So every detector here records why it exists. A rule with a note saying "this shipped once, on this date, and here's the false positive I let through on purpose" is something you can evaluate. A rule without one is a guess.

And where a rule turned out to be wrong, I retract it in public instead of quietly deleting it. See [docs/essays](docs/essays) for 3 SEO rules I taught for a year that don't hold up.

**A real example.** I banned "It's not X. It's Y." from all client content 6 months ago, wrote the detector, shipped it. While packaging that detector to give away, I ran it on some deliberately bad copy and it missed that exact pattern. The rule spelled out "is not" as two words, so it caught "It isn't a problem. It's a symptom" and sailed past "It's not a problem. It's a symptom." Same sentence, different apostrophe.

That's in here, with the fix and the test.

---

### Yes, this README fails its own checker

Run `prose-tells scan README.md` and you'll get about 10 hits. Almost all of them are quotes.

This page demonstrates the tells it detects, so it contains them: "In today's fast-paced landscape" and "You're not alone" appear in the sample output above, and the "It's not X. It's Y." story quotes that pattern 3 times on purpose.

That's a real limitation worth knowing before you rely on it. **The checker can't tell the difference between using a phrase and quoting one.** If you write about bad copy, or quote a competitor, or include an example of what not to do, expect a flag and use your judgment.

It caught one genuine slip in here too, which is the more useful half of the story: I'd written "three ways people actually use it" in a document that bans "actually." Fixed.

## Two honest limits

**This catches tells, not bad writing.** Clean output is a floor, not a finished piece. In the pipeline these came from, a human still reads everything before it ships. A draft can pass every check and still be boring.

**The detectors under-report on purpose.** They're tuned to miss rather than to cry wolf, because a checker that flags good writing gets switched off within a week, and then it protects nothing. If you want it stricter, that's what the profile settings are for.

---

## Scope, stated up front

**12 drops, one a week, Aug 5 to Sep 23 2026. Then maintenance mode.**

This is a deliberate run with an ending, not a project that gets abandoned in October. Maintenance means bugs and price updates keep getting fixed. When the weekly drops stop, that's the plan working, not the project dying.

## License and contributing

MIT. Use it commercially, fork it, ship it inside your own product. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Found a false positive? That's the most useful thing you can report, and there's a template for it. Read [CONTRIBUTING.md](CONTRIBUTING.md) first though: a few files here are mirrored from a private repo and can't be edited directly, and it explains what to do instead.
