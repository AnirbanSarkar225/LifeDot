from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, time, random, threading, collections
from datetime import datetime
from werkzeug.utils import secure_filename
from database import (
    register_user, login_user, get_family_info, 
    update_family_info, add_medical_report, get_medical_reports
)
from resetlink import send_reset_link, reset_password
from email_al import send_email

# Point to the frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'LifeDot02')
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

SENDER_EMAIL = os.environ.get("HEART_SENDER")
SENDER_PASS = os.environ.get("HEART_PASS")
FAMILY_EMAILS = [e.strip() for e in os.environ.get("HEART_FAMILY", "").split(",") if e.strip()]

# BPM monitoring
bpm_window = collections.deque(maxlen=12)
_lock = threading.Lock()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def generate_bpm():
    """Generate realistic BPM values"""
    return int(max(40, min(200, random.gauss(75, 10))))

def monitor_loop():
    """Background thread to continuously generate BPM"""
    while True:
        with _lock:
            bpm_window.append(generate_bpm())
        time.sleep(1)

# Start monitoring thread
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
    except Exception as e:
        print(f"❌ Static file error for {path}: {e}")
        return "File not found", 404

# ---------- AUTH ----------

@app.route("/register", methods=["POST"])
def register():
    try:
        d = request.get_json()
        required = ["name", "address", "phone_number", "alt_phone_number", "email", "password"]
        
        if not all(k in d for k in required):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        success = register_user(
            d["name"], 
            d["address"], 
            d["phone_number"], 
            d["alt_phone_number"], 
            d["email"], 
            d["password"]
        )
        
        if success:
            print(f"✅ User registered: {d['email']}")
        else:
            print(f"❌ Registration failed for: {d['email']}")
        
        return jsonify({"success": success})
    
    except Exception as e:
        print(f"❌ Register error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        d = request.get_json()
        
        if not d.get("email") or not d.get("password"):
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        user = login_user(d["email"], d["password"])
        
        if user:
            print(f"✅ User logged in: {d['email']}")
            return jsonify({"success": True, "user": user})
        else:
            print(f"❌ Login failed for: {d['email']}")
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
    
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/forgot-password", methods=["POST"])
def forgot():
    try:
        d = request.get_json()
        email = d.get("email")
        
        if not email:
            return jsonify({"success": False, "error": "Email required"}), 400
        
        success = send_reset_link(email)
        
        if success:
            print(f"✅ Reset link sent to: {email}")
        else:
            print(f"❌ Failed to send reset link to: {email}")
        
        return jsonify({"success": success})
    
    except Exception as e:
        print(f"❌ Forgot password error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/reset-password", methods=["POST"])
def reset_password_endpoint():
    try:
        d = request.get_json()
        email = d.get("email")
        new_password = d.get("new_password")
        
        if not email or not new_password:
            return jsonify({"success": False, "error": "Email and new password required"}), 400
        
        # For simplicity, directly update password by email
        # In production, use token-based reset
        success = reset_password(email, new_password)
        
        return jsonify({"success": success})
    
    except Exception as e:
        print(f"❌ Reset password error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/reset-password/<token>", methods=["POST"])
def reset_with_token(token):
    try:
        d = request.get_json()
        new_password = d.get("password")
        
        if not new_password:
            return jsonify({"success": False, "error": "Password required"}), 400
        
        success = reset_password(token, new_password)
        
        if success:
            print(f"✅ Password reset successful via token")
        else:
            print(f"❌ Password reset failed - invalid token")
        
        return jsonify({"success": success})
    
    except Exception as e:
        print(f"❌ Reset password (token) error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------- BPM ----------

@app.route("/bpm", methods=["GET"])
def bpm():
    try:
        with _lock:
            current = bpm_window[-1] if bpm_window else generate_bpm()
            avg = int(sum(bpm_window) / len(bpm_window)) if bpm_window else current
        
        print(f"📊 BPM: {current}, AVG: {avg}")
        return jsonify({"bpm": current, "avg_bpm": avg})
    
    except Exception as e:
        print(f"❌ BPM error: {e}")
        return jsonify({"error": str(e)}), 500

# ---------- EMERGENCY ----------

@app.route("/emergency", methods=["POST"])
def emergency():
    try:
        # Get JSON data if available
        data = request.get_json() or {}
        user_id = data.get("user_id", "Unknown")
        bpm_value = data.get("bpm", "Unknown")
        is_manual = data.get("manual", False)
        is_auto = data.get("auto", False)
        
        print(f"🚨 Emergency alert triggered:")
        print(f"   User ID: {user_id}")
        print(f"   BPM: {bpm_value}")
        print(f"   Manual: {is_manual}, Auto: {is_auto}")
        
        # Check email configuration
        if not SENDER_EMAIL or not SENDER_PASS:
            error_msg = "Email credentials not configured"
            print(f"❌ {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500
        
        if not FAMILY_EMAILS:
            error_msg = "No emergency contacts configured"
            print(f"❌ {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500
        
        # Prepare email content
        alert_type = "Manual" if is_manual else ("Automatic" if is_auto else "Emergency")
        condition = f"Heart rate: {bpm_value} BPM" if bpm_value != "Unknown" else "Abnormal heart rate detected"
        location = "Simulated GPS: 22.5726° N, 88.3639° E"
        
        subject = f"🚨 LifeDot {alert_type} Emergency Alert"
        body = f"""
🚨 LifeDot Emergency Alert Triggered

Alert Type: {alert_type}
User ID: {user_id}
Condition: {condition}
Time: {now()}
Location: {location}

This is an automated alert from the LifeDot health monitoring system.

Please check on the patient immediately.

---
LifeDot Health Monitoring System
"""
        
        # Send email
        print(f"📧 Sending emergency email to {len(FAMILY_EMAILS)} recipient(s)...")
        success, err = send_email(SENDER_EMAIL, SENDER_PASS, FAMILY_EMAILS, subject, body)
        
        if success:
            print(f"✅ Emergency email sent successfully to: {', '.join(FAMILY_EMAILS)}")
            return jsonify({"success": True, "message": "Emergency alert sent"})
        else:
            error_msg = f"Failed to send email: {err}"
            print(f"❌ {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500
    
    except Exception as e:
        error_msg = f"Emergency endpoint error: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

# ---------- FAMILY INFO ----------

@app.route("/family/<int:user_id>", methods=["GET"])
def get_family(user_id):
    try:
        family = get_family_info(user_id)
        return jsonify({"success": True, "family": family})
    except Exception as e:
        print(f"❌ Get family error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/family/<int:user_id>", methods=["POST"])
def update_family(user_id):
    try:
        d = request.get_json()
        success = update_family_info(
            user_id,
            d.get("name", ""),
            d.get("phone", ""),
            d.get("alt_phone", ""),
            d.get("email", "")
        )
        return jsonify({"success": success})
    except Exception as e:
        print(f"❌ Update family error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------- MEDICAL REPORTS ----------

@app.route("/upload-report/<int:user_id>", methods=["POST"])
def upload(user_id):
    try:
        # Check if file is present
        if 'report' not in request.files and 'file' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        
        f = request.files.get('report') or request.files.get('file')
        description = request.form.get('description', 'No description')
        
        if f.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Secure the filename
        filename = secure_filename(f.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        
        # Save file
        f.save(filepath)
        
        # Add to database
        add_medical_report(user_id, filename, description)
        
        print(f"✅ Report uploaded: {filename} for user {user_id}")
        return jsonify({"success": True, "filename": filename})
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/reports/<int:user_id>", methods=["GET"])
def get_reports(user_id):
    try:
        reports = get_medical_reports(user_id)
        return jsonify({"success": True, "reports": reports})
    except Exception as e:
        print(f"❌ Get reports error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------- HEALTH CHECK ----------

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "timestamp": now(),
        "bpm_monitoring": len(bpm_window) > 0,
        "email_configured": bool(SENDER_EMAIL and SENDER_PASS),
        "emergency_contacts": len(FAMILY_EMAILS)
    })

# ---------- ERROR HANDLERS ----------

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 LIFEDOT SERVER STARTING")
    print("=" * 60)
    print(f"✅ Frontend directory: {FRONTEND_DIR}")
    print(f"✅ Upload directory: {UPLOAD_FOLDER}")
    print(f"✅ Email configured: {bool(SENDER_EMAIL and SENDER_PASS)}")
    print(f"✅ Emergency contacts: {len(FAMILY_EMAILS)}")
    print(f"✅ Server running at: http://127.0.0.1:8000")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=8000, debug=True)