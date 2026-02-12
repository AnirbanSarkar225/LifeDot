import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import set_reset_token, get_email_by_token, update_password_by_token
import os

SENDER_EMAIL = os.environ.get("HEART_SENDER")
SENDER_PASS = os.environ.get("HEART_PASS")

def send_reset_link(email):
    """Generate token, store it, send reset email."""
    try:
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Store token in database
        if not set_reset_token(email, token):
            return False
        
        # Create reset link
        reset_link = f"https://lifedot-topaz.vercel.app/resetpassword.html?token={token}"
        
        # Email content
        subject = "🔐 LifeDot Password Reset"
        body = f"""
Hello,

You requested a password reset for your LifeDot account.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you did not request this reset, please ignore this email.

Best regards,
LifeDot Team
"""
        
        # Send email
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        if not SENDER_EMAIL or not SENDER_PASS:
            print("❌ Email credentials not configured")
            return False
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.send_message(msg)
        
        print(f"✅ Reset link sent to {email}")
        return True
        
    except Exception as e:
        print(f"❌ send_reset_link error: {e}")
        return False

def reset_password(token, new_password):
    """Update password using reset token."""
    try:
        # Verify token exists
        email = get_email_by_token(token)
        if not email:
            print("❌ Invalid or expired token")
            return False
        
        # Update password
        success = update_password_by_token(token, new_password)
        
        if success:
            print(f"✅ Password reset successful for {email}")
        else:
            print(f"❌ Password update failed for {email}")
        
        return success
        
    except Exception as e:
        print(f"❌ reset_password error: {e}")
        return False