import os
import psycopg2
from psycopg2 import extras
import bcrypt
import sys
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1") 
DB_NAME = os.environ.get("DB_NAME", "registration_data") 
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "Anirban@42")
DB_PORT = os.environ.get("DB_PORT", "5432")
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print("❌ Database connection error:", e)
        sys.exit(1)
def register_user(name, address, phone_number, alt_phone_number, email, password):
    """Insert a new user into userinfo. Returns True on success, False otherwise."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO userinfo (name, address, phone_number, alternate_phone_number, email, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, address, phone_number, alt_phone_number, email, hashed))
        conn.commit()
        return True
    except Exception as e:
        print("❌ register_user error:", e)
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def login_user(email, password):
    """Check login credentials and return user info if valid."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        cur.execute("SELECT id, name, password_hash FROM userinfo WHERE email = %s", (email,))
        row = cur.fetchone()
        if not row:
            return None 

        stored_hash = row["password_hash"].encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return {"id": row["id"], "name": row["name"], "email": email}
        return None
    except Exception as e:
        print("❌ login_user error:", e)
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def set_reset_token(email, token):
    """Store reset token for user. Returns True on success."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("ALTER TABLE userinfo ADD COLUMN IF NOT EXISTS reset_token VARCHAR(200)")
        cur.execute("UPDATE userinfo SET reset_token = %s WHERE email = %s", (token, email))
        conn.commit()
        return True
    except Exception as e:
        print("❌ set_reset_token error:", e)
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def get_email_by_token(token):
    """Return email associated with reset token, or None."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT email FROM userinfo WHERE reset_token = %s", (token,))
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        print("❌ get_email_by_token error:", e)
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def update_password_by_token(token, new_password):
    """Set new password (hashed) for user with given reset token. Returns True on success."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("""
            UPDATE userinfo
            SET password_hash = %s, reset_token = NULL
            WHERE reset_token = %s
        """, (hashed, token))
        conn.commit()
        return cur.rowcount == 1
    except Exception as e:
        print("❌ update_password_by_token error:", e)
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def get_family_info(user_id):
    """Fetch family member info for a specific user."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        cur.execute("SELECT * FROM familyinfo WHERE user_id = %s", (user_id,))
        family = cur.fetchone()
        return dict(family) if family else None
    except Exception as e:
        print("❌ get_family_info error:", e)
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def update_family_info(user_id, name, phone_number, alt_phone_number, email):
    """Insert or update family info."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM familyinfo WHERE user_id = %s", (user_id,))
        exists = cur.fetchone()
        if exists:
            cur.execute("""
                UPDATE familyinfo
                SET name = %s, phone_number = %s, alt_phone_number = %s, email = %s
                WHERE user_id = %s
            """, (name, phone_number, alt_phone_number, email, user_id))
        else:
            cur.execute("""
                INSERT INTO familyinfo (user_id, name, phone_number, alt_phone_number, email)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, name, phone_number, alt_phone_number, email))
        conn.commit()
        return True
    except Exception as e:
        print("❌ update_family_info error:", e)
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def add_medical_report(user_id, filename, description):
    """Insert uploaded medical report into database."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO medical_reports (user_id, filename, description)
            VALUES (%s, %s, %s)
        """, (user_id, filename, description))
        conn.commit()
        return True
    except Exception as e:
        print("❌ add_medical_report error:", e)
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
def get_medical_reports(user_id):
    """Fetch all medical reports for a user."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT filename, description, upload_date
            FROM medical_reports
            WHERE user_id = %s
            ORDER BY upload_date DESC
        """, (user_id,))
        reports = cur.fetchall()
        return [
            {"filename": r[0], "description": r[1], "upload_date": r[2]}
            for r in reports
        ]
    except Exception as e:
        print("❌ get_medical_reports error:", e)
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
