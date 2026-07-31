# Tool summaries

Building blocks for posts. Each tool has a one-liner, who it's for, how to use it,
and why it matters. Mix into whatever post structure you want.

Repo: `github.com/jlank31/marketing-engineer-tools`

---

## 1. prose-tells (scan)

**One-liner**
A spell-checker for AI writing tells. It names the exact line that reads as machine-written and tells you why.

**Who it's for**
Anyone publishing AI-assisted copy who's had the nagging feeling some of it reads generic. Marketers, agencies, content teams, solo founders writing their own stuff.

**How to use it**
```
pip install prose-tells
prose-tells scan draft.md
```
Point it at any file. Get a numbered list back with your own lines quoted. Run it as the last pass before publishing, or send the output to a writer instead of marking up their doc.

**Why it matters**
AI detectors answer "was this written by a model?" with a percentage. That's useless to an editor, because a score doesn't tell you what to change. This answers a different question: which lines, and what should they say instead.

It also catches things no other tool looks at. Whether every paragraph is the same length, which is a robot rhythm that survives a clean word-level pass. Whether an article cites 3 real sources or just gestures at authority.

**Numbers you can use**
25 banned phrases, 8 shape-level tell families, 14 lexical detector families, zero dependencies, no API key.

---

## 2. prose-tells corpus

**One-liner**
Reads your entire published archive at once and shows you where you've started repeating yourself.

**Who it's for**
Anyone with 10+ published pieces. The more you've written, the more uncomfortable it gets.

**How to use it**
```
prose-tells corpus ./blog/
```
Point it at a folder. Once a quarter is about right.

**Why it matters**
Every piece passes on its own while the library slowly converges into one voice telling one anecdote citing one set of numbers. That convergence is invisible from inside any single draft, and nobody re-reads their whole archive.

It found, on a 10-post archive: the same 5 statistics recycled across 4 posts, the same opening move in 6 pairs of posts, and 94 verbatim runs.

**The honest bit**
Some repetition is your positioning working. Some is a rut. The tool finds it; you decide which is which. It never fails a build.

---

## 3. prose-tells fix

**One-liner**
The same tool, but it edits instead of complaining.

**Who it's for**
Anyone who's run a writing checker, agreed with it, and then had to make 30 small edits by hand.

**How to use it**
```python
from prose_tells import strip_em_dashes, apply_contractions
```
Four deterministic rewrites: em dashes stripped, "do not" contracted, "52 percent" rendered as "52%", empty intensifiers cut.

**Why it matters**
Flagging is the fun part to build. Fixing is fiddly: cut a word and you're left with a doubled space, an orphaned comma, a sentence that now starts lowercase. So almost nobody builds it, and every checker hands you a list and walks away.

Repairing the seam around each cut is what turns a tool you tried once into one you run every time.

**Before / after**
```
"We do not ship — it is actually 52 percent slower."
"We don't ship, it's 52% slower."
```

---

## 4. Landing Page Copy Tournament

**One-liner**
Rewrites your landing page 8 ways, enters your live copy as the 9th competitor, and has 5 judges rank them all.

**Who it's for**
Anyone about to redesign a page, or stuck in an internal argument about a headline.

**How to use it**
A Claude Code skill. Give it your page and your brand rules, get back a scored report plus a recommended copy sheet. Never auto-ships.

**Why it matters**
Every AI copy tool has the same blind spot: ask for a rewrite and you get a rewrite. There's no outcome where the answer is "your page was already fine."

Entering the live page as a competitor fixes that. Sometimes the original wins, and the report says so.

**The judges**
A skeptical CFO hunting unprovable claims. A founder scrolling at midnight. A competitor looking for what's copyable. The person you're selling to. A conversion copywriter.

They read all 9 versions in one pass rather than scoring each alone, which kills the halo effect and costs a fraction as much.

---

## 5. CLAUDE.md Upgrader

**One-liner**
Rewrites your project's AI instruction file so the assistant behaves like a teammate instead of a stranger.

**Who it's for**
Anyone using Claude Code, Cursor, or similar on a project they return to.

**How to use it**
Run it on an existing project, commit the result. About 5 minutes.

**Why it matters**
Most instruction files are "be helpful" boilerplate. What actually changes behavior is operating rules: what to do without asking, what to never touch, how much effort a given task deserves.

**The payoff**
The assistant stops asking questions it should already know the answer to.

---

## 6. Project Overlay

**One-liner**
Reads your codebase once and writes a permanent cheat sheet so the AI stops re-deriving it every session.

**Who it's for**
Same audience. Pairs with the one above.

**How to use it**
Point it at a project. It writes file locations, naming conventions, data models, and the gotchas into a file your assistant loads automatically.

**Why it matters**
Context you re-explain every session is context you pay for twice. Once in your time, once in the assistant getting it slightly wrong because you summarized it badly at 4pm on a Thursday.

**The payoff**
Immediate and slightly embarrassing. You see how much of your week went to explaining things you already knew.

---

## 7. llm-run-guard (cost tracking)

**One-liner**
A spend meter for the Claude API that counts the things most trackers miss, plus a circuit breaker that kills a run before it kills your budget.

**Who it's for**
Anyone building on the Anthropic API. Especially anyone who's been surprised by a bill.

