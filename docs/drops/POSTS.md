# LinkedIn posts — 8 drops

**Cadence: Wednesdays, 3:45pm ET.** Personal account, manual post.

## The frame

Open-source giveaway posts, not thought-leadership essays. The structure that
works for this (see Peter Yang's /no-ai-slop launch) is:

1. **Line 1 declares what you're giving away and why you were annoyed enough to
   build it.** No wind-up.
2. **The link goes near the top**, not buried at the bottom. People decide in the
   first 3 lines whether to click.
3. **Ask for the star.** In open source that's a normal, expected ask, not a
   pitch. It's how the thing gets found.
4. **"Why I built it:"** then `→` bullets with CONCRETE examples. Show the actual
   strings it catches, not a description of the category.
5. **A caveat that costs you something.** Say what it won't do or how it can be
   misused. That's what separates a giveaway from an ad.

Emoji: 📌 for links, → for examples. Two markers, used consistently.

Length runs long here (1,300 to 1,800 characters) and that's correct for the
format. The Peter Yang post is 1,400. Long is fine when it's concrete.

Repo goes public before drop 1:
`gh repo edit jlank31/marketing-engineer-tools --visibility public --accept-visibility-change-consequences`

---

## Drop 1 — Wed Aug 5, 3:45pm ET

I ban 25 phrases from every piece of client content I ship. Today I'm open-sourcing the checker that enforces them, plus the 12 other tools I use to run content at scale.

📌 Get it free here: github.com/jlank31/marketing-engineer-tools

If it's useful, a star helps other people find it.

Why I built it:

AI detectors tell you "87% likely AI." That's useless to an editor. It doesn't tell you which line to change.

So this one names the line and says why:

→ Reversals: "It's not a tooling problem. It's a distance problem."
→ Hollow openers: "In today's fast-paced landscape"
→ Manufactured rapport: "You're not alone"
→ Fake-punchy fragments: "The result? A 40% lift."

Zero dependencies, no API key, nothing to sign up for. Point it at a file, get a list.

The uncomfortable part:

I wrote the reversal rule 6 months ago. Built the detector. Shipped it. Last week I finally tested it properly and found it never caught the most common version of that exact pattern.

6 months where the standard I'd written down wasn't being enforced, and nothing was going to tell me.

That's the whole reason this is worth giving away rather than describing. You can read the rules and check whether they hold.

12 more drops, one a week through September.

---

## Drop 2 — Wed Aug 12, 3:45pm ET

Every AI copy tool has the same blind spot: ask for a rewrite, get a rewrite. There's no outcome where it says your page was already fine.

So I built one where your current copy competes. Free, in the same repo:

📌 github.com/jlank31/marketing-engineer-tools

How it works:

→ 8 rewrites of your page, each from a different angle: pain-led, proof-led, objection-led, radically short
→ Your live copy enters as the 9th, unchanged
→ 5 judges read all 9 together and rank them section by section

The judges are the part people underestimate. A skeptical CFO hunting unprovable claims. A founder scrolling at midnight. A competitor looking for what's copyable. The person you're selling to. A conversion copywriter.

They read every version in one pass instead of scoring each alone, which kills the halo effect and costs a fraction as much.

Sometimes your original wins. The report says so plainly.

That felt like a failed run the first time it happened to me. It wasn't. Knowing your page is already strong is worth as much as a rewrite and takes zero work to act on.

Build the null result into the test, or you'll always find what you went looking for.

Drop 2 of 12.

---

## Drop 3 — Wed Aug 19, 3:45pm ET

Every AI writing checker hands you a list of problems and walks away. This week's drop fixes them.

📌 Free: github.com/jlank31/marketing-engineer-tools

Four rewrites nobody should be doing by hand:

→ em dashes stripped (the most recognizable 2026 fingerprint)
→ "do not" contracted to "don't"
→ "52 percent" rendered as "52%"
→ empty intensifiers cut: "what actually works" becomes "what works"

That last one is why this barely exists elsewhere. Deleting a word is trivial. Not leaving a doubled space, an orphaned comma, or a sentence that now starts lowercase is the fiddly part, and it's the difference between a tool you try once and one you run every time.

Where I'd push back on myself:

This won't make your writing good. Clean output is a floor, not a finished piece. A draft can pass every check and still be boring, and no checker will catch that.

I run it as the last pass before publishing, not as a substitute for editing. If you use it to launder AI output straight to publish, you've built a faster way to ship the same slop.

Drop 3 of 12.

---

## Drop 4 — Wed Aug 26, 3:45pm ET

If you use an AI coding assistant, you've had this week: it asks where the config lives, you tell it, and next session it asks again.

Two free tools that fix that, about 5 minutes each:

📌 github.com/jlank31/marketing-engineer-tools

→ The first rewrites your project's instruction file so the assistant behaves like a teammate. Not "be helpful" boilerplate. Operating rules: what to do without asking, what to never touch, how much effort a task deserves.
→ The second reads your codebase once and writes a permanent cheat sheet. File locations, naming conventions, data models, the gotcha that bit you in March.

Why it matters more than it sounds:

Context you re-explain every session is context you're paying for twice. Once in your time, once in the assistant getting it slightly wrong because you summarized it badly at 4pm on a Thursday.

Writing it down once turns your project knowledge into an asset instead of a tax.

The payoff is immediate and slightly embarrassing. You see how much of your week went to explaining things you already knew.

Drop 4 of 12.

---

## Drop 5 — Wed Sep 2, 3:45pm ET

I was under-reporting my own Claude API spend for months. Today I'm open-sourcing the tracker that fixed it.

📌 Free: github.com/jlank31/marketing-engineer-tools

Three reasons cost tracking is usually wrong, all quiet:

→ Cached tokens bill at 1.25x to write and 0.10x to read, and the API reports them SEPARATELY from input_tokens. Miss that and every cached call is understated.
→ Server-side web search costs $10 per 1,000 requests, invisible in the token counts.
→ Unknown model IDs return $0 in most trackers.

That third one is the dangerous one. A new model version silently becomes free, which also makes it invisible to whatever budget cap you built on those numbers. Mine did exactly this.

It now prices anything unfamiliar at the most expensive tier. Overstate, never understate.

The part worth stealing is the cap. Cost reporting tells you what happened yesterday. A cap stops a runaway retry loop from spending a day's budget while you're at lunch. I tested it on a deliberate runaway and it killed the run after one call.

One line changes: Anthropic() becomes TrackedClient().

Drop 5 of 12.

---

## Drop 6 — Wed Sep 9, 3:45pm ET

A model update broke my pipeline on a Friday. This week's drop is the 20 lines that would have saved me, plus the layer around them.

📌 Free: github.com/jlank31/marketing-engineer-tools

What happened: Claude 5 started returning its reasoning in the first slot of the response. Every line of code I had that read content[0] as the answer got a thinking block instead, and crashed. Not a slow degradation. A hard stop, mid-run.

The fix is to stop assuming position 0 and walk the array for the first block that carries text. That's it. It also makes you forward-compatible with whatever block type gets added next.

What's around it:

→ retry with jitter, because a pipeline that fans out and hits a rate limit will otherwise retry in lockstep and re-collide
→ errors that skip retry entirely: TypeError, auth failures, credit-balance errors. Retrying a bug just runs the bug three times.
→ JSON parsing that handles fences and stray prose locally instead of calling a model to repair it

But the piece worth stealing is the counters. The expensive escalation path sends failures to a bigger model to diagnose. The counters tell you how often plain retry was already enough.

Most of us build the safety net and never check whether it catches anything.

Drop 6 of 12.

---

## Drop 7 — Wed Sep 16, 3:45pm ET

The same editor cut the same word from my drafts 7 weeks running before I noticed. Today I'm open-sourcing the tool that would have told me in week 2.

📌 Free: github.com/jlank31/marketing-engineer-tools

Feed it before-and-after pairs of anything a human has edited, and it hands you the pattern:

→ Write "brands", not "vendors" (7x)
→ Cut "very" (5x), the editor removes it every time

Then you paste that into your AI prompt and the drafts stop repeating the mistake.

No API calls, nothing to configure. It's arithmetic on what changed between two versions.

The detail I'd have gotten wrong without shipping it:

Raw word diffs produce garbage instructions. On a heavy rewrite you get things like "aren't" becomes "and founders are already", which would actively mis-train the prompt.

So the list it hands your prompt only takes swaps of 3 words or fewer. The full report keeps everything for you to read.

Your editing history is training data you're already producing and almost certainly throwing away. Feedback you don't capture is feedback you get to receive again.

Drop 7 of 12.

---

## Drop 8 — Wed Sep 23, 3:45pm ET

Three SEO rules I taught clients that turned out to be wrong. Writing this up was uncomfortable, which is roughly the point.

📌 Full writeup, free: github.com/jlank31/marketing-engineer-tools

→ "Open with a 40 to 60 word answer paragraph." I said this for a year. It traces back to a 2017 study about where Google truncates a snippet box, which is a different question from what gets cited. The one study that tested structure directly found 150 to 300 words did better. I was teaching the opposite of the evidence.
→ "Every section should stand alone." Google indexes full pages and segments passages itself.
→ "FAQ schema helps you get cited." Google removed FAQ rich results in May 2026.

What the evidence does reward: topic match, concrete specifics with named sources, and a confident un-hedged voice. That last one is the strongest effect measured in the field, by a distance.

One more worth saying plainly: about 1% of people who see an AI summary click through to a source. Citations are a brand impression play, not a traffic play. Anyone quoting a 115% traffic lift is using a number that doesn't survive checking.

Every rule in the writeup is labeled Confirmed, Plausible, or Folklore, so you can see which ones I'd defend and which I'm still unsure about.

That's the last of 12. Thanks for reading along.
