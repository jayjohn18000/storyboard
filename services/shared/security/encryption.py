"""Encryption utilities for evidence and sensitive data.

Implements envelope encryption for evidence, AES-256 for data at rest,
key rotation, field-level encryption for PII, and encryption audit trails.
"""

import os
import json
import hashlib
import secrets
import base64
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class EncryptionKey:
    """Represents an encryption key with metadata."""
    
    def __init__(self, key_id: str, key_data: bytes, algorithm: str = "AES-256", 
                 created_at: Optional[datetime] = None, expires_at: Optional[datetime] = None):
        self.key_id = key_id
        self.key_data = key_data
        self.algorithm = algorithm
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at
        self.version = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert key to dictionary for storage."""
        return {
            "key_id": self.key_id,
            "key_data": base64.b64encode(self.key_data).decode('utf-8'),
            "algorithm": self.algorithm,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EncryptionKey':
        """Create key from dictionary."""
        key = cls(
            key_id=data["key_id"],
            key_data=base64.b64decode(data["key_data"]),
            algorithm=data["algorithm"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None
        )
        key.version = data.get("version", 1)
        return key
    
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class EnvelopeEncryption:
    """Implements envelope encryption for evidence files."""
    
    def __init__(self, master_key: bytes, key_rotation_days: int = 90):
        self.master_key = master_key
        self.key_rotation_days = key_rotation_days
        self.data_keys: Dict[str, EncryptionKey] = {}
        self.audit_trail: List[Dict[str, Any]] = []
    
    def generate_data_key(self, key_id: Optional[str] = None) -> EncryptionKey:
        """Generate a new data encryption key."""
        if not key_id:
            key_id = f"dek_{secrets.token_hex(16)}"
        
        # Generate random 256-bit key
        key_data = secrets.token_bytes(32)
        
        # Set expiration date
        expires_at = datetime.utcnow() + timedelta(days=self.key_rotation_days)
        
        key = EncryptionKey(
            key_id=key_id,
            key_data=key_data,
            algorithm="AES-256",
            expires_at=expires_at
        )
        
        self.data_keys[key_id] = key
        
        # Log key generation
        self._log_encryption_event("key_generated", {
            "key_id": key_id,
            "algorithm": "AES-256",
            "expires_at": expires_at.isoformat()
        })
        
        return key
    
    def encrypt_data_key(self, data_key: EncryptionKey) -> Tuple[bytes, str]:
        """Encrypt a data key with the master key."""
        # Use AES-GCM for encrypting the data key
        iv = secrets.token_bytes(12)  # 96-bit IV for GCM
        cipher = Cipher(algorithms.AES(self.master_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Encrypt the data key
        encrypted_key = encryptor.update(data_key.key_data) + encryptor.finalize()
        
        # Combine IV, encrypted key, and tag
        encrypted_data_key = iv + encrypted_key + encryptor.tag
        
        return encrypted_data_key, data_key.key_id
    
    def decrypt_data_key(self, encrypted_data_key: bytes, key_id: str) -> EncryptionKey:
        """Decrypt a data key with the master key."""
        if len(encrypted_data_key) < 28:  # 12 (IV) + 16 (tag) = 28 bytes minimum
            raise ValueError("Invalid encrypted data key format")
        
        # Extract IV, encrypted key, and tag
        iv = encrypted_data_key[:12]
        tag = encrypted_data_key[-16:]
        encrypted_key = encrypted_data_key[12:-16]
        
        # Decrypt the data key
        cipher = Cipher(algorithms.AES(self.master_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        
        try:
            key_data = decryptor.update(encrypted_key) + decryptor.finalize()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data key: {e}")
        
        # Create encryption key object
        key = EncryptionKey(key_id=key_id, key_data=key_data, algorithm="AES-256")
        
        # Log decryption event
        self._log_encryption_event("key_decrypted", {"key_id": key_id})
        
        return key
    
    def encrypt_evidence(self, evidence_data: bytes, key_id: Optional[str] = None) -> Tuple[bytes, str]:
        """Encrypt evidence data using envelope encryption."""
        # Generate or retrieve data key
        if key_id and key_id in self.data_keys:
            data_key = self.data_keys[key_id]
        else:
            data_key = self.generate_data_key(key_id)
        
        # Encrypt the evidence data
        iv = secrets.token_bytes(16)  # 128-bit IV for CBC
        cipher = Cipher(algorithms.AES(data_key.key_data), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad the data to block size
        padded_data = self._pad_data(evidence_data)
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Encrypt the data key
        encrypted_data_key, _ = self.encrypt_data_key(data_key)
        
        # Combine encrypted data key and encrypted evidence
        envelope = encrypted_data_key + iv + encrypted_data
        
        # Log encryption event
        self._log_encryption_event("evidence_encrypted", {
            "key_id": data_key.key_id,
            "data_size": len(evidence_data),
            "algorithm": "AES-256-CBC"
        })
        
        return envelope, data_key.key_id
    
    def decrypt_evidence(self, encrypted_envelope: bytes, key_id: str) -> bytes:
        """Decrypt evidence data using envelope encryption."""
        if len(encrypted_envelope) < 60:  # Minimum size for envelope
            raise ValueError("Invalid encrypted envelope format")
        
        # Extract components
        encrypted_data_key = encrypted_envelope[:44]  # 12 (IV) + 32 (key) + 16 (tag)
        iv = encrypted_envelope[44:60]  # 16 bytes
        encrypted_data = encrypted_envelope[60:]
        
        # Decrypt the data key
        data_key = self.decrypt_data_key(encrypted_data_key, key_id)
        
        # Decrypt the evidence data
        cipher = Cipher(algorithms.AES(data_key.key_data), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        try:
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            evidence_data = self._unpad_data(padded_data)
        except Exception as e:
            raise ValueError(f"Failed to decrypt evidence data: {e}")
        
        # Log decryption event
        self._log_encryption_event("evidence_decrypted", {
            "key_id": key_id,
            "data_size": len(evidence_data)
        })
        
        return evidence_data
    
    def _pad_data(self, data: bytes) -> bytes:
        """PKCS7 padding for block cipher."""
        padding_length = 16 - (len(data) % 16)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad_data(self, padded_data: bytes) -> bytes:
        """Remove PKCS7 padding."""
        if len(padded_data) == 0:
            raise ValueError("Cannot unpad empty data")
        
        padding_length = padded_data[-1]
        if padding_length > 16 or padding_length == 0:
            raise ValueError("Invalid padding")
        
        return padded_data[:-padding_length]
    
    def rotate_keys(self) -> Dict[str, Any]:
        """Rotate encryption keys that are near expiration."""
        rotation_results = {
            "rotated_keys": [],
            "expired_keys": [],
            "errors": []
        }
        
        current_time = datetime.utcnow()
        rotation_threshold = timedelta(days=7)  # Rotate keys 7 days before expiration
        
        for key_id, key in list(self.data_keys.items()):
            try:
                if key.expires_at and (key.expires_at - current_time) < rotation_threshold:
                    # Generate new key
                    new_key = self.generate_data_key(f"{key_id}_rotated_{int(current_time.timestamp())}")
                    
                    # Mark old key for deprecation
                    key.expires_at = current_time - timedelta(days=1)
                    
                    rotation_results["rotated_keys"].append({
                        "old_key_id": key_id,
                        "new_key_id": new_key.key_id,
                        "rotated_at": current_time.isoformat()
                    })
                    
                    self._log_encryption_event("key_rotated", {
                        "old_key_id": key_id,
                        "new_key_id": new_key.key_id
                    })
                
                elif key.is_expired():
                    rotation_results["expired_keys"].append(key_id)
                    
            except Exception as e:
                rotation_results["errors"].append({
                    "key_id": key_id,
                    "error": str(e)
                })
        
        return rotation_results
    
    def _log_encryption_event(self, event_type: str, metadata: Dict[str, Any]):
        """Log encryption events for audit trail."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "metadata": metadata,
            "checksum": hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
        }
        
        self.audit_trail.append(event)
        logger.info(f"Encryption event: {event_type}", extra=event)