**How to use it**
```
pip install "llm-run-guard[anthropic]"
```
One line changes: `Anthropic()` becomes `TrackedClient()`. Everything else stays.

There's also a CLI for sizing a job before you run it:
```
llm-cost price claude-opus-5 --in 50000 --cache-read 40000
```

**Why it matters**
Three reasons cost tracking is usually wrong, all quiet:

Cached tokens bill at 1.25x to write and 0.10x to read, and the API reports them separately from `input_tokens` rather than inside them. Miss that and every cached call is understated.

Server-side web search costs $10 per 1,000 requests, invisible in the token counts.

Unknown model IDs return $0 in most trackers. That's the dangerous one: a new model version silently becomes free, which also makes it invisible to whatever budget cap you built on those numbers.

**The part worth stealing**
The cap. Cost reporting tells you about yesterday. A cap stops a runaway retry loop from spending a day's budget while you're at lunch. Tested on a deliberate runaway, it killed the run after 1 call.

---

## 8. llm-run-guard (self-healing)

**One-liner**
The layer that keeps an AI pipeline running unattended, plus the counters that tell you whether its expensive rescue path is worth paying for.

**Who it's for**
Anyone running a pipeline on a schedule, or anything that has to survive overnight.

**How to use it**
```python
@with_healing(attempts=3)
def summarize(doc): ...
```

**Why it matters**
Includes the fix for a real outage: a model update started returning reasoning in the first slot of the response, so every pipeline written as `response.content[0].text` crashed. Not a slow degradation, a hard stop mid-run. The fix is to walk the array for the first block that carries text.

Retries skip errors where retrying is pointless (TypeError, auth failures, credit-balance errors) rather than burning 3 attempts on the same bug. Jitter is in there because a pipeline that fans out and hits a rate limit otherwise retries in lockstep and collides again.

**The part worth stealing**
`metrics()`. The escalation path sends failures to a bigger model to diagnose, which costs real money. The counters tell you how often plain retry was already enough. Most people build the safety net and never check whether it catches anything.

---

## 9. edit-digest

**One-liner**
Learns your editor's style from what they actually change, and hands you rules you can paste into a prompt.

**Who it's for**
Anyone whose drafts get redlined by the same person or the same brand standard, repeatedly.

**How to use it**
```
pip install edit-digest
edit-digest edits.jsonl --prompt-block >> PROMPT.md
```
Feed it before-and-after pairs. Any file with a before and an after column.

**Why it matters**
Your editing history is training data you're already producing and almost certainly throwing away. Every redline is someone telling you their preferences in the clearest terms available, and most teams read each one once and bin it.

Costs nothing to run. No model, no API call. It's arithmetic on what changed.

**What the output looks like**
```
Write "brands", not "vendors" (7x)
Cut "very" (5x). The editor removes it every time.
```

**The detail worth mentioning**
Raw word diffs produce garbage on heavy rewrites: you get pairs like `"aren't" → "are already"`, which is an alignment artifact, not a preference. Feed that into a prompt and you've confidently taught the model something false.

So the prompt-facing list only takes short swaps where the replacement didn't grow. The human report keeps everything. Conservative for the machine, permissive for the human.

---

## 10. The AEO Retractions (essay)

**One-liner**
Three SEO rules I taught clients that turned out to be wrong, with every surviving claim labeled Confirmed, Plausible, or Folklore.

**Who it's for**
Anyone doing SEO or AEO work, or buying it from someone.

**How to use it**
Read it. It's 900 words.

**Why it matters**
The "40 to 60 word answer paragraph" rule traces back to a 2017 study about where Google's snippet box truncates, which is a different question from what gets cited. The one study that tested structure directly found 150 to 300 words did better. So the advice was the opposite of the evidence.

"Every section should stand alone" optimizes for a retrieval step that doesn't need help, at the cost of writing that sounds amnesiac.

FAQ schema stopped being a lever when Google removed FAQ rich results in May 2026.

**The expectation nobody sets**
About 1% of people who see an AI summary click through to a source. Citations are a brand impression play, not a traffic play. Anyone quoting a 115% traffic lift is using a number that doesn't survive checking.

**Why publish a retraction at all**
All three wrong rules shared a shape: a number or mechanism that was true about something, applied to a different question, repeated until it sounded settled. That's what happens when advice circulates faster than anyone re-checks it.

---

## Cross-cutting lines you can reuse

On the whole repo:
- "10+ tools I use to run content at scale"
- "Everything here exists because something went wrong once and I didn't want it to happen twice"
- "Most of it isn't clever. It's just what survived contact with real clients."

On why the provenance matters:
- "Anyone can publish a list of AI writing tells. Knowing which rules survive contact with real publishing is the hard part."
- "Every detector records why it exists, including the false positives I deliberately allowed."

Honest limits worth saying out loud:
- "These catch tells, not bad writing. Clean output is a floor, not a finished piece."
- "The detectors under-report on purpose. A checker that flags good writing gets switched off in a week, and then it protects nothing."

The admission that lands:
- "I wrote the reversal rule 6 months ago, built the detector, shipped it. Last week I tested it properly and found it had never caught the most common version of that exact pattern."
