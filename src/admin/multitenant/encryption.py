import hashlib
import os
import base64
from cryptography.fernet import Fernet


def _derive_key() -> bytes:
    """Derive a stable Fernet key from jwt_secret_key or CREDENTIALS_ENCRYPTION_KEY."""
    env_key = os.environ.get("CREDENTIALS_ENCRYPTION_KEY")
    if env_key:
        return env_key.encode() if isinstance(env_key, str) else env_key
    # Fallback: derive from jwt_secret_key (stable across restarts)
    from src.config import settings
    raw = settings.jwt_secret_key.encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(raw).digest())


class CredentialsEncryptor:
    def __init__(self):
        self._fernet = Fernet(_derive_key())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()

    def mask(self, plaintext: str) -> str:
        if len(plaintext) <= 4:
            return "****"
        return plaintext[:2] + "****" + plaintext[-2:]


encryptor = CredentialsEncryptor()
