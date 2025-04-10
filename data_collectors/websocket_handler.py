"""
Modulo per la gestione delle connessioni websocket per dati in tempo reale.
"""
import json
import threading
import time
from typing import Dict, Any, Callable, List, Set
import websocket
from loguru import logger


class WebSocketManager:
    """Classe per la gestione delle connessioni websocket."""
    
    def __init__(self):
        """Inizializza il gestore websocket."""
        self.connections = {}  # Dizionario delle connessioni attive
        self.callbacks = {}  # Callback per ogni connessione
        self.stop_events = {}  # Eventi per fermare i thread
        self.reconnect_intervals = {}  # Intervalli di riconnessione
    
    def add_connection(self, 
                     name: str, 
                     url: str, 
                     on_message: Callable[[str], None],
                     subscription_msg: Dict[str, Any] = None,
                     reconnect_interval: int = 30):
        """
        Aggiunge una nuova connessione websocket.
        
        Args:
            name: Nome univoco per la connessione
            url: URL del websocket
            on_message: Funzione di callback per i messaggi ricevuti
            subscription_msg: Messaggio da inviare dopo la connessione
            reconnect_interval: Intervallo di riconnessione in secondi
        """
        if name in self.connections:
            logger.warning(f"Connessione '{name}' già esistente. Chiusura e ricreazione.")
            self.close_connection(name)
        
        # Crea nuovo evento di stop
        self.stop_events[name] = threading.Event()
        self.callbacks[name] = on_message
        self.reconnect_intervals[name] = reconnect_interval
        
        # Funzioni di callback websocket
        def on_open(ws):
            logger.info(f"Connessione websocket '{name}' aperta")
            if subscription_msg:
                ws.send(json.dumps(subscription_msg))
                logger.info(f"Inviato messaggio di sottoscrizione per '{name}'")
        
        def on_message_wrapper(ws, message):
            try:
                self.callbacks[name](message)
            except Exception as e:
                logger.error(f"Errore nel gestore dei messaggi per '{name}': {str(e)}")
        
        def on_error(ws, error):
            logger.error(f"Errore nella connessione websocket '{name}': {str(error)}")
        
        def on_close(ws, close_status_code, close_msg):
            msg = f"Connessione websocket '{name}' chiusa"
            if close_status_code or close_msg:
                msg += f" ({close_status_code}: {close_msg})"
            logger.info(msg)
            
            # Riconnetti se non è stato richiesto uno stop
            if name in self.stop_events and not self.stop_events[name].is_set():
                interval = self.reconnect_intervals.get(name, 30)
                logger.info(f"Tentativo di riconnessione tra {interval} secondi...")
                time.sleep(interval)
                self._start_connection_thread(name, url, subscription_msg)
        
        # Crea e avvia la connessione
        self._start_connection_thread(name, url, subscription_msg)
    
    def _start_connection_thread(self, name: str, url: str, subscription_msg: Dict[str, Any] = None):
        """
        Avvia un thread per la connessione websocket.
        
        Args:
            name: Nome della connessione
            url: URL del websocket
            subscription_msg: Messaggio di sottoscrizione
        """
        def run_websocket():
            # Crea websocket con callback
            ws = websocket.WebSocketApp(
                url,
                on_open=lambda ws: self._on_open_wrapper(ws, name, subscription_msg),
                on_message=lambda ws, msg: self._on_message_wrapper(ws, msg, name),
                on_error=lambda ws, err: self._on_error_wrapper(ws, err, name),
                on_close=lambda ws, code, msg: self._on_close_wrapper(ws, code, msg, name, url, subscription_msg)
            )
            
            self.connections[name] = ws
            
            # Avvia il websocket
            ws.run_forever()
            
            logger.debug(f"Thread websocket '{name}' terminato")
        
        # Avvia il thread
        thread = threading.Thread(target=run_websocket, daemon=True)
        thread.start()
        logger.info(f"Avviato thread per connessione websocket '{name}'")
    
    def _on_open_wrapper(self, ws, name: str, subscription_msg: Dict[str, Any] = None):
        """Wrapper per l'evento on_open."""
        logger.info(f"Connessione websocket '{name}' aperta")
        if subscription_msg:
            ws.send(json.dumps(subscription_msg))
            logger.info(f"Inviato messaggio di sottoscrizione per '{name}'")
    
    def _on_message_wrapper(self, ws, message: str, name: str):
        """Wrapper per l'evento on_message."""
        try:
            if name in self.callbacks:
                self.callbacks[name](message)
        except Exception as e:
            logger.error(f"Errore nel gestore dei messaggi per '{name}': {str(e)}")
    
    def _on_error_wrapper(self, ws, error, name: str):
        """Wrapper per l'evento on_error."""
        logger.error(f"Errore nella connessione websocket '{name}': {str(error)}")
    
    def _on_close_wrapper(self, ws, close_status_code, close_msg, name: str, url: str, subscription_msg: Dict[str, Any] = None):
        """Wrapper per l'evento on_close."""
        msg = f"Connessione websocket '{name}' chiusa"
        if close_status_code or close_msg:
            msg += f" ({close_status_code}: {close_msg})"
        logger.info(msg)
        
        # Riconnetti se non è stato richiesto uno stop
        if name in self.stop_events and not self.stop_events[name].is_set():
            interval = self.reconnect_intervals.get(name, 30)
            logger.info(f"Tentativo di riconnessione tra {interval} secondi...")
            time.sleep(interval)
            self._start_connection_thread(name, url, subscription_msg)
    
    def close_connection(self, name: str):
        """
        Chiude una connessione websocket.
        
        Args:
            name: Nome della connessione da chiudere
        """
        if name in self.connections:
            # Imposta l'evento di stop
            if name in self.stop_events:
                self.stop_events[name].set()
            
            # Chiudi la connessione
            try:
                self.connections[name].close()
                logger.info(f"Chiusa connessione websocket '{name}'")
            except Exception as e:
                logger.error(f"Errore nella chiusura della connessione '{name}': {str(e)}")
            
            # Rimuovi la connessione dalle strutture dati
            self.connections.pop(name, None)
        else:
            logger.warning(f"Tentativo di chiusura di una connessione inesistente: '{name}'")
    
    def close_all(self):
        """Chiude tutte le connessioni websocket."""
        for name in list(self.connections.keys()):
            self.close_connection(name)
        
        # Pulisci le strutture dati
        self.connections = {}
        self.callbacks = {}
        self.stop_events = {}
        self.reconnect_intervals = {}
        
        logger.info("Tutte le connessioni websocket sono state chiuse")