class FieldLevelEncryption:
    """Implements field-level encryption for PII data."""
    
    def __init__(self, encryption_service: EnvelopeEncryption):
        self.encryption_service = encryption_service
        self.pii_fields = {
            "ssn", "social_security_number", "tax_id", "ein",
            "phone", "email", "address", "date_of_birth",
            "driver_license", "passport_number", "credit_card"
        }
    
    def encrypt_pii_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt PII fields in a data structure."""
        encrypted_data = data.copy()
        
        for field, value in data.items():
            if self._is_pii_field(field) and isinstance(value, str):
                encrypted_value, key_id = self.encryption_service.encrypt_evidence(value.encode())
                
                # Store encrypted value with metadata
                encrypted_data[field] = {
                    "_encrypted": True,
                    "_key_id": key_id,
                    "_value": base64.b64encode(encrypted_value).decode('utf-8'),
                    "_algorithm": "AES-256"
                }
        
        return encrypted_data
    
    def decrypt_pii_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt PII fields in a data structure."""
        decrypted_data = encrypted_data.copy()
        
        for field, value in encrypted_data.items():
            if isinstance(value, dict) and value.get("_encrypted"):
                try:
                    encrypted_bytes = base64.b64decode(value["_value"])
                    key_id = value["_key_id"]
                    
                    decrypted_bytes = self.encryption_service.decrypt_evidence(encrypted_bytes, key_id)
                    decrypted_data[field] = decrypted_bytes.decode('utf-8')
                    
                except Exception as e:
                    logger.error(f"Failed to decrypt PII field {field}: {e}")
                    decrypted_data[field] = None  # Mark as failed to decrypt
        
        return decrypted_data
    
    def _is_pii_field(self, field_name: str) -> bool:
        """Check if a field name indicates PII data."""
        field_lower = field_name.lower()
        return any(pii_field in field_lower for pii_field in self.pii_fields)


