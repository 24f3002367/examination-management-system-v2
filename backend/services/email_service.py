import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def send_email(to_email, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = current_app.config["SENDER_EMAIL"]
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP(current_app.config["MAIL_HOST"], current_app.config["MAIL_PORT"]) as server:
            server.sendmail(current_app.config["SENDER_EMAIL"], [to_email], msg.as_string())
    except Exception as e:
        print(f"Email error: {e}")