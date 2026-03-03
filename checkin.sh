#!/bin/bash
# Run this script in Terminal.app (outside Cursor) so git commit is not wrapped with --trailer.
# Or upgrade Git to a version that supports: git commit --trailer
set -e
cd "$(dirname "$0")"
git add -A
git status
git commit -m "Initial commit: Tool Registry MCP API Hub"
git push -u origin main
echo "Done. Code pushed to git@github.com:srirama4n/tool_registry.git"
