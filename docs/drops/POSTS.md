# LinkedIn posts — 8 drops

**Cadence: Wednesdays, 3:45pm ET.** Personal account, manual post.

Each post leads with a specific failure and ends on a concrete line, never a
question. No hashtags (not a reach lever on any channel in 2026).

None of the 8 pitch the service. The repo is the pitch: someone who installs a
tool that works has already learned the relevant thing about how the work gets
done. A sales line in a giveaway post undercuts the giveaway.

**Known and deliberate:** post 1 trips the reversal detector, because its first
line quotes `"It's not X. It's Y."` as the specimen. That is the subject of the
post. If someone runs the tool on it and reports the hit, the answer is yes, that
is the example. Every other post is clean at 0 issues.

Repo flips public before drop 1:
`gh repo edit jlank31/marketing-engineer-tools --visibility public --accept-visibility-change-consequences`

| # | Date | Drop |
|---|---|---|
| 1 | Wed Aug 5 | prose-tells |
| 2 | Wed Aug 12 | Landing Page Copy Tournament |
| 3 | Wed Aug 19 | prose-tells fix + GitHub check |
| 4 | Wed Aug 26 | CLAUDE.md Upgrader + Project Overlay |
| 5 | Wed Sep 2 | llm-run-guard |
| 6 | Wed Sep 9 | llm-run-guard: self-healing |
| 7 | Wed Sep 16 | edit-digest |
| 8 | Wed Sep 23 | The AEO Retractions + email sequences |

---

## Drop 1 — Wed Aug 5, 3:45pm ET

I banned "It's not X. It's Y." from every piece of client content 6 months ago.

Wrote the rule. Wrote the detector. Shipped it into a pipeline that publishes
weekly.

Last week I packaged it up to give away, ran it on deliberately bad copy, and it caught 16 things while missing the one I care about most.

The regex spelled out "is not" as two words. So it caught the "isn't" version and sailed straight past the "it's not"
version. Same sentence. Different apostrophe.

Six months of client work where the rule I'd written down wasn't being enforced.

Fixed it, added the test, put the whole thing on GitHub. Free, MIT, zero
dependencies.

It finds the lines that read as machine-written and says why, instead of a confidence score you can't act on.

pip install prose-tells

github.com/jlank31/marketing-engineer-tools

12 more of these coming, one a week through September

---

## Drop 2 — Wed Aug 12, 3:45pm ET

Most AI copy tools share one flaw: ask for a rewrite and you get a rewrite. There's no outcome where the answer is "your page was already fine."

So the copy tournament I've been using enters the live page as a competitor.

8 rewrites, each from a different angle: pain-led, proof-led, objection-led, radical brevity. Your current copy joins as the 9th entrant, unchanged.

A 5-person panel then reads all 9 in one pass and ranks them section by section: a skeptical CFO hunting unprovable claims, a founder scrolling at midnight, a competitor, your ideal customer, a conversion copywriter.

Reading all 9 together beats scoring each alone, which produces halo effects and costs 9x more.

If the baseline wins, the report says so plainly. Cheap, useful outcome: your page is strong, stop rewriting it.

Never auto-ships.

Free in the repo, drop 2 of 12

github.com/jlank31/marketing-engineer-tools

---

## Drop 3 — Wed Aug 19, 3:45pm ET

Complaining about a draft is easy. Fixing it is the boring part, so most tools skip it.

4 rewrites that should never be done by hand:

> em dashes stripped, because they're the most recognizable 2026 fingerprint
> "do not" contracted to "don't", because the expanded form reads stiff
> spelled-out percentages rendered as the symbol
> empty intensifiers cut, with the punctuation and capitalization around each
  cut repaired so the sentence still reads

That last part is the trick. Deleting a word is trivial. Not leaving a doubled space, an orphaned comma, or a lowercase sentence start is what makes it usable on a finished draft.

It won't make writing good. Clean output is a floor, not a finished piece.

pip install prose-tells

github.com/jlank31/marketing-engineer-tools

---

## Drop 4 — Wed Aug 26, 3:45pm ET

If you use an AI coding assistant, you've had this week: it asks where the config
lives. You tell it. Next session, it asks again.

