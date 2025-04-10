"""
Gestione del database per MarketMover Radar.
Supporta sia Redis che SQLite per l'archiviazione dei dati.
"""
import json
import time
import sqlite3
from typing import Dict, List, Any, Optional, Union
import redis
from loguru import logger
import pandas as pd

from config import (
    USE_REDIS, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
    SQLITE_DB_PATH
)
from database.schema import create_sqlite_tables


class DatabaseManager:
    """Gestore del database con supporto per Redis e SQLite."""
    
    def __init__(self):
        """Inizializza la connessione al database."""
        self.use_redis = USE_REDIS
        
        if self.use_redis:
            try:
                self.redis_client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD,
                    db=REDIS_DB,
                    decode_responses=True
                )
                self.redis_client.ping()  # Verifica connessione
                logger.info("Connessione a Redis stabilita con successo")
            except Exception as e:
                logger.error(f"Errore nella connessione a Redis: {str(e)}")
                logger.info("Fallback a SQLite")
                self.use_redis = False
        
        if not self.use_redis:
            try:
                self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
                self.sqlite_conn.row_factory = sqlite3.Row
                create_sqlite_tables(self.sqlite_conn)
                logger.info("Connessione a SQLite stabilita con successo")
            except Exception as e:
                logger.error(f"Errore nella connessione a SQLite: {str(e)}")
                raise
    
    def close(self):
        """Chiude la connessione al database."""
        if self.use_redis:
            self.redis_client.close()
        else:
            self.sqlite_conn.close()
    
    def store_crypto_data(self, symbol: str, interval: str, data: Dict[str, Any]):
        """
        Archivia dati crypto nel database.
        
        Args:
            symbol: Simbolo della crypto (es. "BTC")
            interval: Intervallo temporale (es. "1h")
            data: Dati da archiviare
        """
        key = f"crypto:{symbol}:{interval}"
        timestamp = int(time.time())
        data_with_timestamp = {**data, "timestamp": timestamp}
        
        if self.use_redis:
            # Per Redis, memorizziamo come hash con TTL
            self.redis_client.hset(key, mapping=data_with_timestamp)
            # Impostiamo scadenza in base all'intervallo
            ttl_multiplier = {
                "1m": 60 * 24,        # 1 giorno
                "5m": 60 * 24 * 3,    # 3 giorni
                "15m": 60 * 24 * 7,   # 1 settimana
                "1h": 60 * 24 * 30,   # 1 mese
                "4h": 60 * 24 * 90,   # 3 mesi
                "1d": 60 * 24 * 365,  # 1 anno
            }
            ttl = ttl_multiplier.get(interval, 60 * 24 * 7)  # default 1 settimana
            self.redis_client.expire(key, ttl)
            
            # Memorizza anche nella serie temporale
            ts_key = f"ts:crypto:{symbol}:{interval}"
            self.redis_client.zadd(ts_key, {json.dumps(data): timestamp})
            self.redis_client.expire(ts_key, ttl)
        else:
            # Per SQLite
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                INSERT INTO crypto_data (symbol, interval, price, volume, high, low, timestamp, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    interval,
                    data.get("price", 0),
                    data.get("volume", 0),
                    data.get("high", 0),
                    data.get("low", 0),
                    timestamp,
                    json.dumps(data)
                )
            )
            self.sqlite_conn.commit()
    
    def store_news_data(self, source: str, news_data: Dict[str, Any]):
        """
        Archivia dati di notizie nel database.
        
        Args:
            source: Fonte della notizia
            news_data: Dati della notizia
        """
        timestamp = int(time.time())
        news_id = news_data.get("id", f"{source}_{timestamp}")
        
        if self.use_redis:
            key = f"news:{news_id}"
            news_with_timestamp = {**news_data, "timestamp": timestamp, "source": source}
            self.redis_client.hset(key, mapping=news_with_timestamp)
            # TTL di 7 giorni per le notizie
            self.redis_client.expire(key, 60 * 60 * 24 * 7)
            
            # Aggiunge alla lista cronologica delle notizie
            self.redis_client.zadd("news:timeline", {news_id: timestamp})
            
            # Aggiunge indici per categoria e asset correlati
            for category in news_data.get("categories", []):
                self.redis_client.sadd(f"news:category:{category}", news_id)
            
            for asset in news_data.get("related_assets", []):
                self.redis_client.sadd(f"news:asset:{asset}", news_id)
        else:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                INSERT INTO news_data (news_id, source, title, content, url, timestamp, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    news_id,
                    source,
                    news_data.get("title", ""),
                    news_data.get("content", ""),
                    news_data.get("url", ""),
                    timestamp,
                    json.dumps(news_data)
                )
            )
            
            # Inserisce categorie
            for category in news_data.get("categories", []):
                cursor.execute(
                    "INSERT INTO news_categories (news_id, category) VALUES (?, ?)",
                    (news_id, category)
                )
            
            # Inserisce asset correlati
            for asset in news_data.get("related_assets", []):
                cursor.execute(
                    "INSERT INTO news_assets (news_id, asset) VALUES (?, ?)",
                    (news_id, asset)
                )
            
            self.sqlite_conn.commit()
    
    def get_crypto_data(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Recupera dati crypto dal database.
        
        Args:
            symbol: Simbolo della crypto
            interval: Intervallo temporale
            limit: Numero massimo di record da recuperare
            
        Returns:
            Lista di dati ordinati cronologicamente
        """
        if self.use_redis:
            # Recupera dalla serie temporale
            ts_key = f"ts:crypto:{symbol}:{interval}"
            result = self.redis_client.zrevrange(ts_key, 0, limit - 1, withscores=True)
            
            # Converte risultati
            data_list = []
            for data_json, timestamp in result:
                data = json.loads(data_json)
                data["timestamp"] = int(timestamp)
                data_list.append(data)
            
            # Ordina per timestamp
            return sorted(data_list, key=lambda x: x["timestamp"])
        else:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT * FROM crypto_data
                WHERE symbol = ? AND interval = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (symbol, interval, limit)
            )
            
            rows = cursor.fetchall()
            data_list = []
            for row in rows:
                data = json.loads(row["data_json"])
                data["timestamp"] = row["timestamp"]
                data_list.append(data)
            
            # Ordina per timestamp
            return sorted(data_list, key=lambda x: x["timestamp"])
    
    def get_news_data(self, 
                     limit: int = 50, 
                     category: Optional[str] = None,
                     asset: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recupera dati di notizie dal database.
        
        Args:
            limit: Numero massimo di notizie da recuperare
            category: Filtra per categoria (opzionale)
            asset: Filtra per asset correlato (opzionale)
            
        Returns:
            Lista di notizie ordinate cronologicamente
        """
        if self.use_redis:
            news_ids = []
            
            if category:
                news_ids = self.redis_client.smembers(f"news:category:{category}")
            elif asset:
                news_ids = self.redis_client.smembers(f"news:asset:{asset}")
            else:
                # Recupera dalla timeline generale
                news_with_ts = self.redis_client.zrevrange(
                    "news:timeline", 0, limit - 1, withscores=True
                )
                news_ids = [news_id for news_id, _ in news_with_ts]
            
            # Limita alla quantità richiesta
            news_ids = list(news_ids)[:limit]
            
            # Recupera i dettagli delle notizie
            result = []
            for news_id in news_ids:
                news_data = self.redis_client.hgetall(f"news:{news_id}")
                if news_data:
                    # Converte tipi di dati
                    if "timestamp" in news_data:
                        news_data["timestamp"] = int(news_data["timestamp"])
                    if "categories" in news_data and isinstance(news_data["categories"], str):
                        news_data["categories"] = json.loads(news_data["categories"])
                    if "related_assets" in news_data and isinstance(news_data["related_assets"], str):
                        news_data["related_assets"] = json.loads(news_data["related_assets"])
                    
                    result.append(news_data)
            
            # Ordina per timestamp
            return sorted(result, key=lambda x: x.get("timestamp", 0), reverse=True)
        else:
            cursor = self.sqlite_conn.cursor()
            
            query = """
                SELECT n.*, GROUP_CONCAT(DISTINCT nc.category) as categories,
                GROUP_CONCAT(DISTINCT na.asset) as related_assets
                FROM news_data n
                LEFT JOIN news_categories nc ON n.news_id = nc.news_id
                LEFT JOIN news_assets na ON n.news_id = na.news_id
            """
            
            params = []
            
            if category:
                query += " WHERE n.news_id IN (SELECT news_id FROM news_categories WHERE category = ?)"
                params.append(category)
            elif asset:
                query += " WHERE n.news_id IN (SELECT news_id FROM news_assets WHERE asset = ?)"
                params.append(asset)
            
            query += " GROUP BY n.news_id ORDER BY n.timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                news_data = json.loads(row["data_json"])
                news_data["timestamp"] = row["timestamp"]
                
                # Gestisce liste concatenate
                if row["categories"]:
                    news_data["categories"] = row["categories"].split(",")
                if row["related_assets"]:
                    news_data["related_assets"] = row["related_assets"].split(",")
                
                result.append(news_data)
            
            return result
    
    def get_data_for_analysis(self, 
                             symbols: List[str], 
                             interval: str = "1h",
                             news_limit: int = 100) -> Dict[str, Any]:
        """
        Recupera dati completi per l'analisi, combinando crypto e notizie.
        
        Args:
            symbols: Lista di simboli crypto da analizzare
            interval: Intervallo temporale per i dati crypto
            news_limit: Numero massimo di notizie da includere
            
        Returns:
            Dizionario con dati di mercato e notizie
        """
        result = {
            "market_data": {},
            "news_data": self.get_news_data(limit=news_limit)
        }
        
        # Recupera dati di mercato per ogni simbolo
        for symbol in symbols:
            result["market_data"][symbol] = self.get_crypto_data(symbol, interval)
        
        return result
    
    def store_analysis_result(self, analysis_data: Dict[str, Any]):
        """
        Memorizza i risultati dell'analisi.
        
        Args:
            analysis_data: Dati dell'analisi da memorizzare
        """
        timestamp = int(time.time())
        analysis_id = f"analysis_{timestamp}"
        
        if self.use_redis:
            key = f"analysis:{analysis_id}"
            analysis_with_timestamp = {**analysis_data, "timestamp": timestamp}
            
            # Converti dizionari e liste in formato JSON per Redis
            for k, v in analysis_with_timestamp.items():
                if isinstance(v, (dict, list)):
                    analysis_with_timestamp[k] = json.dumps(v)
            
            self.redis_client.hset(key, mapping=analysis_with_timestamp)
            # TTL di 30 giorni per i risultati dell'analisi
            self.redis_client.expire(key, 60 * 60 * 24 * 30)
            
            # Aggiunge alla timeline dell'analisi
            self.redis_client.zadd("analysis:timeline", {analysis_id: timestamp})
        else:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                INSERT INTO analysis_results 
                (analysis_id, timestamp, title, summary, trends, data_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    timestamp,
                    analysis_data.get("title", ""),
                    analysis_data.get("summary", ""),
                    json.dumps(analysis_data.get("trends", [])),
                    json.dumps(analysis_data)
                )
            )
            self.sqlite_conn.commit()

    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Recupera l'analisi più recente.
        
        Returns:
            Dati dell'analisi più recente o None se non disponibile
        """
        if self.use_redis:
            # Ottiene l'ID dell'analisi più recente
            latest = self.redis_client.zrevrange("analysis:timeline", 0, 0)
            if not latest:
                return None
            
            analysis_id = latest[0]
            analysis_data = self.redis_client.hgetall(f"analysis:{analysis_id}")
            
            # Converti stringhe JSON in oggetti Python
            for k, v in analysis_data.items():
                try:
                    analysis_data[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    # Non è JSON, mantieni il valore originale
                    pass
            
            return analysis_data
        else:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT * FROM analysis_results
                ORDER BY timestamp DESC
                LIMIT 1
                """
            )
            
            row = cursor.fetchone()
            if not row:
                return None
            
            analysis_data = json.loads(row["data_json"])
            analysis_data["timestamp"] = row["timestamp"]
            
            return analysis_data
    
    def get_historical_data_as_dataframe(self, symbol: str, interval: str) -> pd.DataFrame:
        """
        Recupera dati storici come DataFrame pandas.
        
        Args:
            symbol: Simbolo della crypto
            interval: Intervallo temporale
            
        Returns:
            DataFrame pandas con i dati storici
        """
        data = self.get_crypto_data(symbol, interval, limit=1000)
        return pd.DataFrame(data)
