# LinkedIn posts: 8 drops

**Cadence: Wednesdays, 3:45pm ET.** Personal account, manual post.

## The voice

Drop 1 is Jared's own draft, finished. The other 7 match its register, which is
different from a polished launch post in specific ways:

- **Casual and personal, not announced.** "I've been building a nice repo of
  skills and tools" beats any hook I can write, because it sounds like a person.
- **Short lines, no trailing periods on the standalone ones.** Reads like
  someone typing, not publishing.
- **A values line near the top.** "I firmly believe we should all be getting
  smarter together" is what makes this a giveaway instead of a launch.
- **"A like and a share"**, not "a star". LinkedIn-native ask, lower friction.
- **Link at position 3**, before any explanation.
- **`→` bullets show real strings**, never descriptions of categories.
- **One admission per post.** Something that cost something to say.

Length lands 900 to 1,400 characters. Concrete beats short.

Repo goes public before drop 1:
`gh repo edit jlank31/marketing-engineer-tools --visibility public --accept-visibility-change-consequences`

---

## Drop 1: Wed Aug 5, 3:45pm ET

I've been building a nice repo of skills and tools, so starting today I'm open-sourcing a bunch of them

10+ tools I use to run content at scale

I firmly believe we should all be getting smarter together

📌 Get it free here: github.com/jlank31/marketing-engineer-tools

If it's useful, a like and a share help other people find it

Here's some info on the first one, robot-check

AI detectors tell you "87% likely AI." That's useless to an editor. It doesn't tell you which line to change.

So this one names the line and says why:

→ Reversals: "It's not a tooling problem. It's a distance problem."
→ Hollow openers: "In today's fast-paced landscape"
→ Manufactured rapport: "You're not alone"
→ Fake-punchy fragments: "The result? A 40% lift."

Zero dependencies, no API key, nothing to sign up for. Point it at a file, get a list.

One thing I'll admit: I wrote that reversal rule 6 months ago, built the detector, shipped it into a pipeline that publishes weekly. Last week I tested it properly and found it had never caught the most common version of the pattern.

6 months of my own standard not being enforced. Nobody would have known.

Which is why this is worth handing over instead of writing about. You can check whether the rules hold up

New drop every Wednesday

---

## Drop 2: Wed Aug 12, 3:45pm ET

Every AI copy tool has the same blind spot

Ask for a rewrite, you get a rewrite. There's no outcome where it tells you the page was already fine

So I built one where your current copy competes

📌 Free, same repo: github.com/jlank31/marketing-engineer-tools

How it runs:

→ 8 rewrites of your page, each from a different angle: pain-led, proof-led, objection-led, radically short
→ Your live copy enters as the 9th, untouched
→ 5 judges read all 9 together and rank them section by section

The judges are the part people skip. A skeptical CFO hunting unprovable claims. A founder scrolling at midnight. A competitor looking for what's copyable. The person you're selling to.

They read every version in one pass instead of scoring each alone, which kills the halo effect and costs a fraction as much.

Sometimes your original wins. The report says so plainly.

That felt like a wasted run the first time it happened to me. It wasn't. Knowing your page is already strong is worth as much as a rewrite, and it costs you nothing to act on.

Build the null result into the test, or you'll only ever find what you went looking for

Drop 2 of 12

---

## Drop 3: Wed Aug 19, 3:45pm ET

Every AI writing checker hands you a list and walks away

This week's tool does the boring half and fixes them

📌 Free: github.com/jlank31/marketing-engineer-tools

Four rewrites nobody should be doing by hand:

→ em dashes stripped, the most recognizable 2026 fingerprint
→ "do not" contracted to "don't"
→ "52 percent" rendered as "52%"
→ empty intensifiers cut: "what actually works" becomes "what works"

That last one is why this barely exists elsewhere. Deleting a word takes a second. Not leaving a doubled space, an orphaned comma, or a sentence that now starts lowercase is the fiddly part nobody wants to build.

Where I'd push back on myself:

This won't make your writing good. Clean output is a floor, not a finished piece. A draft can pass every check and still be dull, and no checker catches that.

I run it as the last pass before publishing, never instead of editing. Use it to launder AI output straight to publish and you've just built a faster way to ship the same slop

Drop 3 of 12

---

## Drop 4: Wed Aug 26, 3:45pm ET

If you use an AI coding assistant you've had this week

It asks where the config lives. You tell it. Next session it asks again

Two free tools that fix that, about 5 minutes each

📌 github.com/jlank31/marketing-engineer-tools

→ One rewrites your project's instruction file so the assistant behaves like a teammate. Not "be helpful" boilerplate. Operating rules: what to do without asking, what to never touch, how much effort a task deserves.
→ The other reads your codebase once and writes the cheat sheet itself. File locations, naming conventions, the gotcha that bit you in March.

