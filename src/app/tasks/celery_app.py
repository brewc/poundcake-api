"""Celery application configuration."""
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from datetime import datetime
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "poundcake_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.alert_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_time_limit - 10,
    
    # Worker settings
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    worker_max_tasks_per_child=settings.celery_worker_max_tasks_per_child,
    worker_disable_rate_limits=False,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_extended=True,
    
    # Retry policy
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3, "countdown": 60},
    task_retry_backoff=True,
    task_retry_backoff_max=600,
    task_retry_jitter=True,
)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Handle task pre-run signal."""
    logger.info(f"Task started: {task.name} [{task_id}]")
    
    # Update task execution in database
    try:
        from app.core.database import SessionLocal
        from app.models.models import TaskExecution
        
        db = SessionLocal()
        try:
            task_execution = db.query(TaskExecution).filter(
                TaskExecution.task_id == task_id
            ).first()
            
            if task_execution:
                task_execution.status = "started"
                task_execution.started_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error updating task prerun status: {e}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                         retval=None, state=None, **extra):
    """Handle task post-run signal."""
    logger.info(f"Task completed: {task.name} [{task_id}] - State: {state}")
    
    # Update task execution in database
    try:
        from app.core.database import SessionLocal
        from app.models.models import TaskExecution
        
        db = SessionLocal()
        try:
            task_execution = db.query(TaskExecution).filter(
                TaskExecution.task_id == task_id
            ).first()
            
            if task_execution:
                task_execution.status = "success" if state == "SUCCESS" else state.lower()
                task_execution.completed_at = datetime.utcnow()
                task_execution.result = retval if isinstance(retval, dict) else {"result": str(retval)}
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error updating task postrun status: {e}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None,
                        traceback=None, einfo=None, **extra):
    """Handle task failure signal."""
    logger.error(f"Task failed: {sender.name} [{task_id}] - {exception}")
    
    # Update task execution in database
    try:
        from app.core.database import SessionLocal
        from app.models.models import TaskExecution
        
        db = SessionLocal()
        try:
            task_execution = db.query(TaskExecution).filter(
                TaskExecution.task_id == task_id
            ).first()
            
            if task_execution:
                task_execution.status = "failure"
                task_execution.completed_at = datetime.utcnow()
                task_execution.error = str(exception)
                task_execution.traceback = str(traceback) if traceback else None
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error updating task failure status: {e}")
