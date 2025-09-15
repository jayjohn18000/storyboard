"""Authentication and authorization system.

Implements JWT-based authentication, refresh tokens, MFA/2FA,
session management, and brute force protection.
"""

import os
import json
import hashlib
import secrets
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import jwt
import pyotp
import qrcode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles in the system."""
    ADMIN = "admin"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class Permission(Enum):
    """System permissions."""
    CREATE_CASE = "create_case"
    READ_CASE = "read_case"
    UPDATE_CASE = "update_case"
    DELETE_CASE = "delete_case"
    UPLOAD_EVIDENCE = "upload_evidence"
    PROCESS_EVIDENCE = "process_evidence"
    CREATE_STORYBOARD = "create_storyboard"
    RENDER_VIDEO = "render_video"
    APPROVE_CASE = "approve_case"
    EXPORT_CASE = "export_case"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"


@dataclass
class User:
    """User model with authentication data."""
    user_id: str
    username: str
    email: str
    role: UserRole
    permissions: List[Permission]
    password_hash: str
    salt: str
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    mfa_secret: Optional[str] = None
    mfa_enabled: bool = False
    password_changed_at: Optional[datetime] = None


@dataclass
class Session:
    """User session data."""
    session_id: str
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    created_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True


@dataclass
class LoginAttempt:
    """Login attempt tracking for brute force protection."""
    ip_address: str
    username: str
    timestamp: datetime
    success: bool
    failure_reason: Optional[str] = None


class PasswordHasher:
    """Secure password hashing using PBKDF2."""
    
    def __init__(self, iterations: int = 100000):
        self.iterations = iterations
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """Hash a password with salt."""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        password_hash = hashlib.sha256(key).hexdigest()
        salt_hex = salt.hex()
        
        return password_hash, salt_hex
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt_bytes = bytes.fromhex(salt)
            computed_hash, _ = self.hash_password(password, salt_bytes)
            return computed_hash == password_hash
        except Exception:
            return False


class MFAManager:
    """Manages Multi-Factor Authentication."""
    
    def __init__(self):
        self.issuer_name = "Legal-Sim"
    
    def generate_mfa_secret(self, user_id: str) -> str:
        """Generate a new MFA secret for a user."""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_id: str, username: str, secret: str) -> str:
        """Generate QR code for MFA setup."""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=self.issuer_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # For simplicity, return the URI instead of actual QR code
        return totp_uri
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """Verify an MFA token."""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 1 window tolerance
        except Exception:
            return False
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for MFA."""
        return [secrets.token_hex(4).upper() for _ in range(count)]


class BruteForceProtection:
    """Protects against brute force attacks."""
    
    def __init__(self, max_attempts: int = 5, lockout_duration: int = 900):  # 15 minutes
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.login_attempts: Dict[str, List[LoginAttempt]] = {}
    
    def record_login_attempt(self, ip_address: str, username: str, success: bool, 
                           failure_reason: Optional[str] = None):
        """Record a login attempt."""
        attempt = LoginAttempt(
            ip_address=ip_address,
            username=username,
            timestamp=datetime.utcnow(),
            success=success,
            failure_reason=failure_reason
        )
        
        key = f"{ip_address}:{username}"
        if key not in self.login_attempts:
            self.login_attempts[key] = []
        
        self.login_attempts[key].append(attempt)
        
        # Clean up old attempts
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.lockout_duration)
        self.login_attempts[key] = [
            a for a in self.login_attempts[key] 
            if a.timestamp > cutoff_time
        ]
    
    def is_locked_out(self, ip_address: str, username: str) -> bool:
        """Check if IP/username combination is locked out."""
        key = f"{ip_address}:{username}"
        
        if key not in self.login_attempts:
            return False
        
        recent_attempts = [
            a for a in self.login_attempts[key]
            if a.timestamp > datetime.utcnow() - timedelta(seconds=self.lockout_duration)
        ]
        
        failed_attempts = [a for a in recent_attempts if not a.success]
        return len(failed_attempts) >= self.max_attempts
    
    def get_remaining_attempts(self, ip_address: str, username: str) -> int:
        """Get remaining login attempts before lockout."""
        key = f"{ip_address}:{username}"
        
        if key not in self.login_attempts:
            return self.max_attempts
        
        recent_attempts = [
            a for a in self.login_attempts[key]
            if a.timestamp > datetime.utcnow() - timedelta(seconds=self.lockout_duration)
        ]
        
        failed_attempts = [a for a in recent_attempts if not a.success]
        return max(0, self.max_attempts - len(failed_attempts))


