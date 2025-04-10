"""
Modulo per la raccolta dei dati crypto da diverse fonti.
"""
import time
from typing import Dict, List, Any, Optional
import ccxt
from pycoingecko import CoinGeckoAPI
import requests
from loguru import logger

from config import COINGECKO_API_KEY, BINANCE_API_KEY, BINANCE_API_SECRET


class CryptoDataCollector:
    """Classe per la raccolta di dati crypto da diverse fonti."""
    
    def __init__(self):
        """Inizializza i client per le API crypto."""
        # CoinGecko API
        self.coingecko = CoinGeckoAPI()
        if COINGECKO_API_KEY:
            self.coingecko.api_key = COINGECKO_API_KEY
        
        # Binance API
        self.binance = None
        if BINANCE_API_KEY and BINANCE_API_SECRET:
            self.binance = ccxt.binance({
                'apiKey': BINANCE_API_KEY,
                'secret': BINANCE_API_SECRET,
                'enableRateLimit': True
            })
        
        # Mappatura ID CoinGecko per asset comuni
        self.coingecko_id_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'SOL': 'solana',
            'DOGE': 'dogecoin',
            'MATIC': 'matic-network',
            'DOT': 'polkadot',
            'SHIB': 'shiba-inu',
            'LTC': 'litecoin',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'XLM': 'stellar'
        }
        
        # Mappatura intervalli CCXT
        self.ccxt_timeframe_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
    
    def get_coin_price(self, symbol: str) -> Dict[str, Any]:
        """
        Ottiene il prezzo corrente di una crypto da CoinGecko.
        
        Args:
            symbol: Simbolo della crypto (es. 'BTC')
            
        Returns:
            Dizionario con informazioni sul prezzo
        """
        try:
            coin_id = self.coingecko_id_map.get(symbol, symbol.lower())
            data = self.coingecko.get_price(
                ids=coin_id,
                vs_currencies='usd',
                include_market_cap=True,
                include_24hr_vol=True,
                include_24hr_change=True
            )
            
            if not data or coin_id not in data:
                logger.warning(f"Nessun dato disponibile per {symbol} da CoinGecko")
                return {}
            
            return {
                'symbol': symbol,
                'price': data[coin_id]['usd'],
                'market_cap': data[coin_id]['usd_market_cap'],
                'volume_24h': data[coin_id]['usd_24h_vol'],
                'change_24h': data[coin_id]['usd_24h_change'],
                'source': 'coingecko',
                'timestamp': int(time.time())
            }
        except Exception as e:
            logger.error(f"Errore nel recupero del prezzo per {symbol} da CoinGecko: {str(e)}")
            return {}
    
    def get_detailed_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Ottiene dati di mercato dettagliati da CoinGecko.
        
        Args:
            symbol: Simbolo della crypto
            
        Returns:
            Dizionario con dati di mercato dettagliati
        """
        try:
            coin_id = self.coingecko_id_map.get(symbol, symbol.lower())
            data = self.coingecko.get_coin_by_id(
                id=coin_id,
                localization='false',
                tickers=False,
                market_data=True,
                community_data=False,
                developer_data=False
            )
            
            if not data or 'market_data' not in data:
                logger.warning(f"Nessun dato di mercato dettagliato per {symbol}")
                return {}
            
            market_data = data['market_data']
            
            return {
                'symbol': symbol,
                'name': data.get('name', ''),
                'price': market_data['current_price'].get('usd', 0),
                'market_cap': market_data['market_cap'].get('usd', 0),
                'volume_24h': market_data['total_volume'].get('usd', 0),
                'high_24h': market_data['high_24h'].get('usd', 0),
                'low_24h': market_data['low_24h'].get('usd', 0),
                'price_change_24h': market_data.get('price_change_24h', 0),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h', 0),
                'market_cap_change_24h': market_data.get('market_cap_change_24h', 0),
                'market_cap_change_percentage_24h': market_data.get('market_cap_change_percentage_24h', 0),
                'circulating_supply': market_data.get('circulating_supply', 0),
                'total_supply': market_data.get('total_supply', 0),
                'max_supply': market_data.get('max_supply', 0),
                'last_updated': data.get('last_updated', ''),
                'source': 'coingecko_detailed',
                'timestamp': int(time.time())
            }
        except Exception as e:
            logger.error(f"Errore nel recupero dei dati dettagliati per {symbol}: {str(e)}")
            return {}
    
    def get_historical_ohlc(self, 
                           symbol: str, 
                           interval: str = '1h', 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Ottiene dati OHLC storici da Binance.
        
        Args:
            symbol: Simbolo della crypto
            interval: Intervallo temporale (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Numero di candle da recuperare
            
        Returns:
            Lista di candle OHLC
        """
        if not self.binance:
            logger.warning("API Binance non configurate, impossibile ottenere dati OHLC")
            return []
        
        try:
            # Converti simbolo in formato Binance
            market_symbol = f"{symbol}/USDT"
            timeframe = self.ccxt_timeframe_map.get(interval, '1h')
            
            # Recupera i dati OHLC
            ohlcv = self.binance.fetch_ohlcv(
                symbol=market_symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            # Converti in lista di dizionari
            result = []
            for candle in ohlcv:
                timestamp, open_price, high, low, close, volume = candle
                result.append({
                    'symbol': symbol,
                    'timestamp': timestamp // 1000,  # Converti da millisecondi a secondi
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume,
                    'interval': interval,
                    'source': 'binance'
                })
            
            return result
        except Exception as e:
            logger.error(f"Errore nel recupero dei dati OHLC per {symbol}: {str(e)}")
            return []
    
    def get_market_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Calcola indicatori di mercato per un asset.
        
        Args:
            symbol: Simbolo della crypto
            
        Returns:
            Dizionario con indicatori di mercato
        """
        try:
            # Recupera dati OHLC per calcolo indicatori
            ohlc_data = self.get_historical_ohlc(symbol, interval='1d', limit=30)
            
            if not ohlc_data:
                logger.warning(f"Dati insufficienti per calcolare indicatori per {symbol}")
                return {}
            
            # Esempio: Calcolo indicatori semplici
            closes = [candle['close'] for candle in ohlc_data]
            
            # Media mobile a 7 giorni
            sma7 = sum(closes[-7:]) / 7 if len(closes) >= 7 else None
            
            # Media mobile a 14 giorni
            sma14 = sum(closes[-14:]) / 14 if len(closes) >= 14 else None
            
            # Volatilità (deviazione standard)
            volatility = None
            if len(closes) >= 7:
                mean = sum(closes[-7:]) / 7
                variance = sum((price - mean) ** 2 for price in closes[-7:]) / 7
                volatility = variance ** 0.5
            
            # RSI (versione semplificata)
            rsi = None
            if len(closes) >= 14:
                gains = []
                losses = []
                for i in range(len(closes) - 14, len(closes) - 1):
                    diff = closes[i+1] - closes[i]
                    if diff >= 0:
                        gains.append(diff)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(diff))
                
                avg_gain = sum(gains) / len(gains) if gains else 0
                avg_loss = sum(losses) / len(losses) if losses else 0
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 100
            
            return {
                'symbol': symbol,
                'sma7': sma7,
                'sma14': sma14,
                'volatility': volatility,
                'rsi': rsi,
                'current_price': closes[-1] if closes else None,
                'price_7d_ago': closes[-7] if len(closes) >= 7 else None,
                'price_14d_ago': closes[-14] if len(closes) >= 14 else None,
                'price_change_7d': ((closes[-1] / closes[-7]) - 1) * 100 if len(closes) >= 7 else None,
                'price_change_14d': ((closes[-1] / closes[-14]) - 1) * 100 if len(closes) >= 14 else None,
                'source': 'calculated',
                'timestamp': int(time.time())
            }
        except Exception as e:
            logger.error(f"Errore nel calcolo degli indicatori per {symbol}: {str(e)}")
            return {}
    
    def get_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Ottiene dati di sentiment di mercato da CoinGecko.
        
        Args:
            symbol: Simbolo della crypto
            
        Returns:
            Dizionario con dati di sentiment
        """
        try:
            coin_id = self.coingecko_id_map.get(symbol, symbol.lower())
            
            # CoinGecko fornisce una metrica di community_data che include sentiment
            data = self.coingecko.get_coin_by_id(
                id=coin_id,
                localization='false',
                tickers=False,
                market_data=False,
                community_data=True,
                developer_data=False
            )
            
            if not data or 'sentiment_votes_up_percentage' not in data:
                logger.warning(f"Nessun dato di sentiment disponibile per {symbol}")
                return {}
            
            return {
                'symbol': symbol,
                'sentiment_up_percentage': data.get('sentiment_votes_up_percentage', 0),
                'sentiment_down_percentage': data.get('sentiment_votes_down_percentage', 0),
                'reddit_subscribers': data.get('community_data', {}).get('reddit_subscribers', 0),
                'twitter_followers': data.get('community_data', {}).get('twitter_followers', 0),
                'reddit_avg_posts_48h': data.get('community_data', {}).get('reddit_average_posts_48h', 0),
                'reddit_avg_comments_48h': data.get('community_data', {}).get('reddit_average_comments_48h', 0),
                'source': 'coingecko_sentiment',
                'timestamp': int(time.time())
            }
        except Exception as e:
            logger.error(f"Errore nel recupero dei dati di sentiment per {symbol}: {str(e)}")
            return {}


def collect_all_crypto_data(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Funzione di utilità per raccogliere tutti i dati per un elenco di simboli.
    
    Args:
        symbols: Lista di simboli crypto
        
    Returns:
        Dizionario organizzato per simbolo con tutti i dati
    """
    collector = CryptoDataCollector()
    all_data = {}
    
    for symbol in symbols:
        logger.info(f"Raccolta dati per {symbol}...")
        
        symbol_data = {
            'price': collector.get_coin_price(symbol),
            'market_data': collector.get_detailed_market_data(symbol),
            'ohlc': {
                '1h': collector.get_historical_ohlc(symbol, '1h', 24),
                '4h': collector.get_historical_ohlc(symbol, '4h', 30),
                '1d': collector.get_historical_ohlc(symbol, '1d', 30)
            },
            'indicators': collector.get_market_indicators(symbol),
            'sentiment': collector.get_market_sentiment(symbol)
        }
        
        all_data[symbol] = symbol_data
        
        # Pausa per rispettare i rate limit
        time.sleep(1)
    
    return all_data
