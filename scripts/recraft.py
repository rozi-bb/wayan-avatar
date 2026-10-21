#!/usr/bin/env python3
"""Recraft API helper for the Avatar AI asset pipeline.

Stdlib only -- no pip install needed.

Reads RECRAFT_API_TOKEN from the environment, or from .env next to the
project root if the variable is not already set.

Usage:
    python3 scripts/recraft.py balance
    python3 scripts/recraft.py gen "prompt" --model recraftv4_1_vector --out assets/vector/name
    python3 scripts/recraft.py gen "prompt" --model recraftv4_1_flash --n 4 --out assets/drafts/name
    python3 scripts/recraft.py vectorize assets/drafts/name_1.webp --out assets/vector/name
    python3 scripts/recraft.py style ref1.png ref2.png --model recraftv4_styles
"""

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://external.api.recraft.ai/v1"
ROOT = Path(__file__).resolve().parent.parent

# Price per image in USD, for the --dry-run cost estimate.
PRICES = {
    "recraftv4_1_flash": 0.007,
    "recraftv4_1": 0.035,
    "recraftv4_1_vector": 0.08,
    "recraftv4_1_pro": 0.21,
    "recraftv4_1_pro_vector": 0.30,
    "recraftv4_styles": 0.035,
    "recraftv4_styles_vector": 0.05,
    "recraftv4_styles_pro_vector": 0.12,
    "recraftv2_vector": 0.044,
    "recraftv3_vector": 0.08,
}


def token():
    tok = os.environ.get("RECRAFT_API_TOKEN")
    if not tok:
        env = ROOT / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line.startswith("RECRAFT_API_TOKEN="):
                    tok = line.split("=", 1)[1].strip().strip("'\"")
                    break
    if not tok:
        sys.exit(
            "RECRAFT_API_TOKEN is not set. Put it in .env or export it.\n"
            "Create a token at https://app.recraft.ai/profile/api"
        )
    return tok


def call(method, path, payload=None):
    """Plain HTTP with Bearer auth. Prints status + body and stops on non-2xx."""
    url = f"{API}{path}"
    data = None
    headers = {"Authorization": f"Bearer {token()}"}
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        ctype = err.headers.get("Content-Type", "")
        sys.exit(f"HTTP {err.code} ({ctype}): {body}")
    except urllib.error.URLError as err:
        sys.exit(f"Network error: {err.reason}")


def data_url(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    import base64

    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def download(url, dest):
    """Image URLs expire after ~24h, so always save a local copy."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp:
        dest.write_bytes(resp.read())
    print(f"  saved {dest.relative_to(ROOT)} ({dest.stat().st_size // 1024} KB)")


def ext_for(model, image_format):
    return ".svg" if "vector" in model else f".{image_format}"


def cmd_balance(args):
    me = call("GET", "/users/me")
    units = me["credits"]
    print(f"{me['name']} <{me['email']}>")
    print(f"credits: {units} API units = ${units / 1000:.2f}")
    print(f"  ~{int(units / 80)} SVG at recraftv4_1_vector ($0.08)")
    print(f"  ~{int(units / 7)} drafts at recraftv4_1_flash ($0.007)")


def cmd_gen(args):
    body = {"prompt": args.prompt, "model": args.model, "n": args.n}
    if args.size:
        body["size"] = args.size
    if args.seed is not None:
        body["random_seed"] = args.seed
    if args.style_id:
        body["style_id"] = args.style_id
    if args.colors:
        body["controls"] = {
            "colors": [{"rgb": list(map(int, c.split(",")))} for c in args.colors]
        }
    if "vector" not in args.model:
        body["image_format"] = args.image_format

    est = PRICES.get(args.model, 0) * args.n
    if args.dry_run:
        print(json.dumps(body, indent=2))
        print(f"\nestimated cost: ${est:.3f}")
        return

    print(f"generating {args.n}x {args.model} (est ${est:.3f}) ...")
    result = call("POST", "/images/generations", body)
    print(f"  charged {result['credits']} units (${result['credits'] / 1000:.3f})")
    if result.get("style_id"):
        print(f"  style_id: {result['style_id']}")

    ext = ext_for(args.model, args.image_format)
    for i, image in enumerate(result["data"], 1):
        suffix = f"_{i}" if args.n > 1 else ""
        download(image["url"], ROOT / f"{args.out}{suffix}{ext}")


def cmd_vectorize(args):
    print(f"vectorizing {args.image} (est $0.010) ...")
    body = {"image_url": data_url(args.image), "shape_stacking": args.shape_stacking}
    result = call("POST", "/images/vectorize", body)
    print(f"  charged {result['credits']} units (${result['credits'] / 1000:.3f})")
    # vectorize returns a single `image`, not a `data` array
    download(result["image"]["url"], ROOT / f"{args.out}.svg")


def cmd_style(args):
    print(f"creating style from {len(args.images)} reference(s) (est $0.005) ...")
    body = {
        "image_urls": [data_url(p) for p in args.images],
        "model": args.model,
        "match": args.match,
    }
    result = call("POST", "/styles", body)
    print(f"style_id: {result['id']}")
    print("Reuse it with: --style-id " + result["id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("balance", help="show remaining API units").set_defaults(
        func=cmd_balance
    )

    g = sub.add_parser("gen", help="generate images")
    g.add_argument("prompt")
    g.add_argument("--model", default="recraftv4_1_vector")
    g.add_argument("--n", type=int, default=1, help="1 to 6")
    g.add_argument("--size", default="1:1", help="w:h ratio, e.g. 1:1 or 16:9")
    g.add_argument("--seed", type=int, help="random_seed for reproducibility")
    g.add_argument("--style-id", dest="style_id")
    g.add_argument("--colors", nargs="*", help='RGB triples, e.g. "255,102,0"')
    g.add_argument("--image-format", default="webp", choices=["webp", "png"])
    g.add_argument("--out", default="assets/out", help="path prefix, no extension")
    g.add_argument("--dry-run", action="store_true", help="print body + cost only")
    g.set_defaults(func=cmd_gen)

    v = sub.add_parser("vectorize", help="raster file to SVG ($0.01)")
    v.add_argument("image")
    v.add_argument("--shape-stacking", default="hierarchical",
                   choices=["hierarchical", "cut_out"])
    v.add_argument("--out", default="assets/vector/out")
    v.set_defaults(func=cmd_vectorize)

    s = sub.add_parser("style", help="create a reusable style from references")
    s.add_argument("images", nargs="+")
    s.add_argument("--model", default="recraftv4_styles")
    s.add_argument("--match", default="flexible", choices=["flexible", "precise"])
    s.set_defaults(func=cmd_style)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
