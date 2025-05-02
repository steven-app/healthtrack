from flask import current_app, render_template
from flask_mail import Message
from app import mail
import jwt
from datetime import datetime, timedelta

def send_password_reset_email(user):
    token = jwt.encode(
        {
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=1)
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    msg = Message('Reset Your Password',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    
    msg.body = render_template('email/reset_password.txt',
                             user=user,
                             token=token)
    msg.html = render_template('email/reset_password.html',
                             user=user,
                             token=token)
    
    mail.send(msg) 