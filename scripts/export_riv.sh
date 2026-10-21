#!/usr/bin/env bash
# Export the Rive file open in the editor to web/wayan.riv, overwriting it.
#
# The Rive desktop editor is sandboxed on macOS and cannot write into the
# project, so the export is fetched as inline base64 from the editor's local
# MCP server (http://127.0.0.1:9791/mcp) and written here instead.
#
# Usage: scripts/export_riv.sh            (Rive editor open, file "wayan" active)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/web/wayan.riv"
URL=http://127.0.0.1:9791/mcp
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SID=$(curl -si "$URL" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"export-script","version":"1"}}}' \
  | tr -d '\r' | sed -n 's/^mcp-session-id: //p')
[ -n "$SID" ] || { echo "Rive editor MCP not reachable at $URL" >&2; exit 1; }

DEST_JSON=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$TMP")
curl -s "$URL" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"export_file","arguments":{"format":"riv","destination":'"$DEST_JSON"',"inline_base64":true}}}' \
  > "$TMP/response.txt"

python3 - "$TMP/response.txt" "$OUT" <<'PY'
import base64, json, sys
raw = open(sys.argv[1], encoding="utf-8").read()
lines = [l[5:].strip() for l in raw.splitlines() if l.startswith("data:")]
body = json.loads(lines[-1] if lines else raw)
payload = json.loads(body["result"]["content"][0]["text"])
if "data" not in payload:
    sys.exit("export did not return inline data: " + json.dumps(payload)[:300])
if not payload["filename"].startswith("wayan"):
    sys.exit("active Rive file is not 'wayan' (got %s) - switch tabs first" % payload["filename"])
open(sys.argv[2], "wb").write(base64.b64decode(payload["data"]))
print("wrote", sys.argv[2], len(base64.b64decode(payload["data"])), "bytes")
PY
