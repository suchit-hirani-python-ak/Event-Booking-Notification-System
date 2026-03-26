import asyncio
from celery import Celery
import os
from app.core.config import settings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings

current_dir = os.path.dirname(__file__)
template_path = os.path.join(current_dir, "templates")

celery_app = Celery(
    "worker",
    broker = settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_from,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=template_path) # type: ignore

@celery_app.task(name="send_welcome_email_task")
def send_welcome_email_task(email: str):
    # Professional HTML Email Template

    user_name = email.split('@')[0]
    message = MessageSchema(
        subject="Welcome to Event Booking!",
        recipients=[email], # type: ignore
        template_body={"email":email,"user_name":user_name},
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    asyncio.run(fm.send_message(message,template_name="register_template.html"))
    return {"status": "email_sent", "recipient": email}