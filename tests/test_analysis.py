"""
Test unitari per i moduli di analisi.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import pandas as pd
import numpy as np

# Aggiungi il percorso principale al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.trend_detector import TrendDetector
from analysis.llm_analyzer import LLMAnalyzer


class TestTrendDetector(unittest.TestCase):
    """Test per la classe TrendDetector."""
    
    def setUp(self):
        """Configura il test."""
        self.detector = TrendDetector()
        
        # Crea dati di test (10 candele OHLC)
        self.test_data = []
        base_price = 50000
        
        for i in range(10):
            # Simuliamo un trend rialzista
            close_price = base_price * (1 + 0.01 * i)
            self.test_data.append({
                'timestamp': 1625097600 + i * 3600,
                'open': close_price * 0.99,
                'high': close_price * 1.02,
                'low': close_price * 0.98,
                'close': close_price,
                'volume': 1000000 * (1 + 0.1 * np.random.random())
            })
    
    def test_detect_price_trends(self):
        """Test per il metodo detect_price_trends."""
        result = self.detector.detect_price_trends(self.test_data)
        
        # Verifica i campi principali
        self.assertIn('trend', result)
        self.assertIn('strength', result)
        self.assertIn('support', result)
        self.assertIn('resistance', result)
        
        # Data la natura rialzista dei dati di test, ci aspettiamo un uptrend
        self.assertEqual(result['trend'], 'uptrend')
        self.assertTrue(result['strength'] > 0)
    
    def test_detect_volume_trends(self):
        """Test per il metodo detect_volume_trends."""
        result = self.detector.detect_volume_trends(self.test_data)
        
        # Verifica i campi principali
        self.assertIn('trend', result)
        self.assertIn('strength', result)
        self.assertIn('avg_volume', result)
    
    def test_detect_momentum(self):
        """Test per il metodo detect_momentum."""
        # Aggiungiamo più dati per RSI
        for i in range(10):
            # Continuiamo il trend rialzista
            close_price = self.test_data[-1]['close'] * (1 + 0.01)
            self.test_data.append({
                'timestamp': self.test_data[-1]['timestamp'] + 3600,
                'open': close_price * 0.99,
                'high': close_price * 1.02,
                'low': close_price * 0.98,
                'close': close_price,
                'volume': 1000000 * (1 + 0.1 * np.random.random())
            })
        
        result = self.detector.detect_momentum(self.test_data)
        
        # Verifica i campi principali
        self.assertIn('rsi', result)
        self.assertIn('momentum', result)
        self.assertIn('macd', result)
        
        # In un trend rialzista, il momentum dovrebbe essere positivo
        self.assertTrue(result['momentum'] > 0)
    
    def test_detect_volatility(self):
        """Test per il metodo detect_volatility."""
        result = self.detector.detect_volatility(self.test_data)
        
        # Verifica i campi principali
        self.assertIn('volatility', result)
        self.assertIn('atr', result)
        self.assertIn('bollinger_width', result)
    
    def test_analyze_all_trends(self):
        """Test per il metodo analyze_all_trends."""
        result = self.detector.analyze_all_trends(self.test_data)
        
        # Verifica la struttura del risultato
        self.assertIn('price', result)
        self.assertIn('volume', result)
        self.assertIn('momentum', result)
        self.assertIn('volatility', result)


class TestLLMAnalyzer(unittest.TestCase):
    """Test per la classe LLMAnalyzer."""
    
    @patch('analysis.llm_analyzer.requests')
    def setUp(self, mock_requests):
        """Configura il test."""
        self.mock_requests = mock_requests
        
        # Configura mock per la connessione a LM Studio
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'id': 'local-model', 'object': 'model'}]
        }
        mock_requests.get.return_value = mock_response
        
        # Configura mock per le chiamate LLM
        mock_llm_response = MagicMock()
        mock_llm_response.status_code = 200
        mock_llm_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'This is a test response from the LLM.'
                }
            }]
        }
        mock_requests.post.return_value = mock_llm_response
        
        # Inizializza l'analizzatore
        self.analyzer = LLMAnalyzer(server_url="http://localhost:1234/v1")
    
    def test_call_llm(self):
        """Test per il metodo _call_llm."""
        prompt = "This is a test prompt"
        result = self.analyzer._call_llm(prompt)
        
        # Verifica la chiamata a requests.post
        self.mock_requests.post.assert_called_once()
        # Verifica il risultato
        self.assertEqual(result, "This is a test response from the LLM.")
    
    def test_analyze_market_trends(self):
        """Test per il metodo analyze_market_trends."""
        # Dati di mercato di test
        market_data = {
            'BTC': [
                {'close': 50000, 'high': 51000, 'low': 49000, 'timestamp': 1625097600},
                {'close': 50500, 'high': 51500, 'low': 49500, 'timestamp': 1625101200}
            ]
        }
        
        # Configura mock per la risposta JSON dei trend
        trend_response = MagicMock()
        trend_response.status_code = 200
        trend_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '''
                    [
                        {"trend": "BTC in consolidation phase", "confidence": 0.85, "assets": ["BTC"], "direction": "neutral"}
                    ]
                    '''
                }
            }]
        }
        self.mock_requests.post.return_value = trend_response
        
        # Chiama il metodo
        result = self.analyzer.analyze_market_trends(market_data)
        
        # Verifica la struttura del risultato
        self.assertIn('analysis', result)
        self.assertIn('trends', result)
    
    def test_analyze_news(self):
        """Test per il metodo analyze_news."""
        # Notizie di test
        news_data = [
            {
                'title': 'Bitcoin Price Analysis',
                'source': 'CoinDesk',
                'extracted_entities': {'sentiment_score': 0.5},
                'related_assets': ['BTC']
            },
            {
                'title': 'Ethereum 2.0 Update',
                'source': 'CryptoNews',
                'extracted_entities': {'sentiment_score': 0.8},
                'related_assets': ['ETH']
            }
        ]
        
        # Configura mock per la risposta JSON degli insights
        insights_response = MagicMock()
        insights_response.status_code = 200
        insights_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '''
                    {
                        "themes": [
                            {"theme": "Technical Analysis", "frequency": 0.75, "assets": ["BTC"]}
                        ],
                        "overall_sentiment": 0.6,
                        "high_impact_news": [
                            {"title": "Ethereum 2.0 Update", "impact_score": 0.8, "assets": ["ETH"]}
                        ]
                    }
                    '''
                }
            }]
        }
        self.mock_requests.post.return_value = insights_response
        
        # Chiama il metodo
        result = self.analyzer.analyze_news(news_data)
        
        # Verifica la struttura del risultato
        self.assertIn('analysis', result)
        self.assertIn('themes', result)
        self.assertIn('sentiment', result)
        self.assertIn('high_impact_news', result)


if __name__ == '__main__':
    unittest.main()
