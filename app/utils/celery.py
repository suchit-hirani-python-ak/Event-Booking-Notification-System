import asyncio
from datetime import datetime
from typing import cast
from pymongo.asynchronous.database import AsyncDatabase
from celery import Celery
import os
from app.db.session import db_manager
from app.core.config import settings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from app.repositories.notification_repository import NotificationRepository

current_dir = os.path.dirname(__file__)
template_path = os.path.join(current_dir, "templates")

celery_app = Celery(
    "worker",
    broker = settings.redis_url,
    backend=settings.redis_url,
    include=['app.utils.celery']
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

@celery_app.task(
    bind=True, 
    name="send_booking_notification_task",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=60,  # Starts at 60s, then 120s, 240s...
    retry_jitter=True
)
def send_booking_notification_task(self, email: str, booking_id: str):
    """
    Background task to send email and log to MongoDB.
    Replaces the NotificationService class for distributed execution.
    """
    # 2. Get the current attempt number (1, 2, or 3)
    attempt = self.request.retries + 1
    if db_manager.db is None:
        asyncio.run(db_manager.connect_to_mongo())
    
    # 2. FIX: Pass .db (the MongoDB object), NOT the manager itself
    repo = NotificationRepository(db_manager.db) 
    
    try:
        # 3. Prepare the Email Message
        message = MessageSchema(
            subject="Booking Confirmation",
            recipients=[email],
            template_body={
                "booking_id": booking_id,
                "user_name": email.split('@')[0]
            },
            subtype=MessageType.html
        )
        
        # 4. Execute Async Operations inside Sync Celery Worker
        fm = FastMail(conf)
        
        async def run_notification():
            # Send the email
            await fm.send_message(message, template_name="booking_template.html")
            # Log SUCCESS to MongoDB
            await repo.log_notification(booking_id, email, "sent", attempt)

        asyncio.run(run_notification())
        return {"status": "success", "attempt": attempt}

    except Exception as exc:
        # 5. Log FAILURE for this attempt to MongoDB before retrying
        asyncio.run(repo.log_notification(
            booking_id, 
            email, 
            "failed", 
            attempt, 
            message=str(exc)
        ))
        
        # 6. Raise for Celery to handle the next retry
        raise self.retry(exc=exc)