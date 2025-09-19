"""Database models for the Legal Simulation Platform."""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Text, Integer, BigInteger, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(ENUM('admin', 'attorney', 'paralegal', 'viewer', name='user_role'), nullable=False, default='viewer')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    cases = relationship("Case", back_populates="creator")
    evidence = relationship("Evidence", back_populates="uploader")
    storyboards = relationship("Storyboard", back_populates="creator")
    renders = relationship("Render", back_populates="creator")
    export_jobs = relationship("ExportJob", back_populates="creator")


class Case(Base):
    """Case model."""
    __tablename__ = "cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    case_number = Column(String(100), unique=True)
    status = Column(ENUM('draft', 'active', 'archived', 'deleted', name='case_status'), default='draft')
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    case_metadata = Column(JSON, default={})
    
    # Relationships
    creator = relationship("User", back_populates="cases")
    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    storyboards = relationship("Storyboard", back_populates="case", cascade="all, delete-orphan")
    renders = relationship("Render", back_populates="case", cascade="all, delete-orphan")
    export_jobs = relationship("ExportJob", back_populates="case", cascade="all, delete-orphan")


class Evidence(Base):
    """Evidence model."""
    __tablename__ = "evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False)
    status = Column(ENUM('uploaded', 'processing', 'processed', 'failed', 'locked', name='evidence_status'), default='uploaded')
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    case_metadata = Column(JSON, default={})
    processing_results = Column(JSON, default={})
    
    # Relationships
    case = relationship("Case", back_populates="evidence")
    uploader = relationship("User", back_populates="evidence")


class Storyboard(Base):
    """Storyboard model."""
    __tablename__ = "storyboards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(ENUM('draft', 'validating', 'validated', 'compiling', 'compiled', 'failed', name='storyboard_status'), default='draft')
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    validated_at = Column(DateTime)
    compiled_at = Column(DateTime)
    case_metadata = Column(JSON, default={})
    scenes = Column(JSON, default=[])
    validation_result = Column(JSON, default={})
    timeline_id = Column(UUID(as_uuid=True))
    render_config = Column(JSON, default={})
    
    # Relationships
    case = relationship("Case", back_populates="storyboards")
    creator = relationship("User", back_populates="storyboards")
    renders = relationship("Render", back_populates="storyboard", cascade="all, delete-orphan")


class Render(Base):
    """Render model."""
    __tablename__ = "renders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    storyboard_id = Column(UUID(as_uuid=True), ForeignKey("storyboards.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(ENUM('queued', 'rendering', 'completed', 'failed', 'cancelled', name='render_status'), default='queued')
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    render_config = Column(JSON, default={})
    output_path = Column(String(500))
    file_size = Column(BigInteger)
    case_metadata = Column(JSON, default={})
    
    # Relationships
    case = relationship("Case", back_populates="renders")
    storyboard = relationship("Storyboard", back_populates="renders")
    creator = relationship("User", back_populates="renders")


class ExportJob(Base):
    """Export job model."""
    __tablename__ = "export_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    job_type = Column(String(50), nullable=False)
    status = Column(String(50), default='pending')
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    file_path = Column(String(500))
    file_size = Column(BigInteger)
    case_metadata = Column(JSON, default={})
    
    # Relationships
    case = relationship("Case", back_populates="export_jobs")
    creator = relationship("User", back_populates="export_jobs")


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSON, default={})
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


class ChainOfCustody(Base):
    """Chain of custody model."""
    __tablename__ = "chain_of_custody"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    action = Column(String(100), nullable=False)
    actor = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column("metadata", JSON, default={})
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    
    # Relationships
    evidence = relationship("Evidence")


class EvidenceLock(Base):
    """Evidence lock model for WORM compliance."""
    __tablename__ = "evidence_lock"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False, unique=True)
    immutable_at = Column(DateTime, nullable=False)
    locked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lock_reason = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    evidence = relationship("Evidence")
    locker = relationship("User")
