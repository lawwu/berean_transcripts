#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_CONFIG="$SCRIPT_DIR/site/berean.yaml"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/berean-site.XXXXXX")"
trap 'rm -rf "$BUILD_DIR"' EXIT

# Pin the shared generator so scheduled builds use the same templates, assets,
# Python package layout, and SQLite runtime until this reference is updated.
GENERATOR_REF="${SERMON_BROWSER_REF:-git+https://github.com/lawwu/sermon-browser.git@14e8a34#subdirectory=generator}"
uvx --from "$GENERATOR_REF" sermon-browser build \
    "$SITE_CONFIG" --out "$BUILD_DIR"

# Keep bookmarks and indexed URLs from the previous root-level page layout.
PYTHONPATH="$SCRIPT_DIR/src" python3 \
    -m berean_transcripts.legacy_redirects "$BUILD_DIR" \
    --site-url "https://lawwu.github.io/berean_transcripts"

# Publish the complete generated tree and remove stale legacy pages.
rsync -a --delete "$BUILD_DIR/" "$SCRIPT_DIR/docs/"
