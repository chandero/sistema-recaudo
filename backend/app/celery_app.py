"""Configuración de Celery para tareas en segundo plano."""
import os
from celery import Celery
from celery.schedules import crontab

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "sistema_recaudo",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.state_expiration", "app.tasks.document_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 min max per task
    task_soft_time_limit=300,  # soft limit 5 min
    worker_prefetch_multiplier=1,
    beat_schedule={
        "auto-expire-states": {
            "task": "app.tasks.state_expiration.check_state_expirations",
            "schedule": crontab(minute="*/15"),  # Cada 15 minutos
        },
    },
)
