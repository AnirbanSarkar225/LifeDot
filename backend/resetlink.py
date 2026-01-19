import psycopg2
import secrets
import bcrypt
import os
from email_al import send_email

DB_CONFIG = dict(
    dbname="registration_data",
    user="postgres",
    password="Anirban@42",
    host="127.0.0.1",
    port="5432"
)

SENDER_EMAIL = os.environ.get("HEART_SENDER")
SENDER_PASS = os.environ.get("HEART_PASS")


def send_reset_link(email):
    conn = cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT id FROM userinfo WHERE email = %s", (email,))
        if not cur.fetchone():
            return False

        token = secrets.token_urlsafe(32)
        cur.execute("ALTER TABLE userinfo ADD COLUMN IF NOT EXISTS reset_token VARCHAR(200)")
        cur.execute("UPDATE userinfo SET reset_token = %s WHERE email = %s", (token, email))
        conn.commit()
        reset_url = f"http://127.0.0.1:8000/resetpassword.html?token={token}"
        subject = "LifeDot Password Reset"
        body = f"Click the link below to reset your password:\n{reset_url}"

        success, _ = send_email(SENDER_EMAIL, SENDER_PASS, [email], subject, body)
        return success

    finally:
        if cur: cur.close()
        if conn: conn.close()


def reset_password(token, new_password):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        cur.execute("""
            UPDATE userinfo
            SET password_hash = %s, reset_token = NULL
            WHERE reset_token = %s
        """, (hashed, token))
        conn.commit()
        return cur.rowcount == 1

    finally:
        if cur: cur.close()
        if conn: conn.close()