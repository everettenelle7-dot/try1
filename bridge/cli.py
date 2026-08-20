from __future__ import annotations

import argparse
import json
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8765"


def call(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Tiny Axun Bridge CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    p_notify = sub.add_parser("notify")
    p_notify.add_argument("text")
    p_turn = sub.add_parser("turn")
    p_turn.add_argument("degrees", type=float)

    args = parser.parse_args()
    if args.cmd == "status":
        out = call("GET", "/state")
    elif args.cmd == "notify":
        out = call("POST", "/command", {"action": "notify", "args": {"text": args.text}})
    else:
        out = call("POST", "/command", {"action": "turn", "args": {"degrees": args.degrees}})
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
