from __future__ import annotations

import argparse
import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8765"


def request_json(method: str, path: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    angle_z = 0.0
    print("[mock-game] connected")
    while True:
        try:
            request_json("POST", "/state", {
                "game": "mock-skyrim",
                "player": {"x": 0, "y": 0, "z": 0, "angle_z": angle_z},
            })
            packet = request_json("GET", "/commands/next")
            cmd = packet.get("command")
            if cmd:
                if cmd["action"] == "notify":
                    print("[mock-game] NOTIFY:", cmd.get("args", {}).get("text", ""))
                elif cmd["action"] == "turn":
                    angle_z = (angle_z + float(cmd.get("args", {}).get("degrees", 0))) % 360
                    print("[mock-game] TURN ->", angle_z)
                request_json("POST", "/event", {
                    "type": "command_executed",
                    "command_id": cmd["id"],
                    "action": cmd["action"],
                })
        except URLError as exc:
            print("[mock-game] bridge unavailable:", exc)
        if args.once:
            break
        time.sleep(0.5)


if __name__ == "__main__":
    main()
