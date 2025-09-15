"""Cryptographic utilities for evidence integrity and signing."""

import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional
from datetime import datetime
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64


class CryptoUtils:
    """Utility class for cryptographic operations."""
    
    @staticmethod
    def generate_checksum(data: bytes, algorithm: str = "sha256") -> str:
        """Generate checksum for data."""
        if algorithm == "sha256":
            hash_obj = hashlib.sha256()
        elif algorithm == "sha512":
            hash_obj = hashlib.sha512()
        elif algorithm == "md5":
            hash_obj = hashlib.md5()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        hash_obj.update(data)
        return hash_obj.hexdigest()
    
    @staticmethod
    def verify_checksum(data: bytes, expected_checksum: str, algorithm: str = "sha256") -> bool:
        """Verify data against expected checksum."""
        actual_checksum = CryptoUtils.generate_checksum(data, algorithm)
        return hmac.compare_digest(actual_checksum, expected_checksum)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_key_pair() -> tuple[bytes, bytes]:
        """Generate RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        public_key = private_key.public_key()
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    @staticmethod
    def sign_data(data: bytes, private_key_pem: bytes) -> str:
        """Sign data with private key."""
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )
        
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')
    
    @staticmethod
    def verify_signature(data: bytes, signature: str, public_key_pem: bytes) -> bool:
        """Verify signature with public key."""
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=default_backend()
            )
            
            signature_bytes = base64.b64decode(signature)
            
            public_key.verify(
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
    
    @staticmethod
    def encrypt_data(data: bytes, password: str) -> Dict[str, str]:
        """Encrypt data with password."""
        # Generate random salt
        salt = secrets.token_bytes(16)
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        
        # Generate random IV
        iv = secrets.token_bytes(16)
        
        # Encrypt data
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad data to block size
        padded_data = CryptoUtils._pad_data(data, 16)
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return {
            "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8'),
            "salt": base64.b64encode(salt).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
        }
    
    @staticmethod
    def decrypt_data(encrypted_data: Dict[str, str], password: str) -> bytes:
        """Decrypt data with password."""
        # Decode base64 data
        encrypted_bytes = base64.b64decode(encrypted_data["encrypted_data"])
        salt = base64.b64decode(encrypted_data["salt"])
        iv = base64.b64decode(encrypted_data["iv"])
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        
        # Decrypt data
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        decrypted_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        # Remove padding
        return CryptoUtils._unpad_data(decrypted_data)
    
    @staticmethod
    def _pad_data(data: bytes, block_size: int) -> bytes:
        """Pad data to block size."""
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    @staticmethod
    def _unpad_data(data: bytes) -> bytes:
        """Remove padding from data."""
        padding_length = data[-1]
        return data[:-padding_length]
    
    @staticmethod
    def create_evidence_hash(evidence_data: Dict[str, Any]) -> str:
        """Create deterministic hash for evidence data."""
        # Sort keys for deterministic hashing
        sorted_data = json.dumps(evidence_data, sort_keys=True, separators=(',', ':'))
        return CryptoUtils.generate_checksum(sorted_data.encode('utf-8'))
    
    @staticmethod
    def create_render_hash(render_data: Dict[str, Any]) -> str:
        """Create deterministic hash for render data."""
        # Include only deterministic fields
        deterministic_data = {
            "timeline_id": render_data.get("timeline_id"),
            "width": render_data.get("width"),
            "height": render_data.get("height"),
            "fps": render_data.get("fps"),
            "quality": render_data.get("quality"),
            "profile": render_data.get("profile"),
            "seed": render_data.get("seed"),
            "deterministic": render_data.get("deterministic"),
        }
        
        return CryptoUtils.create_evidence_hash(deterministic_data)
