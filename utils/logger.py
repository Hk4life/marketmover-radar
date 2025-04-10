"""
Modulo per la configurazione avanzata del logging.
"""
import os
import sys
import logging
from datetime import datetime
import json
from typing import Dict, Any, Optional
from loguru import logger

from config import LOG_LEVEL


def setup_logging(log_dir: str = "logs"):
    """
    Configura il sistema di logging con rotazione dei file e formattazione.
    
    Args:
        log_dir: Directory per i file di log
    """
    # Crea directory di log se non esiste
    os.makedirs(log_dir, exist_ok=True)
    
    # Rimuovi gestori predefiniti
    logger.remove()
    
    # Aggiungi gestore per lo stdout con livello configurato
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Aggiungi gestore per i file con rotazione
    logger.add(
        os.path.join(log_dir, "marketmover_{time:YYYY-MM-DD}.log"),
        rotation="00:00",  # Rotazione giornaliera a mezzanotte
        retention="30 days",  # Mantieni i log per 30 giorni
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )
    
    # Aggiungi gestore per gli errori separato
    logger.add(
        os.path.join(log_dir, "marketmover_errors_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention="60 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        encoding="utf-8"
    )
    
    logger.info("Sistema di logging inizializzato")


class StructuredLogger:
    """Logger per eventi strutturati in formato JSON."""
    
    def __init__(self, log_dir: str = "logs/events"):
        """
        Inizializza il logger strutturato.
        
        Args:
            log_dir: Directory per i file di log JSON
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Crea file di log per la sessione corrente
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"events_{self.session_id}.jsonl")
    
    def log_event(self, 
                 event_type: str, 
                 data: Dict[str, Any], 
                 level: str = "INFO") -> None:
        """
        Registra un evento strutturato.
        
        Args:
            event_type: Tipo di evento
            data: Dati dell'evento
            level: Livello di logging
        """
        timestamp = datetime.now().isoformat()
        
        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "level": level,
            "session_id": self.session_id,
            "data": data
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Errore nella registrazione dell'evento strutturato: {str(e)}")
    
    def log_market_event(self, 
                        symbol: str, 
                        event_subtype: str,
                        data: Dict[str, Any]) -> None:
        """
        Registra un evento di mercato.
        
        Args:
            symbol: Simbolo dell'asset
            event_subtype: Sottotipo di evento (price_alert, trend_change, ecc.)
            data: Dati dell'evento
        """
        self.log_event(
            event_type="market",
            data={
                "symbol": symbol,
                "subtype": event_subtype,
                **data
            }
        )
    
    def log_api_call(self, 
                    api_name: str, 
                    endpoint: str,
                    status: str,
                    duration_ms: Optional[float] = None,
                    params: Optional[Dict[str, Any]] = None,
                    error: Optional[str] = None) -> None:
        """
        Registra una chiamata API.
        
        Args:
            api_name: Nome dell'API
            endpoint: Endpoint chiamato
            status: Stato della chiamata (success, error)
            duration_ms: Durata in millisecondi
            params: Parametri della chiamata
            error: Messaggio di errore (se presente)
        """
        level = "INFO" if status == "success" else "ERROR"
        
        self.log_event(
            event_type="api_call",
            level=level,
            data={
                "api": api_name,
                "endpoint": endpoint,
                "status": status,
                "duration_ms": duration_ms,
                "params": params,
                "error": error
            }
        )


# Inizializza i logger
structured_logger = StructuredLogger()
