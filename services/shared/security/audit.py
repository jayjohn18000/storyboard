"""Audit logging and compliance system.

Creates tamper-proof audit logging, implements log shipping to SIEM,
adds suspicious activity detection, creates compliance reports,
and implements legal hold functionality.
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    PASSWORD_CHANGE = "password_change"
    MFA_SETUP = "mfa_setup"
    MFA_DISABLE = "mfa_disable"
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    CASE_DELETED = "case_deleted"
    EVIDENCE_UPLOADED = "evidence_uploaded"
    EVIDENCE_PROCESSED = "evidence_processed"
    EVIDENCE_ACCESSED = "evidence_accessed"
    STORYBOARD_CREATED = "storyboard_created"
    STORYBOARD_UPDATED = "storyboard_updated"
    RENDER_STARTED = "render_started"
    RENDER_COMPLETED = "render_completed"
    EXPORT_CREATED = "export_created"
    DATA_ENCRYPTED = "data_encrypted"
    DATA_DECRYPTED = "data_decrypted"
    KEY_ROTATED = "key_rotated"
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SYSTEM_ERROR = "system_error"


class SeverityLevel(Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    case_id: Optional[str]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    severity: SeverityLevel
    checksum: str
    digital_signature: Optional[str] = None


@dataclass
class ComplianceRule:
    """Compliance rule definition."""
    rule_id: str
    name: str
    description: str
    event_types: List[AuditEventType]
    conditions: Dict[str, Any]
    severity: SeverityLevel
    enabled: bool = True


@dataclass
class LegalHold:
    """Legal hold configuration."""
    hold_id: str
    case_id: str
    description: str
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool = True
    affected_users: List[str] = None
    data_retention_override: bool = False


class DigitalSignature:
    """Creates and verifies digital signatures for audit logs."""
    
    def __init__(self, private_key_path: Optional[str] = None, public_key_path: Optional[str] = None):
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        
        if private_key_path and os.path.exists(private_key_path):
            self.private_key = self._load_private_key(private_key_path)
        else:
            self.private_key = self._generate_key_pair()
        
        if public_key_path and os.path.exists(public_key_path):
            self.public_key = self._load_public_key(public_key_path)
        else:
            self.public_key = self.private_key.public_key()
    
    def _generate_key_pair(self) -> rsa.RSAPrivateKey:
        """Generate a new RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return private_key
    
    def _load_private_key(self, key_path: str) -> rsa.RSAPrivateKey:
        """Load private key from file."""
        with open(key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    
    def _load_public_key(self, key_path: str) -> rsa.RSAPublicKey:
        """Load public key from file."""
        with open(key_path, 'rb') as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )
        return public_key
    
    def sign_data(self, data: bytes) -> str:
        """Sign data with private key."""
        signature = self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature.hex()
    
    def verify_signature(self, data: bytes, signature: str) -> bool:
        """Verify signature with public key."""
        try:
            signature_bytes = bytes.fromhex(signature)
            self.public_key.verify(
                signature_bytes,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False


class AuditLogger:
    """Main audit logging system."""
    
    def __init__(self, storage_backend, siem_backend=None, signature_service=None):
        self.storage_backend = storage_backend
        self.siem_backend = siem_backend
        self.signature_service = signature_service or DigitalSignature()
        self.compliance_rules: List[ComplianceRule] = []
        self.legal_holds: List[LegalHold] = []
        self.suspicious_activity_detector = SuspiciousActivityDetector()
        
        # Load compliance rules
        self._load_default_compliance_rules()
    
    def log_event(self, event_type: AuditEventType, details: Dict[str, Any],
                  user_id: Optional[str] = None, username: Optional[str] = None,
                  ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                  session_id: Optional[str] = None, case_id: Optional[str] = None,
                  resource_id: Optional[str] = None, severity: SeverityLevel = SeverityLevel.LOW) -> AuditEvent:
        """Log an audit event."""
        
        # Create event
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            case_id=case_id,
            resource_id=resource_id,
            action=details.get("action", ""),
            details=details,
            severity=severity,
            checksum=""
        )
        
        # Generate checksum
        event.checksum = self._generate_checksum(event)
        
        # Create digital signature
        if self.signature_service:
            event_data = self._serialize_event_for_signing(event)
            event.digital_signature = self.signature_service.sign_data(event_data)
        
        # Check for suspicious activity
        suspicious_score = self.suspicious_activity_detector.analyze_event(event)
        if suspicious_score > 0.7:  # High suspicion threshold
            self._handle_suspicious_activity(event, suspicious_score)
        
        # Check compliance rules
        self._check_compliance_rules(event)
        
        # Store event
        self.storage_backend.store_audit_event(event)
        
        # Send to SIEM if configured
        if self.siem_backend:
            self.siem_backend.send_event(event)
        
        # Log to application logger
        logger.info(f"Audit event logged: {event_type.value}", extra={
            "event_id": event.event_id,
            "user_id": user_id,
            "case_id": case_id,
            "severity": severity.value
        })
        
        return event
    
    def get_audit_trail(self, case_id: Optional[str] = None, user_id: Optional[str] = None,
                       start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                       event_types: Optional[List[AuditEventType]] = None) -> List[AuditEvent]:
        """Retrieve audit trail events."""
        return self.storage_backend.get_audit_events(
            case_id=case_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types
        )
    
    def verify_audit_integrity(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Verify the integrity of audit trail."""
        events = self.get_audit_trail(case_id=case_id)
        
        integrity_results = {
            "total_events": len(events),
            "verified_events": 0,
            "failed_verifications": [],
            "tampered_events": [],
            "missing_signatures": []
        }
        
        for event in events:
            try:
                # Verify checksum
                expected_checksum = self._generate_checksum(event)
                if event.checksum != expected_checksum:
                    integrity_results["tampered_events"].append({
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "expected_checksum": expected_checksum,
                        "actual_checksum": event.checksum
                    })
                    continue
                
                # Verify digital signature
                if not event.digital_signature:
                    integrity_results["missing_signatures"].append(event.event_id)
                    continue
                
                event_data = self._serialize_event_for_signing(event)
                if not self.signature_service.verify_signature(event_data, event.digital_signature):
                    integrity_results["tampered_events"].append({
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "reason": "invalid_signature"
                    })
                    continue
                
                integrity_results["verified_events"] += 1
                
            except Exception as e:
                integrity_results["failed_verifications"].append({
                    "event_id": event.event_id,
                    "error": str(e)
                })
        
        return integrity_results
    
    def create_legal_hold(self, case_id: str, description: str, created_by: str,
                         expires_at: Optional[datetime] = None,
                         affected_users: Optional[List[str]] = None) -> LegalHold:
        """Create a legal hold for a case."""
        legal_hold = LegalHold(
            hold_id=self._generate_hold_id(),
            case_id=case_id,
            description=description,
            created_by=created_by,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            affected_users=affected_users or []
        )
        
        self.legal_holds.append(legal_hold)
        
        # Log legal hold creation
        self.log_event(
            AuditEventType.SECURITY_VIOLATION,
            {
                "action": "legal_hold_created",
                "hold_id": legal_hold.hold_id,
                "case_id": case_id,
                "description": description,
                "expires_at": expires_at.isoformat() if expires_at else None
            },
            user_id=created_by,
            case_id=case_id,
            severity=SeverityLevel.HIGH
        )
        
        return legal_hold
    
    def is_legal_hold_active(self, case_id: str) -> bool:
        """Check if a legal hold is active for a case."""
        current_time = datetime.utcnow()
        
        for hold in self.legal_holds:
            if (hold.case_id == case_id and 
                hold.is_active and 
                (not hold.expires_at or hold.expires_at > current_time)):
                return True
        
        return False
    
    def generate_compliance_report(self, case_id: Optional[str] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate a compliance report."""
        events = self.get_audit_trail(case_id=case_id, start_date=start_date, end_date=end_date)
        
        report = {
            "report_id": self._generate_report_id(),
            "generated_at": datetime.utcnow().isoformat(),
            "case_id": case_id,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "summary": {
                "total_events": len(events),
                "events_by_type": {},
                "events_by_severity": {},
                "events_by_user": {},
                "unique_users": set(),
                "unique_cases": set()
            },
            "compliance_violations": [],
            "suspicious_activities": [],
            "data_integrity": self.verify_audit_integrity(case_id),
            "legal_holds": []
        }
        
        # Analyze events
        for event in events:
            # Count by type
            event_type = event.event_type.value
            report["summary"]["events_by_type"][event_type] = report["summary"]["events_by_type"].get(event_type, 0) + 1
            
            # Count by severity
            severity = event.severity.value
            report["summary"]["events_by_severity"][severity] = report["summary"]["events_by_severity"].get(severity, 0) + 1
            
            # Count by user
            if event.user_id:
                report["summary"]["events_by_user"][event.user_id] = report["summary"]["events_by_user"].get(event.user_id, 0) + 1
                report["summary"]["unique_users"].add(event.user_id)
            
            if event.case_id:
                report["summary"]["unique_cases"].add(event.case_id)
        
        # Convert sets to lists for JSON serialization
        report["summary"]["unique_users"] = list(report["summary"]["unique_users"])
        report["summary"]["unique_cases"] = list(report["summary"]["unique_cases"])
        
        # Check for legal holds
        if case_id:
            report["legal_holds"] = [
                {
                    "hold_id": hold.hold_id,
                    "description": hold.description,
                    "created_at": hold.created_at.isoformat(),
                    "expires_at": hold.expires_at.isoformat() if hold.expires_at else None,
                    "is_active": hold.is_active
                }
                for hold in self.legal_holds
                if hold.case_id == case_id
            ]
        
        return report
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = int(time.time() * 1000000)  # Microsecond precision
        random_part = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
        return f"audit_{timestamp}_{random_part}"
    
    def _generate_hold_id(self) -> str:
        """Generate unique legal hold ID."""
        timestamp = int(time.time() * 1000)
        random_part = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
        return f"hold_{timestamp}_{random_part}"
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID."""
        timestamp = int(time.time() * 1000)
        random_part = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
        return f"report_{timestamp}_{random_part}"
    
    def _generate_checksum(self, event: AuditEvent) -> str:
        """Generate checksum for event data."""
        # Create a copy without checksum and signature for hashing
        event_data = asdict(event)
        event_data.pop('checksum', None)
        event_data.pop('digital_signature', None)
        
        # Convert to JSON string and hash
        json_str = json.dumps(event_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _serialize_event_for_signing(self, event: AuditEvent) -> bytes:
        """Serialize event data for digital signing."""
        event_data = asdict(event)
        event_data.pop('digital_signature', None)
        json_str = json.dumps(event_data, sort_keys=True, default=str)
        return json_str.encode()
    
    def _check_compliance_rules(self, event: AuditEvent):
        """Check event against compliance rules."""
        for rule in self.compliance_rules:
            if not rule.enabled or event.event_type not in rule.event_types:
                continue
            
            # Check rule conditions
            if self._evaluate_rule_conditions(event, rule.conditions):
                # Log compliance violation
                self.log_event(
                    AuditEventType.SECURITY_VIOLATION,
                    {
                        "action": "compliance_violation",
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "violation_details": rule.description
                    },
                    user_id=event.user_id,
                    case_id=event.case_id,
                    severity=rule.severity
                )
    
    def _evaluate_rule_conditions(self, event: AuditEvent, conditions: Dict[str, Any]) -> bool:
        """Evaluate compliance rule conditions against an event."""
        # Simple condition evaluation - in a real system, this would be more sophisticated
        for field, expected_value in conditions.items():
            if hasattr(event, field):
                actual_value = getattr(event, field)
                if actual_value != expected_value:
                    return False
            elif field in event.details:
                if event.details[field] != expected_value:
                    return False
        
        return True
    
    def _handle_suspicious_activity(self, event: AuditEvent, suspicion_score: float):
        """Handle detected suspicious activity."""
        # Log suspicious activity event
        self.log_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            {
                "action": "suspicious_activity_detected",
                "original_event_type": event.event_type.value,
                "suspicion_score": suspicion_score,
                "details": event.details
            },
            user_id=event.user_id,
            case_id=event.case_id,
            severity=SeverityLevel.HIGH
        )
        
        # In a real system, you might:
        # - Send alerts to security team
        # - Temporarily lock user account
        # - Increase monitoring for the user
        # - Trigger additional authentication requirements
    
    def _load_default_compliance_rules(self):
        """Load default compliance rules."""
        default_rules = [
            ComplianceRule(
                rule_id="rule_001",
                name="Multiple Failed Login Attempts",
                description="User has multiple failed login attempts",
                event_types=[AuditEventType.USER_LOGIN],
                conditions={"action": "login_failed"},
                severity=SeverityLevel.MEDIUM
            ),
            ComplianceRule(
                rule_id="rule_002",
                name="Off-Hours Access",
                description="User accessing system outside business hours",
                event_types=[AuditEventType.USER_LOGIN],
                conditions={"action": "login_successful"},
                severity=SeverityLevel.LOW
            ),
            ComplianceRule(
                rule_id="rule_003",
                name="Bulk Data Export",
                description="Large amount of data being exported",
                event_types=[AuditEventType.EXPORT_CREATED],
                conditions={"export_size": "large"},
                severity=SeverityLevel.HIGH
            )
        ]
        
        self.compliance_rules.extend(default_rules)


class SuspiciousActivityDetector:
    """Detects suspicious activity patterns."""
    
    def __init__(self):
        self.user_activity_history: Dict[str, List[AuditEvent]] = {}
        self.ip_activity_history: Dict[str, List[AuditEvent]] = {}
    
    def analyze_event(self, event: AuditEvent) -> float:
        """Analyze event for suspicious patterns. Returns suspicion score 0-1."""
        suspicion_score = 0.0
        
        # Track user activity
        if event.user_id:
            if event.user_id not in self.user_activity_history:
                self.user_activity_history[event.user_id] = []
            self.user_activity_history[event.user_id].append(event)
            
            # Check for rapid succession of actions
            suspicion_score += self._check_rapid_actions(event.user_id)
            
            # Check for unusual access patterns
            suspicion_score += self._check_unusual_access(event)
        
        # Track IP activity
        if event.ip_address:
            if event.ip_address not in self.ip_activity_history:
                self.ip_activity_history[event.ip_address] = []
            self.ip_activity_history[event.ip_address].append(event)
            
            # Check for multiple users from same IP
            suspicion_score += self._check_multiple_users_same_ip(event.ip_address)
        
        # Check for high-privilege actions
        suspicion_score += self._check_high_privilege_actions(event)
        
        # Check for bulk operations
        suspicion_score += self._check_bulk_operations(event)
        
        return min(suspicion_score, 1.0)  # Cap at 1.0
    
    def _check_rapid_actions(self, user_id: str) -> float:
        """Check for rapid succession of actions."""
        if user_id not in self.user_activity_history:
            return 0.0
        
        recent_events = [
            e for e in self.user_activity_history[user_id]
            if (datetime.utcnow() - e.timestamp).total_seconds() < 300  # Last 5 minutes
        ]
        
        if len(recent_events) > 20:  # More than 20 actions in 5 minutes
            return 0.3
        
        return 0.0
    
    def _check_unusual_access(self, event: AuditEvent) -> float:
        """Check for unusual access patterns."""
        # Check for off-hours access (simplified)
        hour = event.timestamp.hour
        if hour < 6 or hour > 22:  # Outside 6 AM to 10 PM
            return 0.2
        
        return 0.0
    
    def _check_multiple_users_same_ip(self, ip_address: str) -> float:
        """Check for multiple users accessing from same IP."""
        if ip_address not in self.ip_activity_history:
            return 0.0
        
        recent_events = [
            e for e in self.ip_activity_history[ip_address]
            if (datetime.utcnow() - e.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        unique_users = set(e.user_id for e in recent_events if e.user_id)
        if len(unique_users) > 3:  # More than 3 different users from same IP
            return 0.4
        
        return 0.0
    
    def _check_high_privilege_actions(self, event: AuditEvent) -> float:
        """Check for high-privilege actions."""
        high_privilege_actions = [
            AuditEventType.CASE_DELETED,
            AuditEventType.ROLE_CHANGE,
            AuditEventType.PERMISSION_CHANGE,
            AuditEventType.EXPORT_CREATED
        ]
        
        if event.event_type in high_privilege_actions:
            return 0.2
        
        return 0.0
    
    def _check_bulk_operations(self, event: AuditEvent) -> float:
        """Check for bulk operations."""
        if event.event_type == AuditEventType.EVIDENCE_UPLOADED:
            file_count = event.details.get("file_count", 1)
            if file_count > 10:  # More than 10 files uploaded at once
                return 0.3
        
        return 0.0