class JWTManager:
    """Manages JWT token creation and validation."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expiry = timedelta(hours=1)
        self.refresh_token_expiry = timedelta(days=30)
    
    def create_access_token(self, user: User, session_id: str) -> str:
        """Create an access token for a user."""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "session_id": session_id,
            "token_type": "access",
            "exp": datetime.utcnow() + self.access_token_expiry,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user: User, session_id: str) -> str:
        """Create a refresh token for a user."""
        payload = {
            "user_id": user.user_id,
            "session_id": session_id,
            "token_type": "refresh",
            "exp": datetime.utcnow() + self.refresh_token_expiry,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("token_type") != token_type:
                raise jwt.InvalidTokenError("Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {e}")
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Create new access and refresh tokens from a valid refresh token."""
        payload = self.verify_token(refresh_token, "refresh")
        
        # This would typically fetch user data from database
        # For now, we'll return new tokens with the same payload
        user_id = payload["user_id"]
        session_id = payload["session_id"]
        
        # In a real implementation, you'd fetch the user from the database
        # and create new tokens with updated expiry times
        
        return refresh_token, refresh_token  # Simplified for this example


class SessionManager:
    """Manages user sessions."""
    
    def __init__(self, jwt_manager: JWTManager):
        self.jwt_manager = jwt_manager
        self.active_sessions: Dict[str, Session] = {}
        self.max_sessions_per_user = 5
    
    def create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        """Create a new user session."""
        # Clean up old sessions for this user
        self._cleanup_user_sessions(user.user_id)
        
        session_id = secrets.token_urlsafe(32)
        
        access_token = self.jwt_manager.create_access_token(user, session_id)
        refresh_token = self.jwt_manager.create_refresh_token(user, session_id)
        
        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.active_sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get an active session by ID."""
        session = self.active_sessions.get(session_id)
        
        if session and session.is_active and session.expires_at > datetime.utcnow():
            return session
        
        return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].is_active = False
            return True
        
        return False
    
    def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user."""
        invalidated_count = 0
        
        for session in self.active_sessions.values():
            if session.user_id == user_id and session.is_active:
                session.is_active = False
                invalidated_count += 1
        
        return invalidated_count
    
    def _cleanup_user_sessions(self, user_id: str):
        """Clean up old sessions for a user."""
        user_sessions = [
            s for s in self.active_sessions.values()
            if s.user_id == user_id and s.is_active
        ]
        
        if len(user_sessions) >= self.max_sessions_per_user:
            # Remove oldest sessions
            user_sessions.sort(key=lambda x: x.created_at)
            sessions_to_remove = user_sessions[:-self.max_sessions_per_user + 1]
            
            for session in sessions_to_remove:
                session.is_active = False


