"""
Utilidades para PKCE (Proof Key for Code Exchange)
"""
import secrets
import hashlib
import base64
from typing import Tuple

def generate_pkce_pair() -> Tuple[str, str]:
    """
    Generar code_verifier y code_challenge para PKCE
    
    Returns:
        Tuple[str, str]: (code_verifier, code_challenge)
    """
    # Generar code_verifier (43-128 caracteres, URL-safe)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Generar code_challenge (SHA256 hash del code_verifier)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

def generate_state() -> str:
    """
    Generar state parameter para OAuth (protección CSRF)
    
    Returns:
        str: State parameter aleatorio
    """
    return secrets.token_urlsafe(32)

def generate_nonce() -> str:
    """
    Generar nonce parameter para OAuth (protección replay)
    
    Returns:
        str: Nonce parameter aleatorio
    """
    return secrets.token_urlsafe(32)
