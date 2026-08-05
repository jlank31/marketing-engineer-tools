# editor-rules

Learn an editor's style from what they change.

```bash
pip install editor-rules
editor-rules edits.jsonl
```

```
Editor rules: 46 before/after pairs

  Substitutions (3):
     7x   "vendors" -> "brands"
     4x   "utilize" -> "use"
     3x   "aren't" -> "and founders are already"   (report only)

  Deletions (2):
     5x   "very"
     3x   "in order to"
```

Then paste the rules into your AI prompt:

```bash
editor-rules edits.jsonl --prompt-block >> PROMPT.md
```

```
## Apply these every time

- Write "brands", not "vendors" (7x).
- Write "use", not "utilize" (4x).
- Cut "very" (5x). The editor removes it every time.
```

**No model, no API key, no network.** It's `difflib` over word tokens. Costs nothing, same answer every time.

## Why this exists

The same editor cut the same word from my drafts 7 weeks running before I noticed. I only caught it because I eventually ran a diff instead of reading.

Your editing history is training data you're already producing and almost certainly throwing away. Every redline is someone telling you their preferences in the clearest terms available, and most teams read each one once and bin it.

## The part worth understanding

Look at that third substitution in the output above, the one marked `(report only)`:

```
3x   "aren't" -> "and founders are already"
```

That's an artifact of how the diff aligned a heavy rewrite, not a preference. Feed it into a prompt and you've confidently taught the model something false.

So `--prompt-block` only takes swaps where **both sides are 3 words or fewer** and **the replacement is no longer than the original**. The full report keeps everything, because a person can spot an artifact and a prompt cannot.

That asymmetry (conservative for the machine, permissive for the human) is the whole design.

## Input format

Any file with a before and an after column. `.jsonl`, `.json`, or `.csv`:

```jsonl
{"original_text": "We utilize vendors", "edited_text": "We use brands"}
```

Recognized column names: `original_text`/`edited_text`, `before`/`after`, `old`/`new`, `original`/`edited`. Getting your edits into one of those is usually a single query.

Deliberately no database adapter, so this package makes no assumptions about your stack.

## As a library

```python
from editor_rules import compute, render_prompt_block

digest = compute(edits, min_count=3)
digest.substitutions   # [(before, after, count), ...]
digest.deletions       # [(phrase, count), ...]
print(render_prompt_block(digest))
```

## Honest limits

**A pattern needs to repeat before it's a pattern.** Default threshold is 3. On a thin corpus you'll get an empty block, which is the correct answer rather than a failure.

**It sees words, not intent.** It'll tell you the editor keeps cutting "very". It won't tell you why, and sometimes there isn't a why.

**It can't tell a preference from a house rule from a one-off mood.** That's your job, which is why the report shows you everything.

## License

MIT. Part of [marketing-engineer-tools](https://github.com/jlank31/marketing-engineer-tools).