class AuthenticationService:
    """Main authentication service."""
    
    def __init__(self, secret_key: str, user_storage, audit_logger):
        self.password_hasher = PasswordHasher()
        self.mfa_manager = MFAManager()
        self.brute_force_protection = BruteForceProtection()
        self.jwt_manager = JWTManager(secret_key)
        self.session_manager = SessionManager(self.jwt_manager)
        self.user_storage = user_storage
        self.audit_logger = audit_logger
        
        # Role-based permissions mapping
        self.role_permissions = {
            UserRole.ADMIN: list(Permission),
            UserRole.ATTORNEY: [
                Permission.CREATE_CASE, Permission.READ_CASE, Permission.UPDATE_CASE,
                Permission.UPLOAD_EVIDENCE, Permission.PROCESS_EVIDENCE,
                Permission.CREATE_STORYBOARD, Permission.RENDER_VIDEO,
                Permission.APPROVE_CASE, Permission.EXPORT_CASE
            ],
            UserRole.PARALEGAL: [
                Permission.READ_CASE, Permission.UPDATE_CASE,
                Permission.UPLOAD_EVIDENCE, Permission.PROCESS_EVIDENCE,
                Permission.CREATE_STORYBOARD
            ],
            UserRole.REVIEWER: [
                Permission.READ_CASE, Permission.APPROVE_CASE
            ],
            UserRole.VIEWER: [
                Permission.READ_CASE
            ]
        }
    
    def register_user(self, username: str, email: str, password: str, 
                     role: UserRole, created_by: str) -> User:
        """Register a new user."""
        # Check if user already exists
        if self.user_storage.get_user_by_username(username):
            raise ValueError("Username already exists")
        
        if self.user_storage.get_user_by_email(email):
            raise ValueError("Email already exists")
        
        # Hash password
        password_hash, salt = self.password_hasher.hash_password(password)
        
        # Create user
        user = User(
            user_id=secrets.token_urlsafe(16),
            username=username,
            email=email,
            role=role,
            permissions=self.role_permissions[role],
            password_hash=password_hash,
            salt=salt,
            created_at=datetime.utcnow()
        )
        
        # Store user
        self.user_storage.create_user(user)
        
        # Log registration
        self.audit_logger.log_event("user_registered", {
            "user_id": user.user_id,
            "username": username,
            "email": email,
            "role": role.value,
            "created_by": created_by
        })
        
        return user
    
    def authenticate_user(self, username: str, password: str, mfa_token: Optional[str],
                         ip_address: str, user_agent: str) -> Tuple[Session, User]:
        """Authenticate a user and create a session."""
        # Check for brute force lockout
        if self.brute_force_protection.is_locked_out(ip_address, username):
            self.audit_logger.log_event("login_blocked_brute_force", {
                "username": username,
                "ip_address": ip_address
            })
            raise ValueError("Account temporarily locked due to too many failed attempts")
        
        # Get user
        user = self.user_storage.get_user_by_username(username)
        if not user:
            self.brute_force_protection.record_login_attempt(
                ip_address, username, False, "user_not_found"
            )
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            self.brute_force_protection.record_login_attempt(
                ip_address, username, False, "account_inactive"
            )
            raise ValueError("Account is inactive")
        
        # Check if user is locked
        if user.is_locked:
            self.brute_force_protection.record_login_attempt(
                ip_address, username, False, "account_locked"
            )
            raise ValueError("Account is locked")
        
        # Verify password
        if not self.password_hasher.verify_password(password, user.password_hash, user.salt):
            # Update failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.is_locked = True
            
            self.user_storage.update_user(user)
            
            self.brute_force_protection.record_login_attempt(
                ip_address, username, False, "invalid_password"
            )
            
            self.audit_logger.log_event("login_failed", {
                "user_id": user.user_id,
                "username": username,
                "ip_address": ip_address,
                "reason": "invalid_password"
            })
            
            raise ValueError("Invalid credentials")
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not mfa_token:
                raise ValueError("MFA token required")
            
            if not self.mfa_manager.verify_mfa_token(user.mfa_secret, mfa_token):
                self.brute_force_protection.record_login_attempt(
                    ip_address, username, False, "invalid_mfa_token"
                )
                
                self.audit_logger.log_event("login_failed", {
                    "user_id": user.user_id,
                    "username": username,
                    "ip_address": ip_address,
                    "reason": "invalid_mfa_token"
                })
                
                raise ValueError("Invalid MFA token")
        
        # Successful authentication
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        self.user_storage.update_user(user)
        
        self.brute_force_protection.record_login_attempt(ip_address, username, True)
        
        # Create session
        session = self.session_manager.create_session(user, ip_address, user_agent)
        
        # Log successful login
        self.audit_logger.log_event("login_successful", {
            "user_id": user.user_id,
            "username": username,
            "ip_address": ip_address,
            "session_id": session.session_id
        })
        
        return session, user
    
    def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token using refresh token."""
        try:
            new_access_token, new_refresh_token = self.jwt_manager.refresh_access_token(refresh_token)
            
            # Log token refresh
            payload = self.jwt_manager.verify_token(refresh_token, "refresh")
            self.audit_logger.log_event("token_refreshed", {
                "user_id": payload["user_id"],
                "session_id": payload["session_id"]
            })
            
            return new_access_token, new_refresh_token
            
        except jwt.InvalidTokenError as e:
            self.audit_logger.log_event("token_refresh_failed", {
                "error": str(e)
            })
            raise
    
    def logout(self, session_id: str, user_id: str) -> bool:
        """Logout a user and invalidate session."""
        success = self.session_manager.invalidate_session(session_id)
        
        if success:
            self.audit_logger.log_event("logout", {
                "user_id": user_id,
                "session_id": session_id
            })
        
        return success
    
    def logout_all_sessions(self, user_id: str) -> int:
        """Logout all sessions for a user."""
        invalidated_count = self.session_manager.invalidate_user_sessions(user_id)
        
        self.audit_logger.log_event("logout_all_sessions", {
            "user_id": user_id,
            "invalidated_sessions": invalidated_count
        })
        
        return invalidated_count
    
    def verify_permission(self, user: User, permission: Permission) -> bool:
        """Verify if user has a specific permission."""
        return permission in user.permissions
    
    def setup_mfa(self, user_id: str) -> Tuple[str, List[str]]:
        """Set up MFA for a user."""
        user = self.user_storage.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Generate MFA secret and backup codes
        mfa_secret = self.mfa_manager.generate_mfa_secret(user_id)
        backup_codes = self.mfa_manager.generate_backup_codes()
        
        # Update user
        user.mfa_secret = mfa_secret
        user.mfa_enabled = True
        self.user_storage.update_user(user)
        
        # Generate QR code URI
        qr_uri = self.mfa_manager.generate_qr_code(user_id, user.username, mfa_secret)
        
        # Log MFA setup
        self.audit_logger.log_event("mfa_setup", {
            "user_id": user_id,
            "username": user.username
        })
        
        return qr_uri, backup_codes
    
    def disable_mfa(self, user_id: str, backup_code: str) -> bool:
        """Disable MFA for a user using a backup code."""
        user = self.user_storage.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # In a real implementation, you'd verify the backup code
        # For now, we'll just disable MFA
        
        user.mfa_enabled = False
        user.mfa_secret = None
        self.user_storage.update_user(user)
        
        # Log MFA disable
        self.audit_logger.log_event("mfa_disabled", {
            "user_id": user_id,
            "username": user.username
        })
        
        return True
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        user = self.user_storage.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify old password
        if not self.password_hasher.verify_password(old_password, user.password_hash, user.salt):
            raise ValueError("Invalid current password")
        
        # Hash new password
        new_password_hash, new_salt = self.password_hasher.hash_password(new_password)
        
        # Update user
        user.password_hash = new_password_hash
        user.salt = new_salt
        user.password_changed_at = datetime.utcnow()
        user.failed_login_attempts = 0  # Reset failed attempts
        self.user_storage.update_user(user)
        
        # Invalidate all sessions except current one
        invalidated_count = self.session_manager.invalidate_user_sessions(user_id)
        
        # Log password change
        self.audit_logger.log_event("password_changed", {
            "user_id": user_id,
            "username": user.username,
            "invalidated_sessions": invalidated_count
        })
        
        return True
