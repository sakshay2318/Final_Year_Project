from cryptography.fernet import Fernet
from config import SECURITY_KEYS
import base64

def get_key_for_level(level):
    """Retrieve the encryption key for the given security level."""
    if 0 <= level < len(SECURITY_KEYS):
        return SECURITY_KEYS[level].encode('utf-8')
    raise ValueError("Invalid security level")

def decrypt_data(encrypted_data, level):
    """Decrypt data based on the security level."""
    key = get_key_for_level(level)  # Retrieve the decryption key for the level
    fernet = Fernet(key)
    
    try:
        encrypted_data_bytes = base64.b64decode(encrypted_data)  # Base64 decode before decryption
        decrypted_data = fernet.decrypt(encrypted_data_bytes)  # Decrypt using Fernet
        return decrypted_data
    except Exception as e:
        print(f"Decryption failed: {e}")
        raise ValueError("Invalid or mismatched token: Decryption failed")
