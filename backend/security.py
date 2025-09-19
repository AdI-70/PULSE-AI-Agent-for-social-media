"""
Security module for Pulse application
"""

import jwt
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import structlog

logger = structlog.get_logger()


class SecurityManager:
    """Security manager for handling authentication, encryption, and other security features."""
    
    def __init__(self, secret_key: str, encryption_key: Optional[str] = None):
        self.secret_key = secret_key
        self.encryption_key = encryption_key or os.getenv("ENCRYPTION_KEY")
        if self.encryption_key:
            self.cipher_suite = Fernet(self.encryption_key.encode())
    
    def generate_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generate a JWT token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token and return the payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.PyJWTError as e:
            logger.error("Token verification failed", error=str(e))
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.hash_password(plain_password) == hashed_password
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data."""
        if not self.encryption_key:
            logger.warning("Encryption key not configured")
            return None
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error("Data encryption failed", error=str(e))
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data."""
        if not self.encryption_key:
            logger.warning("Encryption key not configured")
            return None
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error("Data decryption failed", error=str(e))
            return None
    
    def mask_sensitive_data(self, data: str, show_last: int = 4) -> str:
        """Mask sensitive data for logging/display."""
        if len(data) <= show_last:
            return "*" * len(data)
        return "*" * (len(data) - show_last) + data[-show_last:]


class RateLimiter:
    """Rate limiter to prevent abuse and protect against DoS attacks."""
    
    def __init__(self, redis_client, max_requests: int = 100, window_seconds: int = 3600):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed based on rate limiting."""
        try:
            current = self.redis.get(key)
            if current is None:
                self.redis.setex(key, self.window_seconds, 1)
                return True
            elif int(current) < self.max_requests:
                self.redis.incr(key)
                return True
            else:
                return False
        except Exception as e:
            logger.error("Rate limiting check failed", error=str(e))
            # Fail open to avoid blocking legitimate requests during Redis issues
            return True
    
    def get_retry_after(self, key: str) -> int:
        """Get the time in seconds until the rate limit resets."""
        try:
            ttl = self.redis.ttl(key)
            return max(0, ttl)
        except Exception as e:
            logger.error("Failed to get rate limit TTL", error=str(e))
            return 0


# Global security manager instance
security_manager = None


def init_security_manager(secret_key: str, encryption_key: Optional[str] = None):
    """Initialize the global security manager."""
    global security_manager
    security_manager = SecurityManager(secret_key, encryption_key)


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    if security_manager is None:
        raise RuntimeError("Security manager not initialized")
    return security_manager