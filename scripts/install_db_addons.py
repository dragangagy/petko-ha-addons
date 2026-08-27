#!/usr/bin/env python3
"""Install/start petko_admin and petko_maintenance on HA."""
from __future__ import annotations

import asyncio
import json
import os
import sys

import websockets

HA = "ws://192.168.1.6:8123/api/websocket"
ADDONS = [
    ("petko_admin", {}),
    ("petko_maintenance", {"postgres_password": "homeassistant"}),
]


async def main() -> int:
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("HA_TOKEN not set", file=sys.stderr)
        return 1

    ws = await websockets.connect(HA)
    await ws.recv()
    await ws.send(json.dumps({"type": "auth", "access_token": token}))
    auth = json.loads(await ws.recv())
    if auth.get("type") != "auth_ok":
        print("auth failed:", auth, file=sys.stderr)
        return 1

    msg_id = 0

    async def sup(endpoint: str, method: str = "get", data: dict | None = None, timeout: int = 900):
        nonlocal msg_id
        msg_id += 1
        payload = {"id": msg_id, "type": "supervisor/api", "endpoint": endpoint, "method": method}
        if data is not None:
            payload["data"] = data
        await ws.send(json.dumps(payload))
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            resp = json.loads(raw)
            if resp.get("id") == msg_id:
                return resp

    print("Refreshing add-on store...")
    refresh = await sup("/store/repositories/refresh", "post")
    print(" refresh:", refresh.get("success"), refresh.get("error"))

    for slug, options in ADDONS:
        print(f"\n=== {slug} ===")
        inst = await sup(f"/addons/{slug}/install", "post")
        print(" install:", inst.get("success"), inst.get("error"))
        if options:
            cfg = await sup(f"/addons/{slug}/options", "post", {"options": options})
            print(" options:", cfg.get("success"), cfg.get("error"))
        rebuild = await sup(f"/addons/{slug}/rebuild", "post")
        print(" rebuild:", rebuild.get("success"), rebuild.get("error"))
        for _ in range(60):
            await asyncio.sleep(5)
            info = (await sup(f"/addons/{slug}/info")).get("result") or {}
            state = info.get("state")
            version = info.get("version")
            print(f"  state={state} version={version}")
            if state == "started":
                break
        start = await sup(f"/addons/{slug}/start", "post")
        print(" start:", start.get("success"), start.get("error"))

    await ws.close()
    print("\nDone. Adminer: http://192.168.1.6:8080")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
