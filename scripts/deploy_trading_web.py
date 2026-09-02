#!/usr/bin/env python3
"""Install/start glab_trading_web add-on on Home Assistant."""
from __future__ import annotations

import asyncio
import json
import os
import sys

import websockets

HA = os.environ.get("HA_URL", "ws://192.168.1.6:8123/api/websocket")
SLUG_HINT = "glab_trading_web"


async def find_slug(sup) -> str | None:
    store = (await sup("/store/addons")).get("result") or {}
    addons = store.get("addons") if isinstance(store, dict) else store
    if not isinstance(addons, list):
        return None
    for item in addons:
        slug = item.get("slug") or ""
        name = (item.get("name") or "").lower()
        if SLUG_HINT in slug or "g-lab trading" in name:
            return slug
    return None


async def main() -> int:
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Set HA_TOKEN (HA Profile -> Long-Lived Access Tokens)", file=sys.stderr)
        return 1

    ws = await websockets.connect(HA)
    await ws.recv()
    await ws.send(json.dumps({"type": "auth", "access_token": token}))
    auth = json.loads(await ws.recv())
    if auth.get("type") != "auth_ok":
        print("HA auth failed", file=sys.stderr)
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
    await sup("/store/repositories/refresh", "post")
    await asyncio.sleep(3)

    slug = await find_slug(sup)
    if not slug:
        print("Add-on not in store yet — push petko-ha-addons to GitHub and refresh again.", file=sys.stderr)
        return 1

    print(f"Found slug: {slug}")
    info = (await sup(f"/addons/{slug}/info")).get("result") or {}
    if not info.get("version"):
        inst = await sup(f"/addons/{slug}/install", "post")
        print("install:", inst.get("success"), inst.get("error"))
        for _ in range(90):
            await asyncio.sleep(3)
            info = (await sup(f"/addons/{slug}/info")).get("result") or {}
            if info.get("version"):
                break
    else:
        rebuild = await sup(f"/addons/{slug}/rebuild", "post")
        print("rebuild:", rebuild.get("success"), rebuild.get("error"))

    start = await sup(f"/addons/{slug}/start", "post")
    print("start:", start.get("success"), start.get("error"))

    for _ in range(30):
        await asyncio.sleep(2)
        info = (await sup(f"/addons/{slug}/info")).get("result") or {}
        state = info.get("state")
        print(f"  state={state}")
        if state == "started":
            break

    await ws.close()
    print("\nLAN: http://192.168.1.6:3010")
    print("Javno: u Cloudflare Tunnel dodaj trade.g-lab.rs -> http://192.168.1.6:3010")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
