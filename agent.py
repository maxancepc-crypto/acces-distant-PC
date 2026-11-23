"""Agent à lancer sur le PC à contrôler. Demande l'autorisation et affiche une bannière rouge tant qu'il tourne."""
import asyncio, io, json, os, random, sys, threading, tkinter as tk
from tkinter import messagebox
import aiohttp, mss, pyautogui
from PIL import Image

try:
    import ctypes; ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
SERVER = sys.argv[1] if len(sys.argv) > 1 else "https://VOTRE-SERVICE.onrender.com"
KEYS = {"Enter": "enter", "Backspace": "backspace", "Tab": "tab", "Escape": "esc", "Delete": "delete",
        "ArrowLeft": "left", "ArrowRight": "right", "ArrowUp": "up", "ArrowDown": "down",
        "Home": "home", "End": "end", "PageUp": "pageup", "PageDown": "pagedown", " ": "space"}
state = {"on": False, "msg": "En attente d'un visualiseur…"}

def act(d):
    t, (W, H) = d.get("t"), pyautogui.size()
    x, y = int(d.get("x", 0) * W), int(d.get("y", 0) * H)
    if t == "move": pyautogui.moveTo(x, y)
    elif t == "down": pyautogui.mouseDown(x, y, button=d["b"])
    elif t == "up": pyautogui.mouseUp(x, y, button=d["b"])
    elif t == "scroll": pyautogui.scroll(-int(d["d"]))
    elif t == "key":
        k = d["k"]
        if k in ("Shift", "Control", "Alt", "Meta", "CapsLock"): return
        mods = [m for m in ("ctrl", "alt") if d.get(m)]
        if len(k) == 1 and not mods: pyautogui.write(k)
        else: pyautogui.hotkey(*mods, KEYS.get(k, k.lower()))

async def run(code, pw):
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect(SERVER.replace("http", "ws", 1) + "/ws", max_msg_size=0, heartbeat=20) as ws:
            await ws.send_json({"t": "agent", "code": code, "pw": pw})
            async def frames():
                with mss.mss() as sc:
                    mon = sc.monitors[1]
                    while True:
                        if state["on"]:
                            g = sc.grab(mon)
                            img = Image.frombytes("RGB", g.size, g.bgra, "raw", "BGRX")
                            img.thumbnail((1280, 1280))
                            b = io.BytesIO(); img.save(b, "JPEG", quality=50)
                            await ws.send_bytes(b.getvalue())
                        await asyncio.sleep(0.12)
            task = asyncio.create_task(frames())
            async for m in ws:
                if m.type != aiohttp.WSMsgType.TEXT: continue
                d = json.loads(m.data)
                if d["t"] == "viewer":
                    state["on"] = d["on"]
                    state["msg"] = "🔴 Visualiseur connecté : écran partagé et contrôlé" if d["on"] else "En attente d'un visualiseur…"
                elif state["on"]:
                    try: act(d)
                    except Exception: pass
            task.cancel()

def main():
    root = tk.Tk(); root.withdraw()
    if not messagebox.askyesno("Accès à distance", "Autoriser la prise de contrôle de ce PC à distance ?\n\nVous pourrez arrêter à tout moment."):
        return
    code, pw = str(random.randint(10**8, 10**9 - 1)), str(random.randint(10**5, 10**6 - 1))
    threading.Thread(target=lambda: asyncio.run(run(code, pw)), daemon=True).start()
    bar = tk.Toplevel(root); bar.title("Accès à distance"); bar.attributes("-topmost", True); bar.configure(bg="#c42b1c")
    bar.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    lbl = tk.Label(bar, fg="white", bg="#c42b1c", font=("Segoe UI", 11), justify="left", padx=14, pady=8)
    lbl.pack()
    tk.Button(bar, text="Arrêter l'accès", command=lambda: os._exit(0)).pack(pady=(0, 10))
    def refresh():
        lbl.config(text=f"Code : {code}     Mot de passe : {pw}\n{state['msg']}"); bar.after(500, refresh)
    refresh(); root.mainloop()

main()
