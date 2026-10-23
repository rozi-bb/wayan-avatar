#!/usr/bin/env python3
"""Call one Rive editor MCP tool with arguments from a JSON file.

For payloads too large to paste into a chat tool call (e.g. shapes generated
from an SVG). Talks to the editor's local MCP server like export_riv.sh.

    python3 scripts/rive_mcp.py path_editor args.json

Stdlib only. Prints the tool's text result.
"""

import json
import sys
import urllib.request

URL = "http://127.0.0.1:9791/mcp"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def post(body, session=None):
    headers = dict(HEADERS, **({"mcp-session-id": session} if session else {}))
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.headers.get("mcp-session-id"), resp.read().decode()


def parse(raw):
    lines = [l[5:].strip() for l in raw.splitlines() if l.startswith("data:")]
    return json.loads(lines[-1] if lines else raw)


def main():
    tool, args_file = sys.argv[1], sys.argv[2]
    session, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-11-25", "capabilities": {},
        "clientInfo": {"name": "rive-mcp-script", "version": "1"}}})
    if not session:
        sys.exit(f"Rive editor MCP not reachable at {URL}")
    args = json.load(open(args_file))
    _, raw = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                   "params": {"name": tool, "arguments": args}}, session)
    body = parse(raw)
    if "error" in body:
        sys.exit(json.dumps(body["error"]))
    for part in body["result"]["content"]:
        print(part.get("text", ""))


if __name__ == "__main__":
    main()
