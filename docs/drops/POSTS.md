# LinkedIn posts — 8 drops

**Cadence: Wednesdays, 3:45pm ET.** Personal account, manual post.

## The frame

These are not product announcements. Each one is **a lesson from building
something**, where the tool is the artifact of the lesson rather than the point.

The reader should finish thinking *"that's a good way to think about it"* before
they think *"I should download that."* The click is a side effect of the idea
landing.

Rules that hold across all 8:

- **The hook is an admission or a counterintuitive claim**, never a feature.
- **One idea per post.** No feature lists, no bullets of capabilities.
- **The lesson generalizes** past the specific tool, so the post is worth reading
  even if you never install anything.
- **No CTA.** "Free, drop N of 12" and the link. Nothing asking for anything.
- **No pitch.** Nobody gets sold. The generosity is the position.
- 500 to 800 characters. Shorter than feels comfortable.
- No hashtags (not a reach lever on any channel in 2026).

Repo goes public before drop 1:
`gh repo edit jlank31/marketing-engineer-tools --visibility public --accept-visibility-change-consequences`

---

## Drop 1 — Wed Aug 5, 3:45pm ET

6 months ago I banned a specific sentence pattern from every piece of client content.

Wrote the rule. Built the detector. Shipped it into a pipeline that publishes every week.

Last week I finally tested that detector properly and found it had never once caught the most common version of the pattern it was written for.

6 months where the standard I'd written down wasn't being enforced, and nothing in the system was going to tell me.

I fixed it, then packaged the whole thing up and put it on GitHub.

That's the first of 12. I'm giving away the tooling I use to run content at scale, one a week through September.

Some of it is clever. Most of it is just what survived contact with real clients.

github.com/jlank31/marketing-engineer-tools

---

## Drop 2 — Wed Aug 12, 3:45pm ET

Every AI copy tool shares one blind spot: ask it for a rewrite and you'll get a rewrite. There's no outcome where it tells you the page was already fine.

So I built one where your current copy competes.

8 rewrites from different angles, your live page entered as the 9th, and a 5-person panel that reads all of them together and ranks section by section. A skeptical CFO. A founder scrolling at midnight. The person you're selling to.

Sometimes the original wins.

That felt like a failed run the first time it happened. It wasn't. Knowing your page is already strong is worth as much as a rewrite.

Build the null result into the test, or you'll always find what you went looking for.

Free, drop 2 of 12
github.com/jlank31/marketing-engineer-tools

---

## Drop 3 — Wed Aug 19, 3:45pm ET

Most writing tools tell you what's wrong. Very few of them fix it.

Flagging is the fun part to build. Fixing is fiddly and unglamorous: cut a word and you're left with a doubled space, an orphaned comma, a sentence that now starts lowercase.

So nobody builds it, and every AI writing checker hands you a list and walks away.

This week's drop does the boring half. 4 rewrites nobody should be doing by hand, and it cleans up after itself.

It won't make your writing good. Clean output is a floor, not a finished piece.

But doing the tedious part is what turns a tool you tried once into one you run every time.

Free, drop 3 of 12
github.com/jlank31/marketing-engineer-tools

---

## Drop 4 — Wed Aug 26, 3:45pm ET

For months I started every working session by re-explaining my own project to a machine with no memory.

Where the config lives. What never to touch. Why that one file is strange.

Then I wrote it down once and got the time back.

Two tools in this week's drop do that for you. One rewrites your project's instruction file so your AI assistant behaves like a teammate instead of a stranger. The other reads your codebase and writes the cheat sheet itself.

5 minutes each.

The payoff is immediate and slightly embarrassing: you see how much of your week went to context you already had and never bothered to write down.

Free, drop 4 of 12
github.com/jlank31/marketing-engineer-tools

---

## Drop 5 — Wed Sep 2, 3:45pm ET

I was under-reporting my own AI spend for months and had no idea.

Not by a rounding error. The tracking looked healthy and the number was wrong, which is the combination that keeps you from looking.

3 reasons, all quiet. The one worth knowing: most cost trackers return $0 for a model they don't recognize. So a new model version silently becomes free, which also makes it invisible to whatever budget cap you built on those numbers.

Mine now prices anything unfamiliar at the most expensive tier. Overstate, never understate.

That generalizes well past AI. The number you trust is usually the one you never checked.

Free, drop 5 of 12
github.com/jlank31/marketing-engineer-tools

---

## Drop 6 — Wed Sep 9, 3:45pm ET

A model update broke my pipeline on a Friday.

Not gracefully. Hard stop, mid-run. The models started returning their reasoning first, so every line of code I had that grabbed the opening of a response grabbed the wrong thing.

20 lines to fix. Months of it working fine had taught me nothing about how fragile that assumption was.

This week's drop is that fix, plus the retry layer around it. And the counters, which are the part worth stealing: they measure whether the expensive recovery path is earning its keep.

Most of us build the safety net and never check whether it catches anything.

Free, drop 6 of 12
github.com/jlank31/marketing-engineer-tools

---

## Drop 7 — Wed Sep 16, 3:45pm ET

The same editor cut the same word from my drafts 7 weeks running before I noticed.

7 weeks. And I only caught it because I eventually ran a diff instead of reading.

Your editing history is training data you're already producing and almost certainly throwing away. Every redline is someone telling you their preferences in the clearest terms available.

This week's tool reads before-and-after pairs and hands you the pattern. No API calls, nothing to configure. It's arithmetic on what changed.

Then you paste that into your prompt and stop making those mistakes.

Feedback you don't capture is feedback you get to receive again.

Free, drop 7 of 12
github.com/jlank31/marketing-engineer-tools

---

## Drop 8 — Wed Sep 23, 3:45pm ET

3 things I taught clients that turned out to be wrong.

I told people to open with a 40 to 60 word answer paragraph. Said it for a year. It traces back to a 2017 study about where Google truncates a snippet box, which is a different question from what gets cited. The one study that tested the thing directly found the opposite.

I also taught that every section should stand alone, and that FAQ schema helps you get cited. Google removed FAQ rich results in May.

Writing that up was uncomfortable, which is probably the point. Most marketing advice never gets audited. It gets repeated confidently until someone checks.

Full writeup in the repo. Last of 12.

Thanks for reading along these last 3 months.

github.com/jlank31/marketing-engineer-tools
