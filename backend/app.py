import json
import os
import time

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# ==================================================
# APP SETUP
# ==================================================

app = Flask(
    __name__,
    template_folder=os.path.join(
        os.path.dirname(__file__),
        "..", "dashboard", "templates"
    ),
    static_folder=os.path.join(
        os.path.dirname(__file__),
        "..", "dashboard", "static"
    )
)

CORS(app)

# ==================================================
# CONSTANTS
# ==================================================

PORT = 5005
HISTORY_MAX = 100
OFFLINE_TIMEOUT = 5.0  # seconds

DISASTERS = [
    "landslide",
    "earthquake",
    "cloudburst",
    "forest_fire"
]

# Location number → disaster name
LOCATION_MAP = {
    "1": "landslide",
    "2": "forest_fire",
    "3": "cloudburst",
    "4": "earthquake"
}

# ==================================================
# STATE STORE
# ==================================================

# Per-disaster runtime data.
# Flask NEVER modifies state/confidence/verification_result.
# Only the brain owns those. Flask only stores what the brain sends.

state_store = {
    d: {
        "state": "SAFE",
        "confidence": 0.0,
        "last_update": None,
        "raw": {},
        "raw_history": [],   # list of {"t": str, "v": float}
        "conf_history": [],  # list of {"t": str, "v": float}
    }
    for d in DISASTERS
}

# ==================================================
# PENDING ACTIONS
# ==================================================

# Admin dashboard clicks queue an action here.
# The brain polls this endpoint and consumes the action.
# Flask stores the intent only — brain decides what to do.

pending_actions = {d: None for d in DISASTERS}

# ==================================================
# USER STORAGE
# ==================================================

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ==================================================
# PAGES
# ==================================================

@app.route("/")
def index():
    return render_template("admin.html")


@app.route("/admin")
def admin_page():
    return render_template("admin.html")


@app.route("/user")
def user_page():
    return render_template("user.html")


# ==================================================
# BRAIN → BACKEND
# Brain calls this after every processing cycle.
# Backend stores the data — does NOT recalculate anything.
# ==================================================

@app.route("/api/update/<disaster>", methods=["POST"])
def update(disaster):

    if disaster not in DISASTERS:
        return jsonify({"error": "unknown disaster"}), 400

    data = request.json
    if not data:
        return jsonify({"error": "no data"}), 400

    store = state_store[disaster]

    # Store authoritative state sent by brain
    store["state"] = data.get("state", store["state"])
    store["confidence"] = data.get("confidence", store["confidence"])
    store["last_update"] = time.time()
    store["raw"] = data.get("raw", {})

    # History — raw sensor primary value + confidence
    ts = time.strftime("%H:%M:%S")
    raw_val = data.get("raw_value", 0.0)

    store["raw_history"].append({"t": ts, "v": raw_val})
    store["conf_history"].append({"t": ts, "v": round(store["confidence"], 2)})

    # Trim to HISTORY_MAX
    if len(store["raw_history"]) > HISTORY_MAX:
        store["raw_history"] = store["raw_history"][-HISTORY_MAX:]

    if len(store["conf_history"]) > HISTORY_MAX:
        store["conf_history"] = store["conf_history"][-HISTORY_MAX:]

    return jsonify({"ok": True})


# ==================================================
# BRAIN ← BACKEND
# Brain polls this to receive admin actions.
# Action is consumed (one-time read) — cleared after retrieval.
# Flask queues the intent. Brain decides what to do with it.
# ==================================================

@app.route("/api/pending/<disaster>", methods=["GET"])
def get_pending(disaster):

    if disaster not in DISASTERS:
        return jsonify({"action": None}), 400

    action = pending_actions[disaster]

    # Consume the action — cleared so it is not applied twice
    if action is not None:
        pending_actions[disaster] = None

    return jsonify({"action": action})


# ==================================================
# ADMIN → BACKEND
# Dashboard buttons queue actions for the brain to consume.
# Flask stores the intent only.
# Flask NEVER directly changes state, confidence, or
# verification_result — only the brain does that.
# ==================================================

@app.route("/api/confirm/<disaster>", methods=["POST"])
def confirm(disaster):

    if disaster not in DISASTERS:
        return jsonify({"error": "unknown disaster"}), 400

    pending_actions[disaster] = "CONFIRM"

    return jsonify({"ok": True, "queued": "CONFIRM"})


@app.route("/api/reject/<disaster>", methods=["POST"])
def reject(disaster):

    if disaster not in DISASTERS:
        return jsonify({"error": "unknown disaster"}), 400

    pending_actions[disaster] = "FALSE_POSITIVE"

    return jsonify({"ok": True, "queued": "FALSE_POSITIVE"})


@app.route("/api/reset/<disaster>", methods=["POST"])
def reset(disaster):

    if disaster not in DISASTERS:
        return jsonify({"error": "unknown disaster"}), 400

    pending_actions[disaster] = "RESET"

    return jsonify({"ok": True, "queued": "RESET"})


# ==================================================
# STATUS API
# Admin dashboard polls this every second.
# Returns brain-authoritative state + history arrays.
# ==================================================

@app.route("/api/status")
def status():

    result = {}
    now = time.time()

    for d in DISASTERS:

        s = state_store[d]
        lu = s["last_update"]
        online = (
            lu is not None and
            (now - lu) < OFFLINE_TIMEOUT
        )

        result[d] = {
            "state": s["state"],
            "confidence": s["confidence"],
            "last_update": lu,
            "online": online,
            "raw": s["raw"],
            "raw_history": s["raw_history"],
            "conf_history": s["conf_history"],
        }

    return jsonify(result)


# ==================================================
# USER STATUS API
# User dashboard polls this with their location number.
# Returns filtered status for their disaster zone.
# ==================================================

@app.route("/api/user_status")
def user_status():

    location = request.args.get("location", "1")
    disaster = LOCATION_MAP.get(location, "landslide")

    s = state_store[disaster]
    now = time.time()
    lu = s["last_update"]
    online = (
        lu is not None and
        (now - lu) < OFFLINE_TIMEOUT
    )

    return jsonify({
        "disaster": disaster,
        "state": s["state"],
        "confidence": s["confidence"],
        "online": online,
        "raw": s["raw"],
    })


# ==================================================
# USER REGISTRATION
# ==================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.json
    if not data:
        return jsonify({"error": "no data"}), 400

    users = load_users()

    entry = {
        "name": data.get("name", "").strip(),
        "phone": data.get("phone", "").strip(),
        "location": data.get("location", "1"),
        "registered_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    users.append(entry)
    save_users(users)

    return jsonify({"ok": True})


@app.route("/api/users")
def get_users():
    return jsonify(load_users())


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    print("\n" + "=" * 44)
    print("  DISASTER MANAGEMENT BACKEND V2")
    print("=" * 44)
    print(f"  Port    : {PORT}")
    print(f"  Admin   : http://localhost:{PORT}/admin")
    print(f"  User    : http://localhost:{PORT}/user")
    print(f"  History : {HISTORY_MAX} points per graph")
    print(f"  Timeout : {OFFLINE_TIMEOUT}s offline threshold")
    print("=" * 44 + "\n")

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        threaded=True
    )
