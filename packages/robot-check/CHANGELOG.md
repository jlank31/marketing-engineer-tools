# Changelog

All notable changes to `robot-check`.

## 0.1.0 - 2026-08-05

First release. Lexical + statistical per-text detectors (`content_quality`) and
corpus-level reuse detection (`repetition`), plus the `scan` CLI.

API is unstable until 1.0. The only stability promise is
`check_text(text, profile) -> Result`.
