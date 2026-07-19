import os
from cryptography.fernet import Fernet


class CredentialsEncryptor:
    def __init__(self):
        key = os.environ.get("CREDENTIALS_ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key().decode()
            os.environ["CREDENTIALS_ENCRYPTION_KEY"] = key
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()

    def mask(self, plaintext: str) -> str:
        if len(plaintext) <= 4:
            return "****"
        return plaintext[:2] + "****" + plaintext[-2:]


encryptor = CredentialsEncryptor()
