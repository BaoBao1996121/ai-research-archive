"""Safe login implementation fixing security issues from buggy_user_service.py

Fixes applied:
- SQL injection: Use parameterized queries (?)
- Password security: Hash verification with hashlib.pbkdf2_hmac
- Input validation: Basic length/format checks
- Resource management: Use 'with' statement for DB connection
"""
import sqlite3
import hashlib
import secrets
from typing import Optional

DB_PATH = "users.db"
HASH_ITERATIONS = 100000
HASH_ALGORITHM = "sha256"


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Hash password using PBKDF2.
    
    Args:
        password: Plain text password to hash
        salt: Optional salt bytes. If None, generates new random salt.
    
    Returns:
        Tuple of (salt_bytes, hash_bytes)
    """
    if salt is None:
        salt = secrets.token_bytes(32)
    
    pwd_hash = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode('utf-8'),
        salt,
        HASH_ITERATIONS
    )
    return salt, pwd_hash


def verify_password(password: str, stored_salt: bytes, stored_hash: bytes) -> bool:
    """
    Verify password against stored salt and hash.
    
    Args:
        password: Plain text password to verify
        stored_salt: Salt bytes from storage
        stored_hash: Hash bytes from storage
    
    Returns:
        True if password matches, False otherwise
    """
    _, computed_hash = hash_password(password, stored_salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def login(username: str, password: str) -> Optional[int]:
    """
    Authenticate user and return user ID.
    
    Security measures:
    - Parameterized SQL query prevents injection
    - PBKDF2 hash verification (not plain text comparison)
    - Input validation for username and password
    - Proper DB resource cleanup with 'with' statement
    - Timing-safe hash comparison
    
    Args:
        username: User's username
        password: User's plain text password
    
    Returns:
        User ID (int) if authentication succeeds, None otherwise
    """
    # Input validation
    if not username or not isinstance(username, str) or len(username) > 255:
        return None
    if not password or not isinstance(password, str) or len(password) > 1024:
        return None
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            # Parameterized query (salt_hash stored as BLOB containing salt + hash)
            cur.execute(
                "SELECT id, pwd_salt, pwd_hash FROM users WHERE name = ?",
                (username,)
            )
            row = cur.fetchone()
        
        if row is None:
            return None
        
        user_id, salt, pwd_hash = row
        
        # Timing-safe hash comparison
        if verify_password(password, salt, pwd_hash):
            return user_id
        
        return None
    
    except sqlite3.Error:
        return None
