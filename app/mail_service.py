from typing import List
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config import settings
import os
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS= True,
    MAIL_SSL_TLS= False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), f'api_v1/templates/email')
)

async def send_email_async(subject: str, email_to: List[str], body: dict):
    message = MessageSchema(
        subject=subject,
        recipients=email_to,
        body=body,
        subtype='html',
    )
    
    fm = FastMail(conf)
    await fm.send_message(message, template_name='email.html')

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: dict):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype='html',
    )
    fm = FastMail(conf)
    background_tasks.add_task(
    fm.send_message, message, template_name='email.html')