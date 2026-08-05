# Security

## Reporting

Use GitHub's [private vulnerability reporting](https://github.com/jlank31/marketing-engineer-tools/security/advisories/new) rather than a public issue.

Best effort acknowledgement within a week. This is a small project maintained on weekends; please don't treat that as an SLA.

## Threat model, honestly

Every package here is deliberately small in surface area:

- **`robot-check`** has zero dependencies, makes no network calls, opens no sockets, and executes nothing it reads. It compiles regexes and reads text files you point it at. The realistic risks are a catastrophically backtracking pattern on adversarial input (report it — that's a real bug) and the ordinary risk of pointing any file reader at a path you didn't mean to.
- **`llm-cost`** (from Aug 31) talks to the Anthropic API and reads `ANTHROPIC_API_KEY` from the environment. It never logs the key. It does record token counts and costs.

Nothing here stores credentials, phones home, or collects telemetry. There is no analytics in any package and there won't be.

## What is deliberately not here

This repo is downstream of a private production pipeline. No client data, no credentials, no infrastructure identifiers, and no client-specific configuration is published, and CI enforces that on every push and pull request (`tools/check_brand_leak.py` plus gitleaks). If you ever spot something in this repo that looks like it escaped from a private system — a key, an internal hostname, a customer name — please report it privately. That's a leak, and I'd want to know immediately.
