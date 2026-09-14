#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${HOME}/.agents/skills"
DRY=0
while [[ $# -gt 0 ]]; do case "$1" in --dry-run) DRY=1; shift;; --target) TARGET="$2"; shift 2;; *) echo "unknown argument: $1" >&2; exit 2;; esac; done
for skill in sponsor-job-agent-dev sponsor-job-agent-ops; do
  src="$ROOT/skills/$skill"; dst="$TARGET/$skill"
  if find "$src" -type l | grep -q .; then echo "refusing symlink in $src" >&2; exit 3; fi
  if [[ $DRY -eq 1 ]]; then echo "would install $skill -> $dst"; continue; fi
  mkdir -p "$TARGET"; tmp="${dst}.tmp.$$"; rm -rf "$tmp"; cp -R "$src" "$tmp"; rm -rf "$dst"; mv "$tmp" "$dst"; echo "installed $skill -> $dst"
done
