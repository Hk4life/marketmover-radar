"""
Test unitari per i collettori di dati.
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Aggiungi il percorso principale al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_collectors.crypto_collector import CryptoDataCollector, collect_all_crypto_data
from data_collectors.news_collector import NewsCollector, collect_all_news


class TestCryptoDataCollector(unittest.TestCase):
    """Test per la classe CryptoDataCollector."""
    
    @patch('data_collectors.crypto_collector.CoinGeckoAPI')
    def setUp(self, mock_coingecko):
        """Configura il test."""
        self.mock_coingecko = mock_coingecko
        self.collector = CryptoDataCollector()
    
    def test_get_coin_price(self):
        """Test per il metodo get_coin_price."""
        # Configura il mock
        self.collector.coingecko.get_price.return_value = {
            'bitcoin': {
                'usd': 50000,
                'usd_market_cap': 1000000000000,
                'usd_24h_vol': 50000000000,
                'usd_24h_change': 2.5
            }
        }
        
        # Chiama il metodo
        result = self.collector.get_coin_price('BTC')
        
        # Verifica il risultato
        self.assertEqual(result['symbol'], 'BTC')
        self.assertEqual(result['price'], 50000)
        self.assertEqual(result['market_cap'], 1000000000000)
        self.assertEqual(result['volume_24h'], 50000000000)
        self.assertEqual(result['change_24h'], 2.5)
        self.assertEqual(result['source'], 'coingecko')
    
    def test_get_historical_ohlc(self):
        """Test per il metodo get_historical_ohlc."""
        # Simula binance non configurato
        self.collector.binance = None
        result = self.collector.get_historical_ohlc('BTC')
        self.assertEqual(result, [])
        
        # Configura binance mock
        self.collector.binance = MagicMock()
        mock_ohlcv = [
            [1627776000000, 40000, 41000, 39000, 40500, 1000],
            [1627862400000, 40500, 42000, 40000, 41800, 1200]
        ]
        self.collector.binance.fetch_ohlcv.return_value = mock_ohlcv
        
        # Chiama il metodo
        result = self.collector.get_historical_ohlc('BTC', '1d', 2)
        
        # Verifica il risultato
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['symbol'], 'BTC')
        self.assertEqual(result[0]['timestamp'], 1627776000)
        self.assertEqual(result[0]['open'], 40000)
        self.assertEqual(result[0]['high'], 41000)
        self.assertEqual(result[0]['low'], 39000)
        self.assertEqual(result[0]['close'], 40500)
        self.assertEqual(result[0]['volume'], 1000)
        self.assertEqual(result[0]['interval'], '1d')
        self.assertEqual(result[0]['source'], 'binance')


class TestNewsCollector(unittest.TestCase):
    """Test per la classe NewsCollector."""
    
    @patch('data_collectors.news_collector.NewsApiClient')
    def setUp(self, mock_newsapi):
        """Configura il test."""
        self.mock_newsapi = mock_newsapi
        self.collector = NewsCollector()
        self.collector.newsapi = mock_newsapi.return_value
    
    def test_get_news_from_newsapi(self):
        """Test per il metodo get_news_from_newsapi."""
        # Configura il mock
        self.collector.newsapi.get_everything.return_value = {
            'status': 'ok',
            'totalResults': 2,
            'articles': [
                {
                    'source': {'id': 'cnn', 'name': 'CNN'},
                    'author': 'John Doe',
                    'title': 'Bitcoin hits $60,000',
                    'description': 'Bitcoin reaches new all-time high',
                    'url': 'https://example.com/news/1',
                    'publishedAt': '2023-01-01T12:00:00Z',
                    'content': 'Full content here...'
                },
                {
                    'source': {'id': 'bbc', 'name': 'BBC'},
                    'author': 'Jane Smith',
                    'title': 'Ethereum integration successful',
                    'description': 'The Ethereum network completed its upgrade',
                    'url': 'https://example.com/news/2',
                    'publishedAt': '2023-01-02T10:30:00Z',
                    'content': 'More content here...'
                }
            ]
        }
        
        # Chiama il metodo
        result = self.collector.get_news_from_newsapi()
        
        # Verifica il risultato
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Bitcoin hits $60,000')
        self.assertEqual(result[0]['source'], 'CNN')
        self.assertEqual(result[1]['title'], 'Ethereum integration successful')
        self.assertTrue('BTC' in result[0]['related_assets'])
        self.assertTrue('ETH' in result[1]['related_assets'])
    
    def test_extract_entities_from_news(self):
        """Test per il metodo extract_entities_from_news."""
        # Crea notizia di test
        news = {
            'title': 'Bitcoin price surges 5% to $52,000',
            'description': 'The cryptocurrency market saw gains today, with Bitcoin up $2,500.',
            'content': 'Analysts expect continued bullish momentum as institutional investors increase their positions.'
        }
        
        # Chiama il metodo
        result = self.collector.extract_entities_from_news(news)
        
        # Verifica il risultato
        self.assertTrue('extracted_entities' in result)
        self.assertTrue('$52,000' in result['extracted_entities']['money_mentions'])
        self.assertTrue('5%' in result['extracted_entities']['percentage_mentions'])
        self.assertTrue(('bullish', 'positive') in result['extracted_entities']['sentiment_terms'])
        self.assertTrue(result['extracted_entities']['sentiment_score'] > 0)


if __name__ == '__main__':
    unittest.main()
