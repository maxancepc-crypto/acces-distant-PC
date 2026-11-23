"""Relais : met en relation un agent (PC contrôlé) et un visualiseur (navigateur)."""
import os, json, hmac
from aiohttp import web, WSMsgType

rooms = {}  # code -> {"agent": ws, "viewer": ws|None, "pw": str, "fails": int}
HERE = os.path.dirname(os.path.abspath(__file__))

async def index(request):
    return web.FileResponse(os.path.join(HERE, "index.html"))

async def ws_handler(request):
    ws = web.WebSocketResponse(max_msg_size=8 * 1024 * 1024, heartbeat=20)
    await ws.prepare(request)
    role, room, code = None, None, None
    async for m in ws:
        if m.type == WSMsgType.TEXT:
            d = json.loads(m.data)
            if role is None:
                if d.get("t") == "agent":
                    code = str(d.get("code"))
                    room = rooms[code] = {"agent": ws, "viewer": None, "pw": str(d.get("pw")), "fails": 0}
                    role = "agent"
                    await ws.send_json({"t": "ok"})
                elif d.get("t") == "viewer":
                    r = rooms.get(str(d.get("code")))
                    if not r or r["fails"] >= 5 or not hmac.compare_digest(r["pw"], str(d.get("pw"))):
                        if r: r["fails"] += 1
                        await ws.send_json({"t": "err", "m": "Code ou mot de passe incorrect"})
                        continue
                    if r["viewer"] and not r["viewer"].closed:
                        await ws.send_json({"t": "err", "m": "Un visualiseur est déjà connecté"})
                        continue
                    role, room, code = "viewer", r, str(d.get("code"))
                    r["viewer"] = ws
                    await ws.send_json({"t": "ok"})
                    await r["agent"].send_json({"t": "viewer", "on": True})
            elif role == "viewer":
                await room["agent"].send_str(m.data)  # événements souris/clavier
        elif m.type == WSMsgType.BINARY and role == "agent":
            v = room["viewer"]
            if v and not v.closed:
                await v.send_bytes(m.data)  # images de l'écran
    if role == "agent":
        rooms.pop(code, None)
        if room["viewer"] and not room["viewer"].closed:
            await room["viewer"].close()
    elif role == "viewer":
        room["viewer"] = None
        if not room["agent"].closed:
            await room["agent"].send_json({"t": "viewer", "on": False})
    return ws

app = web.Application()
app.add_routes([web.get("/", index), web.get("/ws", ws_handler)])
if __name__ == "__main__":
    web.run_app(app, port=int(os.environ.get("PORT", 8080)))
