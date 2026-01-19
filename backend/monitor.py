from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, time, random, threading, collections
from datetime import datetime
from werkzeug.utils import secure_filename
from database import register_user, login_user
from resetlink import send_reset_link, reset_password
from email_al import send_email

# Point to the frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'LifeDot02')
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

SENDER_EMAIL = os.environ.get("HEART_SENDER")
SENDER_PASS = os.environ.get("HEART_PASS")
FAMILY_EMAILS = [e.strip() for e in os.environ.get("HEART_FAMILY","").split(",") if e]

bpm_window = collections.deque(maxlen=12)
_lock = threading.Lock()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def generate_bpm():
    return int(max(40, random.gauss(75, 5)))

def monitor_loop():
    while True:
        with _lock:
            bpm_window.append(generate_bpm())
        time.sleep(1)

threading.Thread(target=monitor_loop, daemon=True).start()

# ---------- SERVE HTML FILES ----------

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static HTML, CSS, JS files from frontend directory"""
    try:
        return send_from_directory(FRONTEND_DIR, path)
    except:
        return "File not found", 404

# ---------- AUTH ----------

@app.route("/register", methods=["POST"])
def register():
    d = request.get_json()
    ok = register_user(d["name"], d["address"], d["phone_number"], d["alt_phone_number"], d["email"], d["password"])
    return jsonify({"success": ok})

@app.route("/login", methods=["POST"])
def login():
    d = request.get_json()
    user = login_user(d["email"], d["password"])
    return jsonify({"success": bool(user), "user": user})

@app.route("/forgot-password", methods=["POST"])
def forgot():
    d = request.get_json()
    return jsonify({"success": send_reset_link(d["email"])})

@app.route("/reset-password/<token>", methods=["POST"])
def reset(token):
    d = request.get_json()
    return jsonify({"success": reset_password(token, d["password"])})

# ---------- BPM ----------

@app.route("/bpm", methods=["GET"])
def bpm():
    with _lock:
        current = bpm_window[-1] if bpm_window else generate_bpm()
        avg = int(sum(bpm_window)/len(bpm_window)) if bpm_window else current
    return jsonify({"bpm": current, "avg_bpm": avg})

# ---------- EMERGENCY ----------

@app.route("/emergency", methods=["POST"])
def emergency():
    if not SENDER_EMAIL or not SENDER_PASS or not FAMILY_EMAILS:
        return jsonify({"success": False, "error": "Email not configured"}), 500

    condition = "Abnormal heart rate detected"
    location = "Simulated GPS: 22.5726° N, 88.3639° E"

    subject = "🚨 LifeDot Emergency Alert"
    body = f"""
LifeDot Emergency Detected

Condition: {condition}
Time: {now()}
Location: {location}
"""

    success, err = send_email(SENDER_EMAIL, SENDER_PASS, FAMILY_EMAILS, subject, body)
    return jsonify({"success": success, "error": err})

# ---------- UPLOAD ----------

@app.route("/upload-report/<int:user_id>", methods=["POST"])
def upload(user_id):
    f = request.files.get("report")
    if not f:
        return jsonify({"success": False}), 400
    name = secure_filename(f.filename)
    f.save(os.path.join(app.config["UPLOAD_FOLDER"], name))
    return jsonify({"success": True, "filename": name})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print(f"✅ Serving frontend from: {FRONTEND_DIR}")
    print(f"✅ Server running at: http://127.0.0.1:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
