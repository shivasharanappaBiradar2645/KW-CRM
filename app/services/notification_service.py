import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models import Contact, Communication, User

def send_email_notification(to_email, subject, body):
    """Sends email using SMTP settings configured in Flask app."""
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_port = current_app.config.get('MAIL_PORT')
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    sender = current_app.config.get('MAIL_DEFAULT_SENDER')

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # If no password configured (dev mode), log notification locally
    if not mail_password:
        current_app.logger.info(f"[DEV MODE] Email to {to_email} | Subject: {subject}\nBody:\n{body}")
        return True

    try:
        server = smtplib.SMTP(mail_server, mail_port)
        if current_app.config.get('MAIL_USE_TLS'):
            server.starttls()
        server.login(mail_username, mail_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def check_and_send_birthday_notifications(app):
    """
    Background job function executed by APScheduler.
    Finds contacts whose birthday or anniversary is today, sends email greeting,
    and logs the activity in the Communications table.
    """
    with app.app_context():
        today = datetime.now().date()
        today_month = today.month
        today_day = today.day

        contacts = Contact.query.all()
        for contact in contacts:
            # 1. Birthday Check
            if contact.birthday and contact.birthday.month == today_month and contact.birthday.day == today_day:
                recipient_email = contact.email
                subject = f"Happy Birthday, {contact.first_name}!"
                body = f"Dear {contact.first_name},\n\nWishing you a fantastic birthday from all of us at KW CRM!\n\nBest regards,\nYour Support Team"

                if recipient_email:
                    send_email_notification(recipient_email, subject, body)

                # Log communication in CRM engagement timeline
                comm = Communication(
                    customer_id=contact.customer_id,
                    direction='Outbound',
                    channel='Email',
                    subject=subject,
                    body=body
                )
                db.session.add(comm)

            # 2. Anniversary Check
            if contact.anniversary and contact.anniversary.month == today_month and contact.anniversary.day == today_day:
                recipient_email = contact.email
                subject = f"Happy Work Anniversary, {contact.first_name}!"
                body = f"Dear {contact.first_name},\n\nCongratulations on your work anniversary today! Thank you for our ongoing partnership.\n\nBest regards,\nYour Support Team"

                if recipient_email:
                    send_email_notification(recipient_email, subject, body)

                # Log communication in CRM engagement timeline
                comm = Communication(
                    customer_id=contact.customer_id,
                    direction='Outbound',
                    channel='Email',
                    subject=subject,
                    body=body
                )
                db.session.add(comm)

        db.session.commit()