class BinanceWebSocketClient:
    """Client per websocket Binance."""
    
    def __init__(self, db_manager, symbols: List[str] = None):
        """
        Inizializza il client websocket Binance.
        
        Args:
            db_manager: Istanza del database manager
            symbols: Lista di simboli da monitorare
        """
        self.db_manager = db_manager
        self.symbols = symbols or ["BTC", "ETH", "BNB", "XRP", "ADA"]
        self.ws_manager = WebSocketManager()
        self.active_streams = set()
    
    def start_ticker_stream(self):
        """Avvia stream per i ticker in tempo reale."""
        
        def on_ticker_message(message):
            try:
                data = json.loads(message)
                
                # Formato adatto per dati ticker Binance
                if 's' in data and 'c' in data:
                    symbol = data['s'].replace('USDT', '')
                    
                    # Crea record per il database
                    ticker_data = {
                        'symbol': symbol,
                        'price': float(data['c']),
                        'high': float(data.get('h', 0)),
                        'low': float(data.get('l', 0)),
                        'volume': float(data.get('v', 0)),
                        'quote_volume': float(data.get('q', 0)),
                        'price_change': float(data.get('p', 0)),
                        'price_change_percent': float(data.get('P', 0)),
                        'source': 'binance_ws'
                    }
                    
                    # Memorizza nel database
                    self.db_manager.store_crypto_data(symbol, "realtime", ticker_data)
                    
                    logger.debug(f"Aggiornamento ticker per {symbol}: {ticker_data['price']} USD")
            except Exception as e:
                logger.error(f"Errore nell'elaborazione del messaggio ticker: {str(e)}")
        
        # Crea endpoint per ogni simbolo
        for symbol in self.symbols:
            stream_name = f"ticker_{symbol.lower()}usdt"
            
            if stream_name in self.active_streams:
                continue
            
            # URL websocket Binance
            url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}usdt@ticker"
            
            # Aggiungi connessione
            self.ws_manager.add_connection(
                name=stream_name,
                url=url,
                on_message=on_ticker_message
            )
            
            self.active_streams.add(stream_name)
            logger.info(f"Avviato stream ticker per {symbol}")
    
    def start_kline_stream(self, interval: str = "1m"):
        """
        Avvia stream per i dati kline (candele).
        
        Args:
            interval: Intervallo temporale (1m, 5m, 15m, 1h, 4h, 1d)
        """
        
        def on_kline_message(message):
            try:
                data = json.loads(message)
                
                # Controlla se è un messaggio kline valido
                if 'k' in data:
                    kline = data['k']
                    symbol = kline['s'].replace('USDT', '')
                    
                    # Crea record per il database
                    kline_data = {
                        'symbol': symbol,
                        'interval': kline['i'],
                        'open_time': kline['t'] // 1000,  # Converti da ms a s
                        'close_time': kline['T'] // 1000,  # Converti da ms a s
                        'open': float(kline['o']),
                        'high': float(kline['h']),
                        'low': float(kline['l']),
                        'close': float(kline['c']),
                        'volume': float(kline['v']),
                        'trades': kline['n'],
                        'final': kline['x'],  # True se la candela è chiusa
                        'source': 'binance_ws'
                    }
                    
                    # Memorizza nel database solo se la candela è chiusa
                    if kline['x']:
                        self.db_manager.store_crypto_data(symbol, kline['i'], kline_data)
                        logger.debug(f"Candela {kline['i']} completata per {symbol}")
            except Exception as e:
                logger.error(f"Errore nell'elaborazione del messaggio kline: {str(e)}")
        
        # Crea endpoint per ogni simbolo
        for symbol in self.symbols:
            stream_name = f"kline_{symbol.lower()}usdt_{interval}"
            
            if stream_name in self.active_streams:
                continue
            
            # URL websocket Binance
            url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}usdt@kline_{interval}"
            
            # Aggiungi connessione
            self.ws_manager.add_connection(
                name=stream_name,
                url=url,
                on_message=on_kline_message
            )
            
            self.active_streams.add(stream_name)
            logger.info(f"Avviato stream kline {interval} per {symbol}")
    
    def stop(self):
        """Ferma tutti gli stream."""
        self.ws_manager.close_all()
        self.active_streams.clear()
        logger.info("Fermati tutti gli stream Binance")