Why it's worth 5 minutes:

Context you re-explain every session is context you pay for twice. Once in your time, once in the assistant getting it slightly wrong because you summarized it badly at 4pm on a Thursday.

Write it down once and your project knowledge becomes an asset instead of a tax.

The payoff is immediate and slightly embarrassing. You see how much of your week went to explaining things you already knew

Drop 4 of 12

---

## Drop 5: Wed Sep 2, 3:45pm ET

I was under-reporting my own Claude API spend for months and had no idea

Today I'm open-sourcing the tracker that fixed it

📌 Free: github.com/jlank31/marketing-engineer-tools

Three reasons cost tracking is usually wrong, all of them quiet:

→ Cached tokens bill at 1.25x to write and 0.10x to read, and the API reports them SEPARATELY from input_tokens. Miss that and every cached call is understated.
→ Server-side web search costs $10 per 1,000 requests, invisible in the token counts.
→ Unknown model IDs return $0 in most trackers.

That third one is the dangerous one. A new model version silently becomes free, which also makes it invisible to whatever budget cap you built on those numbers.

Mine did exactly that. It now prices anything unfamiliar at the most expensive tier. Overstate, never understate.

The part worth stealing is the cap. Cost reporting tells you about yesterday. A cap stops a runaway retry loop from spending a day's budget while you're at lunch. I tested it on a deliberate runaway and it killed the run after one call.

One line changes. Anthropic() becomes TrackedClient()

Drop 5 of 12

---

## Drop 6: Wed Sep 9, 3:45pm ET

A model update broke my pipeline on a Friday

This week's drop is the 20 lines that would have saved me, plus the layer around them

📌 Free: github.com/jlank31/marketing-engineer-tools

What happened: Claude 5 started returning its reasoning in the first slot of the response. Every line of code I had that read content[0] as the answer got a thinking block instead, and crashed. Not a slow degradation. A hard stop, mid-run.

The fix is to stop assuming position 0 and walk the array for the first block that carries text. That's it. It also makes you forward-compatible with whatever block type gets added next.

What's wrapped around it:

→ retry with jitter, because a pipeline that fans out and hits a rate limit will otherwise retry in lockstep and collide again
→ errors that skip retry entirely: TypeError, auth failures, credit balance. Retrying a bug just runs the bug 3 times.
→ JSON parsing that handles fences and stray prose locally instead of calling a model to repair it

But the piece worth stealing is the counters. The expensive escalation path sends failures to a bigger model to diagnose. The counters tell you how often plain retry was already enough.

Most of us build the safety net and never check whether it catches anything

Drop 6 of 12

---

## Drop 7: Wed Sep 16, 3:45pm ET

The same editor cut the same word from my drafts 7 weeks running before I noticed

Today I'm open-sourcing the thing that would have told me in week 2

📌 Free: github.com/jlank31/marketing-engineer-tools

Feed it before-and-after pairs of anything a human edited and it hands you the pattern:

→ Write "brands", not "vendors" (7x)
→ Cut "very" (5x), the editor removes it every time

Then you paste that into your AI prompt and the drafts stop repeating it.

No API calls, nothing to configure. It's arithmetic on what changed between two versions.

The detail I'd have gotten wrong without shipping it:

Raw word diffs produce garbage. On a heavy rewrite you get things like "aren't" becomes "and founders are already", which would actively mis-train the prompt.

So the list it hands your prompt only takes swaps of 3 words or fewer. The full report keeps everything for you to read.

Your editing history is training data you're already producing and almost certainly throwing away. Feedback you don't capture is feedback you get to receive again

Drop 7 of 12

---

## Drop 8: Wed Sep 23, 3:45pm ET

Three SEO rules I taught clients that turned out to be wrong

Writing this up was uncomfortable, which is roughly the point

📌 Full writeup, free: github.com/jlank31/marketing-engineer-tools

→ "Open with a 40 to 60 word answer paragraph." I said this for a year. It traces to a 2017 study about where Google truncates a snippet box, a different question from what gets cited. The one study that tested structure directly found 150 to 300 words did better. I was teaching the opposite of the evidence.
→ "Every section should stand alone." Google indexes full pages and segments passages itself.
→ "FAQ schema helps you get cited." Google removed FAQ rich results in May 2026.

What the evidence does reward: topic match, concrete specifics with named sources, and a confident un-hedged voice. That last one is the strongest effect measured in the field, by a distance.

One more worth saying plainly. About 1% of people who see an AI summary click through to a source. Citations are a brand impression play, not a traffic play. Anyone quoting a 115% traffic lift is using a number that doesn't survive checking.

Every rule in the writeup is labeled Confirmed, Plausible, or Folklore, so you can see which ones I'd defend and which I'm still unsure about.

That's the last of 12. Thanks for reading along