Two free tools for that, both about 5 minutes to run.

The first rewrites your project's instruction file so the assistant behaves like
a teammate instead of a stranger. Not "be helpful" boilerplate. Operating rules: what to do without asking, what to never touch, how much effort a given
task deserves.

The second reads your project once and writes a permanent cheat sheet. File
locations, naming conventions, data models, the gotchas that bit you in March. The
assistant loads it instead of re-deriving your codebase every time.

The payoff is immediate and slightly annoying: you realize how much time you'd
been spending re-explaining your own project to a machine with no memory.

Both are in the repo, drop 4 of 12

github.com/jlank31/marketing-engineer-tools

---

## Drop 5 — Wed Sep 2, 3:45pm ET

Your Claude API cost tracking is probably wrong. Mine was, for months.

3 quiet reasons:

> Cached tokens bill at 1.25x to write and 0.10x to read, and the API reports them SEPARATELY from input_tokens. Skip that, understate every cached call.
> Server-side web search costs $10 per 1,000 requests, on top of tokens.
> Unknown model IDs. Most trackers return $0 for a model they don't know, so a new model version is invisible to your budget cap.

That third one is dangerous. Mine returned 0.0, so a model missing from the price table silently bypassed the cap.

It now falls back to the most expensive tier. Overstate, never understate.

Swap one line: Anthropic() becomes TrackedClient(). You get real per-run cost, and a run that blows its budget dies instead of burning a day's spend.

I tested the cap on a deliberate runaway. It stopped after 1 call.

pip install llm-run-guard

github.com/jlank31/marketing-engineer-tools

---

## Drop 6 — Wed Sep 9, 3:45pm ET

A model update broke my pipeline. Here are the 20 lines that would have saved me.

Claude 5 started returning its reasoning in the first slot of the response. Every piece of code I had that read content[0] as the answer got a thinking block, and crashed.

Not a subtle degradation. A hard stop, mid-run, on a Friday.

The fix is 20 lines: walk the content array and return the first block that's text. Drop 6 is that, plus the retry and repair layer around it.

The part worth stealing is the counters, not the code.

The healing layer sends failures to a bigger model to diagnose, which is expensive. So it counts how often it does that, and how often the "heal" was a transient error a retry would have fixed for free.

I added that because I suspected the expensive path wasn't earning its keep. Suspect the same about yours.

pip install llm-run-guard

github.com/jlank31/marketing-engineer-tools

---

## Drop 7 — Wed Sep 16, 3:45pm ET

The same editor cut the same word from my drafts 7 weeks in a row before I
noticed.

Same word, 7 times. I only caught it because I eventually ran a diff.

Drop 7 does that automatically. Feed it before-and-after pairs of anything a human has redlined and it tells you the pattern:

> Write "brands", not "vendors" (7x)
> Cut "very" (5x), the editor removes it every time

Then you paste that list into your AI prompt and the drafts stop making those
mistakes.

It costs nothing to run. No API call. It's arithmetic on the text differences.

One detail I'd have gotten wrong without shipping it: raw word diffs produce garbage. On a heavy rewrite you get "aren't" becomes "and founders are already", which would mis-train the prompt.

So the prompt-facing list only takes swaps of 3 words or fewer. The human report keeps everything.

github.com/jlank31/marketing-engineer-tools

---

## Drop 8 — Wed Sep 23, 3:45pm ET

3 SEO rules I taught clients that turned out to be wrong.

1. "Open with a 40 to 60 word answer paragraph." I said this for a year. It traces to a 2017 study about where Google truncates a snippet box, not what gets cited. The one paper that tested structure found 150 to 300 words won. I had it backwards.

2. "Every section should stand alone." Google indexes full pages and segments passages itself.

3. "FAQ schema helps you get cited." Google removed FAQ rich results in May 2026.

What it does reward: topic match, concrete specifics with named sources, and a confident un-hedged voice. That last one is the strongest effect measured in the field.

Also: about 1% of people who see an AI summary click a source. Citations are a brand impression play, not a traffic play.

Full writeup plus 7 B2B email sequences in the repo. Last of 12

github.com/jlank31/marketing-engineer-tools