class EncryptionAuditTrail:
    """Manages encryption audit trails for compliance."""
    
    def __init__(self, storage_backend):
        self.storage_backend = storage_backend
        self.audit_events: List[Dict[str, Any]] = []
    
    def log_encryption_event(self, event_type: str, metadata: Dict[str, Any], 
                           user_id: Optional[str] = None, case_id: Optional[str] = None):
        """Log an encryption event to the audit trail."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "case_id": case_id,
            "metadata": metadata,
            "checksum": hashlib.sha256(
                json.dumps(metadata, sort_keys=True).encode()
            ).hexdigest()
        }
        
        self.audit_events.append(event)
        
        # Store in persistent backend
        try:
            self.storage_backend.store_audit_event(event)
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
    
    def get_audit_trail(self, case_id: Optional[str] = None, 
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Retrieve audit trail events."""
        events = self.audit_events.copy()
        
        if case_id:
            events = [e for e in events if e.get("case_id") == case_id]
        
        if start_date:
            events = [e for e in events if datetime.fromisoformat(e["timestamp"]) >= start_date]
        
        if end_date:
            events = [e for e in events if datetime.fromisoformat(e["timestamp"]) <= end_date]
        
        return sorted(events, key=lambda x: x["timestamp"])
    
    def verify_audit_integrity(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Verify the integrity of the audit trail."""
        events = self.get_audit_trail(case_id)
        
        integrity_results = {
            "total_events": len(events),
            "verified_events": 0,
            "failed_verifications": [],
            "tampered_events": []
        }
        
        for event in events:
            try:
                # Recalculate checksum
                expected_checksum = hashlib.sha256(
                    json.dumps(event["metadata"], sort_keys=True).encode()
                ).hexdigest()
                
                if event["checksum"] == expected_checksum:
                    integrity_results["verified_events"] += 1
                else:
                    integrity_results["tampered_events"].append({
                        "timestamp": event["timestamp"],
                        "event_type": event["event_type"],
                        "expected_checksum": expected_checksum,
                        "actual_checksum": event["checksum"]
                    })
                    
            except Exception as e:
                integrity_results["failed_verifications"].append({
                    "timestamp": event["timestamp"],
                    "error": str(e)
                })
        
        return integrity_results


class EncryptionService:
    """Main encryption service that coordinates all encryption operations."""
    
    def __init__(self, master_key: bytes, storage_backend, key_rotation_days: int = 90):
        self.envelope_encryption = EnvelopeEncryption(master_key, key_rotation_days)
        self.field_encryption = FieldLevelEncryption(self.envelope_encryption)
        self.audit_trail = EncryptionAuditTrail(storage_backend)
        
        # Load existing keys
        self._load_existing_keys()
    
    def encrypt_evidence_file(self, file_data: bytes, case_id: str, 
                            user_id: str, evidence_id: str) -> Tuple[bytes, str]:
        """Encrypt an evidence file with full audit trail."""
        try:
            encrypted_data, key_id = self.envelope_encryption.encrypt_evidence(file_data)
            
            # Log encryption event
            self.audit_trail.log_encryption_event(
                event_type="evidence_file_encrypted",
                metadata={
                    "evidence_id": evidence_id,
                    "file_size": len(file_data),
                    "encrypted_size": len(encrypted_data),
                    "key_id": key_id,
                    "algorithm": "AES-256-CBC"
                },
                user_id=user_id,
                case_id=case_id
            )
            
            return encrypted_data, key_id
            
        except Exception as e:
            logger.error(f"Failed to encrypt evidence file {evidence_id}: {e}")
            raise
    
    def decrypt_evidence_file(self, encrypted_data: bytes, key_id: str,
                            case_id: str, user_id: str, evidence_id: str) -> bytes:
        """Decrypt an evidence file with full audit trail."""
        try:
            decrypted_data = self.envelope_encryption.decrypt_evidence(encrypted_data, key_id)
            
            # Log decryption event
            self.audit_trail.log_encryption_event(
                event_type="evidence_file_decrypted",
                metadata={
                    "evidence_id": evidence_id,
                    "encrypted_size": len(encrypted_data),
                    "decrypted_size": len(decrypted_data),
                    "key_id": key_id
                },
                user_id=user_id,
                case_id=case_id
            )
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to decrypt evidence file {evidence_id}: {e}")
            raise
    
    def encrypt_pii_fields(self, data: Dict[str, Any], case_id: str, 
                          user_id: str) -> Dict[str, Any]:
        """Encrypt PII fields in data with audit trail."""
        try:
            encrypted_data = self.field_encryption.encrypt_pii_data(data)
            
            # Log PII encryption event
            self.audit_trail.log_encryption_event(
                event_type="pii_fields_encrypted",
                metadata={
                    "fields_encrypted": list(data.keys()),
                    "data_size": len(json.dumps(data).encode())
                },
                user_id=user_id,
                case_id=case_id
            )
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Failed to encrypt PII fields: {e}")
            raise
    
    def decrypt_pii_fields(self, encrypted_data: Dict[str, Any], case_id: str,
                          user_id: str) -> Dict[str, Any]:
        """Decrypt PII fields in data with audit trail."""
        try:
            decrypted_data = self.field_encryption.decrypt_pii_data(encrypted_data)
            
            # Log PII decryption event
            self.audit_trail.log_encryption_event(
                event_type="pii_fields_decrypted",
                metadata={
                    "fields_decrypted": list(encrypted_data.keys())
                },
                user_id=user_id,
                case_id=case_id
            )
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to decrypt PII fields: {e}")
            raise
    
    def rotate_encryption_keys(self) -> Dict[str, Any]:
        """Rotate encryption keys and log the process."""
        try:
            rotation_results = self.envelope_encryption.rotate_keys()
            
            # Log key rotation event
            self.audit_trail.log_encryption_event(
                event_type="key_rotation_completed",
                metadata=rotation_results
            )
            
            return rotation_results
            
        except Exception as e:
            logger.error(f"Failed to rotate encryption keys: {e}")
            raise
    
    def get_encryption_audit_trail(self, case_id: Optional[str] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get encryption audit trail for compliance reporting."""
        return self.audit_trail.get_audit_trail(case_id, start_date, end_date)
    
    def verify_encryption_integrity(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Verify encryption audit trail integrity."""
        return self.audit_trail.verify_audit_integrity(case_id)
    
    def _load_existing_keys(self):
        """Load existing encryption keys from storage."""
        # This would load keys from persistent storage
        # For now, we'll start with an empty key store
        pass
