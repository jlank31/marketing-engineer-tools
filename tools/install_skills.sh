#!/usr/bin/env bash
# Copy the Claude Code skills in this repo into ~/.claude/skills/.
#
# Copies rather than symlinks, so a `git pull` here can never silently change
# how your agent behaves. Re-run it when you want the updates.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../skills" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

shopt -s nullglob
skills=("$SRC"/*/)
if [ ${#skills[@]} -eq 0 ]; then
  echo "No skills found in $SRC. Is this a full checkout?"
  exit 1
fi

mkdir -p "$DEST"
for dir in "${skills[@]}"; do
  name="$(basename "$dir")"
  if [ -e "$DEST/$name" ]; then
    echo "  skip     $name (already at $DEST/$name — remove it first to replace)"
    continue
  fi
  cp -R "$dir" "$DEST/$name"
  echo "  install  $name"
done
echo
echo "Installed to $DEST. Restart Claude Code to pick them up."
