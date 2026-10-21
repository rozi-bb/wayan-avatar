#!/usr/bin/env python3
"""Local server for Wayan.

Serves web/ and hands the browser a short-lived Azure Speech token, so the
subscription key in .env never reaches the page.

    python3 server.py            then open http://127.0.0.1:8765

Stdlib only -- no pip install needed. Reads AZURE_SPEECH_KEY and
AZURE_SPEECH_REGION from the environment or from .env in this folder.
"""

import json
import os
import time
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
PORT = int(os.environ.get("PORT", "8765"))
TOKEN_TTL = 8 * 60  # Azure tokens live 10 minutes; refresh a little early


def load_env():
    env = ROOT / ".env"
    if not env.is_file():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip("'\""))


load_env()
_cache = {"token": None, "expires": 0.0}


def speech_token():
    """Exchange the subscription key for a 10-minute token, cached for 8."""
    key = os.environ.get("AZURE_SPEECH_KEY")
    region = os.environ.get("AZURE_SPEECH_REGION")
    if not key or not region:
        raise RuntimeError("AZURE_SPEECH_KEY dan AZURE_SPEECH_REGION belum diisi di .env")

    if _cache["token"] and time.time() < _cache["expires"]:
        return _cache["token"], region

    url = f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    req = urllib.request.Request(url, data=b"", method="POST",
                                 headers={"Ocp-Apim-Subscription-Key": key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            token = resp.read().decode()
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"Azure menolak key ({err.code}): {err.read().decode(errors='replace')[:200]}")
    _cache.update(token=token, expires=time.time() + TOKEN_TTL)
    return token, region


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/api/speech-token":
            try:
                token, region = speech_token()
                self.send_json(200, {"token": token, "region": region})
            except Exception as err:  # surface the reason to the page
                self.send_json(500, {"error": str(err)})
            return
        super().do_GET()

    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def end_headers(self):
        # wayan.riv changes often while rigging; never serve a stale copy
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(WEB)))
    print(f"Wayan: http://127.0.0.1:{PORT}")
    server.serve_forever()
