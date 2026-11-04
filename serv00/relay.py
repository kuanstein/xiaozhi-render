# Tiny HTTP+WebSocket relay: ESP32 -> (this, reachable from China) -> Render server
import asyncio, os, aiohttp
from aiohttp import web, WSMsgType
UP = os.environ["UPSTREAM"].rstrip("/")  # e.g. https://xxxx.onrender.com
UP_HTTP = os.environ.get("UP_HTTP", UP)
UP_WS = os.environ.get("UP_WS", UP.replace("https://", "wss://").replace("http://", "ws://"))
PORT = int(os.environ.get("PORT", "8080"))
SKIP = {"host","connection","upgrade","content-length","transfer-encoding","accept-encoding",
        "sec-websocket-key","sec-websocket-version","sec-websocket-extensions","sec-websocket-protocol"}
def clean(h): return {k: v for k, v in h.items() if k.lower() not in SKIP}
async def ws_proxy(req):
    srv = web.WebSocketResponse(heartbeat=30); await srv.prepare(req)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.ws_connect(UP_WS + req.path_qs, headers=clean(req.headers), heartbeat=30) as cli:
                async def up():
                    async for m in srv:
                        if m.type == WSMsgType.TEXT: await cli.send_str(m.data)
                        elif m.type == WSMsgType.BINARY: await cli.send_bytes(m.data)
                        else: break
                    await cli.close()
                async def down():
                    async for m in cli:
                        if m.type == WSMsgType.TEXT: await srv.send_str(m.data)
                        elif m.type == WSMsgType.BINARY: await srv.send_bytes(m.data)
                        else: break
                    await srv.close()
                await asyncio.gather(up(), down(), return_exceptions=True)
    except Exception as e:
        print("ws relay error:", e)
    return srv
async def handler(req):
    if req.headers.get("Upgrade", "").lower() == "websocket": return await ws_proxy(req)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.request(req.method, UP_HTTP + req.path_qs, headers=clean(req.headers), data=await req.read(), timeout=aiohttp.ClientTimeout(total=90)) as r:
                return web.Response(status=r.status, body=await r.read(), content_type=r.content_type)
    except Exception as e:
        return web.Response(status=502, text=f"upstream error: {e}")
async def keepalive(app):  # stops Render's free tier from sleeping
    async def loop():
        while True:
            try:
                async with aiohttp.ClientSession() as s:
                    await s.get(UP_HTTP + "/xiaozhi/ota/", timeout=aiohttp.ClientTimeout(total=60))
            except Exception as e: print("keepalive failed:", e)
            await asyncio.sleep(600)
    app["ka"] = asyncio.create_task(loop())
app = web.Application(); app.on_startup.append(keepalive)
app.router.add_route("*", "/{tail:.*}", handler)
web.run_app(app, host="0.0.0.0", port=PORT)
