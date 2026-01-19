import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(sender_email, sender_pass, recipients, subject, body):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_pass)
            server.send_message(msg)
        return True, None

    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed — check App Password and 2-Step Verification."

    except smtplib.SMTPRecipientsRefused:
        return False, "One or more recipient addresses were refused."

    except Exception as e:
        return False, str(e)
