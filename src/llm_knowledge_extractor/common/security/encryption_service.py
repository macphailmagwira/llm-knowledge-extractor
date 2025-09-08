
import os
import base64
import logging
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Util.Padding import pad, unpad
from llm_knowledge_extractor.core.config import settings

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        self.algorithm = 'aes-256-cbc'
        
        # Get encryption key from environment, or use fallback
        secret_key = settings.ENCRYPTION_SECRET_KEY
        
        # Create a key that's exactly the right length for AES-256 (32 bytes)
        salt = b'salt'
        self.encryption_key = scrypt(
            secret_key.encode(),
            salt=salt,
            key_len=32,
            N=2**14,
            r=8,
            p=1
        )
        
        # Create a proper IV (16 bytes for AES)
        self.encryption_iv = bytearray(16)  # Initialize with zeros
        
        # If an IV is provided in env, use it
        encryption_iv_env = settings.ENCRYPTION_IV
        if encryption_iv_env:
            try:
                # If the IV is provided as hex (32 characters)
                if len(encryption_iv_env) == 32:
                    self.encryption_iv = bytes.fromhex(encryption_iv_env)
                # If the IV is provided as base64 (typically 24 characters)
                elif len(encryption_iv_env) == 24:
                    self.encryption_iv = base64.b64decode(encryption_iv_env)
                else:
                    logger.warning("Invalid ENCRYPTION_IV format. Using default IV instead.")
            except Exception as e:
                logger.warning(f"Failed to parse ENCRYPTION_IV: {e}. Using default IV instead.")
        else:
            logger.warning("No ENCRYPTION_IV provided. Using default IV instead.")
    
    def encrypt(self, text: str) -> str:
        """
        Encrypts a string using AES-256-CBC.
        
        Args:
            text: The plaintext string to encrypt
            
        Returns:
            Hex-encoded encrypted string
        """
        try:
            # Create cipher
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, self.encryption_iv)
            
            # Add padding and encrypt
            data_to_encrypt = text.encode('utf-8')
            padded_data = pad(data_to_encrypt, AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            
            # Return as hex
            return encrypted.hex()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypts a hex-encoded encrypted string using AES-256-CBC.
        
        Args:
            encrypted: Hex-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        try:
            # Create cipher
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, self.encryption_iv)
            
            # Convert from hex and decrypt
            encrypted_bytes = bytes.fromhex(encrypted)
            decrypted_padded = cipher.decrypt(encrypted_bytes)
            
            # Remove padding
            decrypted = unpad(decrypted_padded, AES.block_size)
            
            # Convert to string
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError(f"Decryption failed: {str(e)}")

# Singleton instance for reuse
encryption_service = EncryptionService()