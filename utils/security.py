"""
Modulo per la gestione della sicurezza e della crittografia.
"""
import os
import secrets
import hashlib
import base64
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
from datetime import datetime, timedelta
from loguru import logger


class SecurityManager:
    """Classe per la gestione della sicurezza dell'applicazione."""
    
    def __init__(self, key_file: str = ".env/.secret_key"):
        """
        Inizializza il gestore della sicurezza.
        
        Args:
            key_file: Percorso del file per la chiave di crittografia
        """
        self.key_file = key_file
        self._encryption_key = self._load_or_create_key()
        self._jwt_secret = self._generate_jwt_secret()
    
    def _load_or_create_key(self) -> bytes:
        """
        Carica o crea una chiave di crittografia.
        
        Returns:
            Chiave di crittografia
        """
        # Assicura che la directory esista
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        
        try:
            # Tenta di caricare una chiave esistente
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                return key
        except Exception as e:
            logger.warning(f"Impossibile caricare la chiave esistente: {str(e)}")
        
        # Genera una nuova chiave
        key = Fernet.generate_key()
        
        try:
            # Salva la nuova chiave
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # Imposta permessi sicuri
            os.chmod(self.key_file, 0o600)
        except Exception as e:
            logger.error(f"Impossibile salvare la nuova chiave: {str(e)}")
        
        return key
    
    def _generate_jwt_secret(self) -> str:
        """
        Genera un segreto per JWT.
        
        Returns:
            Segreto JWT
        """
        return secrets.token_hex(32)
    
    def encrypt_data(self, data: str) -> str:
        """
        Crittografa dati sensibili.
        
        Args:
            data: Dati da crittografare
            
        Returns:
            Dati crittografati in formato base64
        """
        try:
            cipher = Fernet(self._encryption_key)
            encrypted_data = cipher.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Errore nella crittografia: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrittografa dati sensibili.
        
        Args:
            encrypted_data: Dati crittografati in formato base64
            
        Returns:
            Dati decrittografati
        """
        try:
            cipher = Fernet(self._encryption_key)
            decoded_data = base64.b64decode(encrypted_data)
            decrypted_data = cipher.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Errore nella decrittografia: {str(e)}")
            raise
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        """
        Crea un hash sicuro per una password con salt.
        
        Args:
            password: Password da proteggere
            salt: Salt opzionale
            
        Returns:
            Dizionario con hash e salt
        """
        # Genera salt se non fornito
        if salt is None:
            salt = os.urandom(16)
        
        # Crea l'hash della password
        password_bytes = password.encode('utf-8')
        hash_obj = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, 100000)
        
        # Converti in formati leggibili
        hash_str = base64.b64encode(hash_obj).decode('utf-8')
        salt_str = base64.b64encode(salt).decode('utf-8')
        
        return {
            'hash': hash_str,
            'salt': salt_str
        }
    
    def verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """
        Verifica una password contro l'hash memorizzato.
        
        Args:
            password: Password da verificare
            stored_hash: Hash memorizzato
            stored_salt: Salt memorizzato
            
        Returns:
            True se la password è corretta
        """
        # Decodifica salt
        salt = base64.b64decode(stored_salt)
        
        # Ricalcola l'hash
        password_hash = self.hash_password(password, salt)
        
        # Verifica
        return password_hash['hash'] == stored_hash
    
    def generate_token(self, user_id: str, expiry_hours: int = 24) -> str:
        """
        Genera un token JWT.
        
        Args:
            user_id: ID dell'utente
            expiry_hours: Validità in ore
            
        Returns:
            Token JWT
        """
        expiry = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        payload = {
            'user_id': user_id,
            'exp': expiry,
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self._jwt_secret, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica un token JWT.
        
        Args:
            token: Token da verificare
            
        Returns:
            Payload decodificato o None se non valido
        """
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning(f"Token scaduto: {token[:10]}...")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token non valido ({str(e)}): {token[:10]}...")
            return None


class RateLimiter:
    """Classe per il rate limiting delle richieste API."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        Inizializza il rate limiter.
        
        Args:
            max_requests: Numero massimo di richieste consentite
            time_window: Finestra temporale in secondi
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}  # client_id -> [(timestamp, count), ...]
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Verifica se una richiesta è consentita.
        
        Args:
            client_id: ID del client
            
        Returns:
            True se la richiesta è consentita
        """
        now = datetime.now().timestamp()
        
        # Rimuovi timestamp scaduti
        if client_id in self.requests:
            self.requests[client_id] = [
                (ts, count) for ts, count in self.requests[client_id] 
                if now - ts < self.time_window
            ]
        else:
            self.requests[client_id] = []
        
        # Calcola il numero totale di richieste nella finestra temporale
        total_requests = sum(count for _, count in self.requests[client_id])
        
        # Verifica se il limite è stato superato
        if total_requests >= self.max_requests:
            return False
        
        # Aggiorna il conteggio
        if self.requests[client_id] and now - self.requests[client_id][-1][0] < 1:
            # Aggiorna l'ultimo timestamp
            last_ts, count = self.requests[client_id][-1]
            self.requests[client_id][-1] = (last_ts, count + 1)
        else:
            # Aggiungi un nuovo timestamp
            self.requests[client_id].append((now, 1))
        
        return True
