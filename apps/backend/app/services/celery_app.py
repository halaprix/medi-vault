"""Celery application and task definitions for medi-vault document processing."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "medi_vault",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.services.celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_max_retries=2,
    beat_schedule_filename="/tmp/medi-vault/celerybeat-schedule",
)
