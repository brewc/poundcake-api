"""Celery tasks for alert processing."""
from typing import Dict, Any
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.core.logging import get_logger
from app.core.database import SessionLocal
from app.models.models import Alert, TaskExecution

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="process_alert",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    retry_backoff=True,
)
def process_alert(self, alert_data: Dict[str, Any], alert_fingerprint: str) -> Dict[str, Any]:
    """
    Process a single alert from Alertmanager.
    
    Args:
        alert_data: Alert data from Alertmanager webhook
        alert_fingerprint: Alert fingerprint for identification
        
    Returns:
        Dict with processing results
    """
    logger.info(f"Processing alert: {alert_fingerprint}")
    
    db = SessionLocal()
    try:
        # Get the alert from database
        alert = db.query(Alert).filter(Alert.fingerprint == alert_fingerprint).first()
        
        if not alert:
            logger.error(f"Alert not found: {alert_fingerprint}")
            return {
                "status": "error",
                "fingerprint": alert_fingerprint,
                "message": "Alert not found in database"
            }
        
        # Update alert processing status
        alert.processing_status = "processing"
        alert.task_id = self.request.id
        db.commit()
        
        # Simulate alert processing logic
        # In a real application, this is where you would:
        # - Analyze the alert
        # - Determine appropriate actions
        # - Execute remediation workflows
        # - Send notifications
        # - Update monitoring systems
        # etc.
        
        logger.info(f"Alert processing logic for: {alert.alert_name}")
        
        # Example: Log alert details
        processing_result = {
            "fingerprint": alert_fingerprint,
            "alert_name": alert.alert_name,
            "severity": alert.severity,
            "status": alert.status,
            "instance": alert.instance,
            "actions_taken": [
                "Logged alert details",
                "Updated processing status",
                # Add your custom processing logic here
            ]
        }
        
        # Update alert with success status
        alert.processing_status = "completed"
        alert.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully processed alert: {alert_fingerprint}")
        
        return {
            "status": "success",
            "result": processing_result
        }
        
    except Exception as e:
        logger.error(f"Error processing alert {alert_fingerprint}: {e}", exc_info=True)
        
        # Update alert with error status
        try:
            alert = db.query(Alert).filter(Alert.fingerprint == alert_fingerprint).first()
            if alert:
                alert.processing_status = "failed"
                alert.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating alert failure status: {db_error}")
        
        # Re-raise to trigger Celery retry
        raise
        
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="process_alert_batch",
    autoretry_for=(Exception,),
)
def process_alert_batch(self, alert_fingerprints: list[str]) -> Dict[str, Any]:
    """
    Process a batch of alerts by queuing individual processing tasks.
    
    Args:
        alert_fingerprints: List of alert fingerprints to process
        
    Returns:
        Dict with batch processing results
    """
    logger.info(f"Processing batch of {len(alert_fingerprints)} alerts")
    
    task_ids = []
    
    db = SessionLocal()
    try:
        for fingerprint in alert_fingerprints:
            # Get alert data
            alert = db.query(Alert).filter(Alert.fingerprint == fingerprint).first()
            
            if not alert:
                logger.warning(f"Alert not found for batch processing: {fingerprint}")
                continue
            
            # Queue individual alert processing task
            alert_data = {
                "fingerprint": alert.fingerprint,
                "status": alert.status,
                "labels": alert.labels,
                "annotations": alert.annotations,
            }
            
            result = process_alert.delay(alert_data, fingerprint)
            task_ids.append(result.id)
            
            # Record task execution
            task_execution = TaskExecution(
                task_id=result.id,
                task_name="process_alert",
                alert_fingerprint=fingerprint,
                status="pending",
                args=[],
                kwargs={"alert_data": alert_data, "alert_fingerprint": fingerprint}
            )
            db.add(task_execution)
        
        db.commit()
        
        logger.info(f"Queued {len(task_ids)} alert processing tasks")
        
        return {
            "status": "success",
            "queued_tasks": len(task_ids),
            "task_ids": task_ids
        }
        
    except Exception as e:
        logger.error(f"Error processing alert batch: {e}", exc_info=True)
        db.rollback()
        raise
        
    finally:
        db.close()


@celery_app.task(name="cleanup_old_data")
def cleanup_old_data(days: int = 30) -> Dict[str, Any]:
    """
    Clean up old data from the database.
    
    Args:
        days: Number of days to keep data
        
    Returns:
        Dict with cleanup results
    """
    logger.info(f"Cleaning up data older than {days} days")
    
    from datetime import timedelta
    from app.models.models import APICall, TaskExecution
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old API calls (and cascade to alerts)
        deleted_api_calls = db.query(APICall).filter(
            APICall.created_at < cutoff_date
        ).delete(synchronize_session=False)
        
        # Delete old task executions
        deleted_tasks = db.query(TaskExecution).filter(
            TaskExecution.created_at < cutoff_date
        ).delete(synchronize_session=False)
        
        db.commit()
        
        logger.info(
            f"Cleanup completed: deleted {deleted_api_calls} API calls "
            f"and {deleted_tasks} task executions"
        )
        
        return {
            "status": "success",
            "deleted_api_calls": deleted_api_calls,
            "deleted_task_executions": deleted_tasks,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        db.rollback()
        raise
        
    finally:
        db.close()
