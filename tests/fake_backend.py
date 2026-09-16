#!/usr/bin/env python3
"""Local deterministic backend used to smoke-test the ADB shim and MaaCore."""

from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path

from aiohttp import web
from PIL import Image, ImageDraw

LOG_FILE = Path(os.getenv("MAA_ONLINE_FAKE_LOG", Path(__file__).with_name("fake-actions.jsonl")))


def make_frame() -> bytes:
    image = Image.new("RGB", (1280, 720), "#111827")
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 100, 1180, 620), outline="#60a5fa", width=4)
    draw.text((480, 340), "MAA ONLINE SMOKE TEST", fill="white")
    output = BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


FRAME = make_frame()


async def record(request: web.Request) -> web.Response:
    payload = await request.json() if request.can_read_body else {}
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"path": request.path, "payload": payload}) + "\n")
    return web.json_response({"status": "ok"})


async def info(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "width": 1280, "height": 720})


async def screenshot(_: web.Request) -> web.Response:
    return web.Response(body=FRAME, content_type="image/png")


app = web.Application()
app.router.add_get("/info", info)
app.router.add_get("/screencap", screenshot)
for path in ("/start", "/exit", "/click", "/swipe", "/input"):
    app.router.add_post(path, record)

if __name__ == "__main__":
    LOG_FILE.unlink(missing_ok=True)
    web.run_app(app, host="127.0.0.1", port=22889)
