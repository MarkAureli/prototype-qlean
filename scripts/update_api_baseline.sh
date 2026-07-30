#!/usr/bin/env bash
# Maintainer helper — refresh the committed core-API baseline.
#
# Run at RELEASE time, after bumping VERSION: this snapshots the current core API
# as the new baseline that the semver gate diffs future PRs against. Then commit
# core-api.baseline.txt and tag the release.
set -euo pipefail
cd "$(dirname "$0")/.."
source "$HOME/.elan/env" 2>/dev/null || true

lake env lean scripts/Checker.lean >/dev/null
ver="$(tr -d '[:space:]' < VERSION)"
{
  echo "# qlean core API baseline — version: ${ver}"
  echo "# regenerate with scripts/update_api_baseline.sh at release; then commit + tag."
  sort build/qlean_core_api.txt
} > core-api.baseline.txt
echo "baseline refreshed for version ${ver} ($(grep -c ' : ' core-api.baseline.txt) core decls)"
