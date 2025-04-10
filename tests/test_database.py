"""
Test unitari per il gestore del database.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import time

# Aggiungi il percorso principale al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test per la classe DatabaseManager."""
    
    @patch('database.db_manager.redis.Redis')
    @patch('database.db_manager.sqlite3.connect')
    def setUp(self, mock_sqlite, mock_redis):
        """Configura il test."""
        self.mock_sqlite = mock_sqlite
        self.mock_redis = mock_redis
        
        # Configura i mock
        self.mock_redis_client = MagicMock()
        mock_redis.return_value = self.mock_redis_client
        self.mock_redis_client.ping.return_value = True
        
        self.mock_sqlite_conn = MagicMock()
        mock_sqlite.return_value = self.mock_sqlite_conn
        
        # Inizializza il database manager
        self.db_manager = DatabaseManager()
    
    def test_store_crypto_data_redis(self):
        """Test per il metodo store_crypto_data con Redis."""
        # Assicura che Redis sia utilizzato
        self.db_manager.use_redis = True
        
        # Dati di test
        symbol = 'BTC'
        interval = '1h'
        data = {
            'price': 50000,
            'volume': 1000000,
            'high': 51000,
            'low': 49000
        }
        
        # Chiama il metodo
        self.db_manager.store_crypto_data(symbol, interval, data)
        
        # Verifica le chiamate a Redis
        self.mock_redis_client.hset.assert_called()
        self.mock_redis_client.expire.assert_called()
        self.mock_redis_client.zadd.assert_called()
    
    def test_store_crypto_data_sqlite(self):
        """Test per il metodo store_crypto_data con SQLite."""
        # Imposta l'uso di SQLite
        self.db_manager.use_redis = False
        
        # Dati di test
        symbol = 'ETH'
        interval = '1d'
        data = {
            'price': 3000,
            'volume': 500000,
            'high': 3100,
            'low': 2900
        }
        
        # Configura mock per sqlite
        mock_cursor = MagicMock()
        self.mock_sqlite_conn.cursor.return_value = mock_cursor
        
        # Chiama il metodo
        self.db_manager.store_crypto_data(symbol, interval, data)
        
        # Verifica le chiamate a SQLite
        mock_cursor.execute.assert_called()
        self.mock_sqlite_conn.commit.assert_called()
    
    def test_store_news_data_redis(self):
        """Test per il metodo store_news_data con Redis."""
        # Assicura che Redis sia utilizzato
        self.db_manager.use_redis = True
        
        # Dati di test
        source = 'CoinDesk'
        news_data = {
            'id': 'news_123',
            'title': 'Bitcoin Price Analysis',
            'content': 'Content here...',
            'url': 'https://example.com/news/123',
            'categories': ['market', 'analysis'],
            'related_assets': ['BTC', 'ETH']
        }
        
        # Chiama il metodo
        self.db_manager.store_news_data(source, news_data)
        
        # Verifica le chiamate a Redis
        self.mock_redis_client.hset.assert_called()
        self.mock_redis_client.expire.assert_called()
        self.mock_redis_client.zadd.assert_called()
    
    def test_store_news_data_sqlite(self):
        """Test per il metodo store_news_data con SQLite."""
        # Imposta l'uso di SQLite
        self.db_manager.use_redis = False
        
        # Dati di test
        source = 'CryptoNews'
        news_data = {
            'id': 'news_456',
            'title': 'Ethereum 2.0 Update',
            'content': 'Content here...',
            'url': 'https://example.com/news/456',
            'categories': ['technology', 'development'],
            'related_assets': ['ETH']
        }
        
        # Configura mock per sqlite
        mock_cursor = MagicMock()
        self.mock_sqlite_conn.cursor.return_value = mock_cursor
        
        # Chiama il metodo
        self.db_manager.store_news_data(source, news_data)
        
        # Verifica le chiamate a SQLite
        self.assertEqual(mock_cursor.execute.call_count, 4)  # 1 insert principale + 2 categorie + 1 asset
        self.mock_sqlite_conn.commit.assert_called()
    
    def test_get_crypto_data_redis(self):
        """Test per il metodo get_crypto_data con Redis."""
        # Assicura che Redis sia utilizzato
        self.db_manager.use_redis = True
        
        # Dati di test
        symbol = 'BTC'
        interval = '1h'
        limit = 10
        
        # Configura mock per Redis
        mock_data = [
            ('{"close": 50000, "high": 51000}', 1625097600),
            ('{"close": 50500, "high": 51500}', 1625101200)
        ]
        self.mock_redis_client.zrevrange.return_value = mock_data
        
        # Chiama il metodo
        result = self.db_manager.get_crypto_data(symbol, interval, limit)
        
        # Verifica il risultato
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['timestamp'], 1625097600)
        self.assertEqual(result[0]['close'], 50000)
        self.assertEqual(result[1]['timestamp'], 1625101200)
        self.assertEqual(result[1]['close'], 50500)
    
    def test_get_news_data_redis(self):
        """Test per il metodo get_news_data con Redis."""
        # Assicura che Redis sia utilizzato
        self.db_manager.use_redis = True
        
        # Dati di test
        limit = 5
        
        # Configura mock per Redis
        self.mock_redis_client.zrevrange.return_value = [('news_123', 1625097600), ('news_456', 1625101200)]
        self.mock_redis_client.hgetall.side_effect = [
            {
                'title': 'Bitcoin News',
                'source': 'CoinDesk',
                'timestamp': '1625097600',
                'categories': '["market", "analysis"]',
                'related_assets': '["BTC"]'
            },
            {
                'title': 'Ethereum Update',
                'source': 'CryptoNews',
                'timestamp': '1625101200',
                'categories': '["technology"]',
                'related_assets': '["ETH"]'
            }
        ]
        
        # Chiama il metodo
        result = self.db_manager.get_news_data(limit=limit)
        
        # Verifica il risultato
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Ethereum Update')
        self.assertEqual(result[0]['timestamp'], 1625101200)
        self.assertEqual(result[1]['title'], 'Bitcoin News')
        self.assertEqual(result[1]['timestamp'], 1625097600)


if __name__ == '__main__':
    unittest.main()
