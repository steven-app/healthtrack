from flask import render_template, current_app
from flask_mail import Message
from app import mail
from threading import Thread
import sys
import traceback

def send_async_email(app, msg):
    """Send email asynchronously to avoid blocking the request handler"""
    with app.app_context():
        try:
            app.logger.info(f"Sending email to {msg.recipients} with subject: {msg.subject}")
            mail.send(msg)
            app.logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            app.logger.error(f"Failed to send email: {str(e)}")
            app.logger.error(traceback.format_exc())

def send_email(subject, sender, recipients, text_body, html_body):
    """General purpose email sending function"""
    try:
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        
        current_app.logger.info(f"Preparing to send email to {recipients} with subject: {subject}")
        
        # For debugging, try sending directly without a thread first
        app = current_app._get_current_object()
        if app.config.get('TESTING', False):
            # Send synchronously in testing mode
            with app.app_context():
                mail.send(msg)
                current_app.logger.info(f"Sent email synchronously to {recipients}")
        else:
            # Use a thread to send email asynchronously
            Thread(
                target=send_async_email,
                args=(app, msg)
            ).start()
            current_app.logger.info(f"Started async thread to send email to {recipients}")
    except Exception as e:
        current_app.logger.error(f"Error preparing email: {str(e)}")
        current_app.logger.error(traceback.format_exc())

def send_password_reset_email(user):
    """Send password reset email to user"""
    try:
        current_app.logger.info(f"Preparing password reset email for user {user.id} ({user.email})")
        token = user.get_reset_password_token()
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        send_email(
            subject='[HealthTrack] Reset Your Password',
            sender=sender,
            recipients=[user.email],
            text_body=render_template('email/reset_password.txt', user=user, token=token),
            html_body=render_template('email/reset_password.html', user=user, token=token)
        )
    except Exception as e:
        current_app.logger.error(f"Error in send_password_reset_email: {str(e)}")
        current_app.logger.error(traceback.format_exc()) 