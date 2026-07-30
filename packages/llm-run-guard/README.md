# llm-run-guard

Know what a run costs, and stop it when it blows the budget.

```bash
pip install "llm-run-guard[anthropic]"
```

```python
from llm_run_guard import TrackedClient, tracked_run

with tracked_run("nightly", cap_usd=5.00) as run:
    client = TrackedClient("summarizer")
    client.messages.create(model="claude-opus-5", ...)   # unchanged

print(run.summary["cost_usd"])
```

One line changes: `Anthropic()` becomes `TrackedClient()`. Everything else about the SDK stays the same.

## Three things most cost tracking gets wrong

**Cache tokens are additive, not a subset.** The API reports `cache_creation_input_tokens` and `cache_read_input_tokens` *separately* from `input_tokens`. Bill them at 1.25x and 0.10x of the input rate, on top. Skip them and every cached call is understated.

**Server-side tools cost money.** Web search bills per request and never appears in the token counts.

**Unknown models are the dangerous one.** The common implementation returns `$0` for a model ID it doesn't recognize. That means a new model version is silently free, and therefore invisible to any budget cap built on those numbers. This prices unknown models at the *most expensive* tier and warns once per process. Overstate, never understate.

## The cap is the point

Cost reporting tells you what happened yesterday. A cap stops a runaway retry loop from spending a day's budget in twenty minutes while you're at lunch.

```python
with tracked_run("batch", cap_usd=2.00):
    ...   # raises RunCostExceeded mid-loop, not afterwards
```

A run killed by its own cap still reports what it spent.

## Keeping a pipeline alive overnight

```python
from llm_run_guard import with_healing, response_text, safe_parse_json

@with_healing(attempts=3)
def summarize(doc):
    return response_text(client.messages.create(...))
```

`response_text()` exists because of a real outage: extended-thinking models return a thinking block as `content[0]`, so every pipeline written as `response.content[0].text` started raising the day that shipped. It walks the array for the first block that carries text.

`safe_parse_json()` handles fences, prose either side, and trailing commas. It deliberately does **not** call a model to repair JSON, because every one of those cases is fixable locally and reaching for an API call is how a cheap failure becomes an expensive one.

Retries skip errors where retrying is pointless (`TypeError`, auth failures, credit-balance errors) rather than burning three attempts on the same bug.

**The part worth reading twice is `metrics()`.** The optional escalation path calls a bigger model to diagnose failures, which costs real money. The counters tell you how often plain retry was enough:

```python
from llm_run_guard import metrics
metrics()["retry_fixed_share"]   # 0.9 means the expensive path is mostly waste
```

Most people add the rescue path and never check whether it earns its keep.

## From the terminal

```bash
llm-cost price claude-opus-5 --in 50000 --out 2000 --cache-read 40000
llm-cost models      # the price table
llm-cost check       # warns if the table has gone stale
```

## Honest limits

**Prices are a dated snapshot, not live data.** Verify anything that matters against [Anthropic's pricing page](https://www.anthropic.com/pricing). Price corrections are the one contribution actively wanted here.

**The budget is per-process.** Fan out across processes and each gets its own.

**This measures what you spend, not whether it was worth spending.** No tool tells you that.

## License

MIT. Part of [marketing-engineer-tools](https://github.com/jlank31/marketing-engineer-tools).
