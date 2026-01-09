"""SQLAlchemy models for database tables."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class APICall(Base):
    """Model for storing all non-GET API calls."""
    
    __tablename__ = "api_calls"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(36), unique=True, nullable=False, index=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    headers = Column(JSON, nullable=True)
    query_params = Column(JSON, nullable=True)
    body = Column(JSON, nullable=True)
    client_host = Column(String(100), nullable=True)
    status_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationship to alerts
    alerts = relationship("Alert", back_populates="api_call", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_api_calls_created_at", "created_at"),
        Index("idx_api_calls_method_path", "method", "path"),
    )
    
    def __repr__(self) -> str:
        return f"<APICall {self.request_id} {self.method} {self.path}>"


class Alert(Base):
    """Model for storing Alertmanager alerts."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    api_call_id = Column(Integer, ForeignKey("api_calls.id"), nullable=False)
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # firing, resolved
    alert_name = Column(String(200), nullable=False, index=True)
    severity = Column(String(20), nullable=True, index=True)
    instance = Column(String(500), nullable=True)
    labels = Column(JSON, nullable=False)
    annotations = Column(JSON, nullable=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    generator_url = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing information
    processing_status = Column(
        String(20), 
        default="pending", 
        nullable=False
    )  # pending, processing, completed, failed
    task_id = Column(String(36), nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationship to API call
    api_call = relationship("APICall", back_populates="alerts")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_alerts_status", "status"),
        Index("idx_alerts_processing_status", "processing_status"),
        Index("idx_alerts_created_at", "created_at"),
        Index("idx_alerts_alert_name_severity", "alert_name", "severity"),
    )
    
    def __repr__(self) -> str:
        return f"<Alert {self.fingerprint} {self.alert_name} {self.status}>"


class TaskExecution(Base):
    """Model for tracking Celery task executions."""
    
    __tablename__ = "task_executions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), unique=True, nullable=False, index=True)
    task_name = Column(String(200), nullable=False)
    alert_fingerprint = Column(String(64), nullable=True, index=True)
    status = Column(String(20), nullable=False)  # pending, started, success, failure, retry
    args = Column(JSON, nullable=True)
    kwargs = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    traceback = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_task_executions_status", "status"),
        Index("idx_task_executions_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<TaskExecution {self.task_id} {self.task_name} {self.status}>"
