import asyncio, aiohttp
from aiohttp import web, WSMsgType
WS_UP, HTTP_UP = "ws://127.0.0.1:8000", "http://127.0.0.1:8003"
SKIP = {"host","connection","upgrade","content-length","transfer-encoding","accept-encoding"} | {h for h in ("sec-websocket-key","sec-websocket-version","sec-websocket-extensions","sec-websocket-protocol")}
def clean(h): return {k: v for k, v in h.items() if k.lower() not in SKIP}
async def ws_proxy(req):
    srv = web.WebSocketResponse(heartbeat=30); await srv.prepare(req)
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect(WS_UP + req.path_qs, headers=clean(req.headers)) as cli:
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
    return srv
async def handler(req):
    if req.headers.get("Upgrade", "").lower() == "websocket": return await ws_proxy(req)
    async with aiohttp.ClientSession() as s:
        async with s.request(req.method, HTTP_UP + req.path_qs, headers=clean(req.headers), data=await req.read()) as r:
            return web.Response(status=r.status, body=await r.read(), content_type=r.content_type)
app = web.Application(); app.router.add_route("*", "/{tail:.*}", handler)
import os
web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
