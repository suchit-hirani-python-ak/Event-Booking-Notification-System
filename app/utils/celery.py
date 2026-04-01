import asyncio
from celery import Celery
import os
from app.db.session import db_manager, get_db
from app.core.config import settings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from app.repositories.notification_repository import NotificationRepository
from app.utils.retrynotification import retry

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


@retry(max_attempts=3, delay=2, backoff=2)
async def run_notification_logic(email: str, booking_id: str, repo: NotificationRepository, fm: FastMail, attempt_num: int = 1):
    # 1. Log the specific attempt in DB before sending
    await repo.log_notification(
        booking_id=booking_id, 
        email=email, 
        status="pending", 
        attempt=attempt_num
    )

    message = MessageSchema(
        subject="Booking Confirmation",
        recipients=[email], # type: ignore
        template_body={"booking_id": booking_id, "user_name": email.split('@')[0]},
        subtype=MessageType.html
    )
    
    await fm.send_message(message, template_name="booking_template.html")
    
    # 2. Update to 'sent' on success
    await repo.log_notification(booking_id, email, status="sent", attempt=attempt_num)
    return "Notification Processed"


async def async_task_wrapper(email: str, booking_id: str):
    # 1. Connect fresh within the CURRENT loop (Replaces Depends)
    await db_manager.connect_to_mongo()
    
    try:
        # 2. Get the DB instance (Replaces db = Depends(get_db))
        db = await get_db() 
        
        # 3. Inject it into your repository
        repo = NotificationRepository(db)
        fm = FastMail(conf)

        return await run_notification_logic(
            email=email, 
            booking_id=booking_id, 
            repo=repo, 
            fm=fm
        )
    finally:
        # 4. Cleanup: Close so the next task doesn't reuse a dead loop's client
        await db_manager.close_mongo_connection()

@celery_app.task(bind=True, name="send_booking_notification_task")
def send_booking_notification_task(self, email: str, booking_id: str):
    try:
        # Only one asyncio.run call per task execution
        return asyncio.run(async_task_wrapper(email, booking_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=600, max_retries=2)