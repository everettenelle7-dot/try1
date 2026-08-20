from __future__ import annotations

import argparse
import json
import threading
import time
import uuid
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8765
ALLOWED_ACTIONS = {"notify", "turn"}

_lock = threading.Lock()
_commands: deque[dict[str, Any]] = deque()
_events: deque[dict[str, Any]] = deque(maxlen=200)
_state: dict[str, Any] = {
    "game": None,
    "connected": False,
    "updated_at": None,
}


def _now() -> float:
    return time.time()


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "AxunBridge/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[bridge] {self.address_string()} {fmt % args}")

    def _send(self, status: int, payload: Any) -> None:
        data = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            with _lock:
                connected = bool(_state.get("connected"))
            return self._send(200, {"ok": True, "connected": connected, "version": "0.1"})
        if path == "/state":
            with _lock:
                return self._send(200, {"ok": True, "state": dict(_state)})
        if path == "/commands/next":
            with _lock:
                cmd = _commands.popleft() if _commands else None
            return self._send(200, {"ok": True, "command": cmd})
        if path == "/events":
            with _lock:
                events = list(_events)
            return self._send(200, {"ok": True, "events": events})
        return self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
        except Exception as exc:
            return self._send(400, {"ok": False, "error": f"bad_json: {exc}"})

        if path == "/command":
            if not isinstance(payload, dict):
                return self._send(400, {"ok": False, "error": "command_must_be_object"})
            action = payload.get("action")
            if action not in ALLOWED_ACTIONS:
                return self._send(
                    400,
                    {"ok": False, "error": "action_not_allowed", "allowed": sorted(ALLOWED_ACTIONS)},
                )
            command = {
                "id": str(uuid.uuid4()),
                "action": action,
                "args": payload.get("args") or {},
                "created_at": _now(),
            }
            with _lock:
                _commands.append(command)
            return self._send(202, {"ok": True, "command": command})

        if path == "/state":
            if not isinstance(payload, dict):
                return self._send(400, {"ok": False, "error": "state_must_be_object"})
            with _lock:
                _state.update(payload)
                _state["connected"] = True
                _state["updated_at"] = _now()
            return self._send(200, {"ok": True})

        if path == "/event":
            if not isinstance(payload, dict):
                return self._send(400, {"ok": False, "error": "event_must_be_object"})
            event = dict(payload)
            event.setdefault("time", _now())
            with _lock:
                _events.append(event)
            return self._send(200, {"ok": True})

        return self._send(404, {"ok": False, "error": "not_found"})


def main() -> None:
    parser = argparse.ArgumentParser(description="Local bridge between an AI/tool client and a game adapter.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[bridge] listening on http://{args.host}:{args.port}")
    print("[bridge] kill switch: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[bridge] stopped")


if __name__ == "__main__":
    main()
