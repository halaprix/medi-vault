"""SQLAlchemy ORM models for medi-vault."""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────

class ProcessingStatus(str, enum.Enum):
    pending = "pending"
    ocr_processing = "ocr_processing"
    llm_parsing = "llm_parsing"
    normalizing = "normalizing"
    complete = "complete"
    failed = "failed"


class BiomarkerCategory(str, enum.Enum):
    lipid_panel = "lipid_panel"
    metabolic_panel = "metabolic_panel"
    thyroid = "thyroid"
    cbc = "cbc"
    vitamins_minerals = "vitamins_minerals"
    hormones = "hormones"
    inflammation = "inflammation"
    liver = "liver"
    kidney = "kidney"
    diabetes = "diabetes"
    other = "other"


class OutOfRangeDirection(str, enum.Enum):
    high = "high"
    low = "low"
    normal = "normal"
    indeterminate = "indeterminate"


class MetricType(str, enum.Enum):
    weight_kg = "weight_kg"
    steps = "steps"
    sleep_hours = "sleep_hours"
    resting_heart_rate_bpm = "resting_heart_rate_bpm"
    active_minutes = "active_minutes"
    calories_burned = "calories_burned"


class MetricSource(str, enum.Enum):
    google_fit = "google_fit"
    manual = "manual"


class SyncJobType(str, enum.Enum):
    google_fit_sync = "google_fit_sync"
    document_processing = "document_processing"


class SyncJobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    complete = "complete"
    failed = "failed"


# ── Models ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=text("NOW()"))
    display_name = Column(String(100), nullable=True)
    google_oauth_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_token_expiry = Column(DateTime(timezone=True), nullable=True)
    settings_json = Column(JSONB, default={})

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    test_results = relationship("TestResult", back_populates="user", cascade="all, delete-orphan")
    health_metrics = relationship("HealthMetric", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=text("NOW()"))
    original_filename = Column(String(255))
    file_hash = Column(String(64), nullable=False)
    file_path = Column(Text, nullable=True)
    raw_ocr_text = Column(Text, nullable=True)
    llm_json_payload = Column(JSONB, nullable=True)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.pending)
    processing_error = Column(Text, nullable=True)
    lab_name = Column(String(200), nullable=True)
    report_date = Column(Date, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="documents")
    test_results = relationship("TestResult", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_documents_user_id", "user_id"),
        Index("ix_documents_file_hash", "user_id", "file_hash"),
        Index("ix_documents_status", "processing_status"),
    )


class Biomarker(Base):
    __tablename__ = "biomarkers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loinc_code = Column(String(20), unique=True, nullable=False)
    standard_name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=False)
    category = Column(Enum(BiomarkerCategory), nullable=False)
    standard_unit = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    aliases = Column(ARRAY(Text), default=[])

    test_results = relationship("TestResult", back_populates="biomarker")
    recommendations = relationship("Recommendation", back_populates="biomarker")

    __table_args__ = (
        Index("ix_biomarkers_loinc", "loinc_code"),
        Index("ix_biomarkers_category", "category"),
    )


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    biomarker_id = Column(UUID(as_uuid=True), ForeignKey("biomarkers.id"), nullable=False)
    result_date = Column(Date, nullable=False)
    value = Column(Float(precision=12), nullable=False)
    raw_value = Column(Float(precision=12), nullable=True)
    raw_unit = Column(String(50), nullable=True)
    standard_unit = Column(String(50), nullable=True)
    ref_range_low = Column(Float(precision=12), nullable=True)
    ref_range_high = Column(Float(precision=12), nullable=True)
    ref_range_text = Column(String(100), nullable=True)
    is_out_of_range = Column(Boolean, default=False)
    out_of_range_direction = Column(Enum(OutOfRangeDirection), default=OutOfRangeDirection.normal)
    lab_ref_range_low = Column(Float(precision=12), nullable=True)
    lab_ref_range_high = Column(Float(precision=12), nullable=True)
    notes = Column(Text, nullable=True)

    document = relationship("Document", back_populates="test_results")
    user = relationship("User", back_populates="test_results")
    biomarker = relationship("Biomarker", back_populates="test_results")
    recommendations = relationship("Recommendation", back_populates="test_result")

    __table_args__ = (
        UniqueConstraint("user_id", "biomarker_id", "result_date", "document_id", name="uq_test_result"),
        Index("ix_results_user", "user_id"),
        Index("ix_results_biomarker", "biomarker_id"),
        Index("ix_results_date", "result_date"),
        Index("ix_results_out_of_range", "is_out_of_range"),
    )


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    metric_type = Column(Enum(MetricType), nullable=False)
    value = Column(Float(precision=12), nullable=False)
    source = Column(Enum(MetricSource), nullable=False)

    user = relationship("User", back_populates="health_metrics")

    __table_args__ = (
        UniqueConstraint("user_id", "date", "metric_type", name="uq_health_metric"),
        Index("ix_metrics_user_date_type", "user_id", "date", "metric_type"),
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    biomarker_id = Column(UUID(as_uuid=True), ForeignKey("biomarkers.id"), nullable=False)
    test_result_id = Column(UUID(as_uuid=True), ForeignKey("test_results.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    rag_context_used = Column(ARRAY(Text), default=[])
    recommendation_text = Column(Text)
    is_dismissed = Column(Boolean, default=False)

    user = relationship("User", back_populates="recommendations")
    biomarker = relationship("Biomarker", back_populates="recommendations")
    test_result = relationship("TestResult", back_populates="recommendations")

    __table_args__ = (
        Index("ix_recommendations_user", "user_id"),
        Index("ix_recommendations_biomarker", "biomarker_id"),
    )


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_type = Column(Enum(SyncJobType), nullable=False)
    celery_task_id = Column(String(255), nullable=True)
    status = Column(Enum(SyncJobStatus), default=SyncJobStatus.queued)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    records_synced = Column(Integer, default=0)

    user = relationship("User", back_populates="sync_jobs")
