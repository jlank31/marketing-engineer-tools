# Three SEO rules I taught that turned out to be wrong

I audited the advice I'd been giving clients about getting cited by AI search. Three rules I'd repeated confidently for months don't survive contact with their own sources.

Writing this up was uncomfortable, which is roughly the point. Most marketing advice never gets audited. It gets repeated until it sounds like consensus.

Every claim below is labeled **Confirmed**, **Plausible**, or **Folklore**, so you can see which ones I'd defend and which I'm still unsure about.

---

## Retraction 1: the "40 to 60 word answer capsule"

**What I taught:** open every section with a 40 to 60 word direct answer, because that's the length AI engines extract.

**Why it's wrong:** the number traces back to a 2017 study measuring where Google's **featured snippet box truncates**. That's a display constraint on a UI element, not a finding about what gets selected or cited. The rule survived a platform shift by having a number attached to it, which made it feel measured.

Worse, the one study I can find that tested paragraph structure against citation directly found the **opposite**: 150 to 300 word passages performed better than short ones.

I was prescribing against the evidence, using a number from a different question.

**What I'd say now:** there is no word target. Answer the question directly and stop when you're done. Don't build a validator for a length rule.

**Label:** the original claim is Folklore. The 150 to 300 word finding is Plausible, single study.

---

## Retraction 2: "every section should stand alone"

**What I taught:** write each section as a self-contained unit, because engines extract passages independently.

**Why it's wrong:** half true in a way that produces bad writing. Engines *do* segment passages, but they do the segmenting themselves, from a full page they've already indexed. ChatGPT fetches the whole page. Google indexes the document and picks passages from it.

Writing every section to stand alone means restating context you already established, which produces the repetitive, slightly amnesiac tone that makes a page read as machine-assembled. I was optimizing for a retrieval step that doesn't need my help, at the cost of the thing a reader notices.

**What I'd say now:** write a coherent document. Let the engine do the segmenting.

**Label:** Folklore, though it started from a real mechanism.

---

## Retraction 3: "FAQ schema helps you get cited"

**What I taught:** add FAQPage structured data to improve your odds of being surfaced.

**Why it's wrong:** Google removed FAQ rich results from Search in May 2026. The visible benefit is gone. I have no evidence the markup ever influenced AI citation independently of the rich result, and I never had any. I inherited the belief from the era when the rich result was visible and kept recommending it after the mechanism disappeared.

That's the pattern worth noticing: the tactic outlived the reason for the tactic, and nobody re-checked.

**What I'd say now:** schema is fine for what it does. It is not a citation lever. Neither is `llms.txt` — one audit of 137,210 domains found **97%** of those files were never fetched once.

**Label:** Folklore.

---

## What the evidence actually rewards

In rough order of effect size:

1. **Topic alignment.** Being about the thing. Unglamorous and the largest lever.
2. **Concrete specifics with named sources.** Numbers, dates, named organizations. This is the one most under-done.
3. **Confident, un-hedged voice.** The strongest measured effect I've seen in this literature, by a distance. Hedged prose ("can help to potentially improve") gets cited far less than a direct claim. **Confirmed**, and it's the finding I'd change my writing over.
4. **Question-format H2s** matching how people actually ask. **Plausible.**
5. **Focused scope.** 53.4% of AI-cited pages are under 1,000 words, and length correlates at r=0.04, which is to say not at all. Long isn't better. It also isn't worse. **Plausible.**

The only reliably negative signal I've found is **keyword stuffing**, at roughly −8%.

---

## The expectation nobody sets

Pew, tracking 900 users, found that about **1%** of people who see an AI summary click through to a cited source.

Citations are a brand-impression play. Being named in an answer is worth something. It is not worth what a first-page ranking was worth, and anyone selling you a "115% traffic lift from AI search" is quoting a number that doesn't survive checking.

Say this to clients before you start, not after the first month's report.

---

## Why I published this instead of quietly editing

The rules I got wrong all shared a shape: a number or a mechanism that was true about *something*, applied to a different question, and repeated until it sounded settled.

That's not a failure of research. It's what happens when advice circulates faster than anyone re-checks it. The only defense is being willing to write the retraction, which costs less than it feels like it will.

If you've been teaching any of these, you're in good company. I was too, for a year.
