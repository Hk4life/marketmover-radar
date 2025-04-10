"""
Configurazione globale per MarketMover Radar.
"""
import os
from dotenv import load_dotenv

# Carica variabili d'ambiente dal file .env
load_dotenv()

# Configurazione API
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")

# Configurazione database
USE_REDIS = os.getenv("USE_REDIS", "True").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# SQLite come fallback o alternativa
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "marketmover.db")

# Configurazione LM Studio
LM_STUDIO_HOST = os.getenv("LM_STUDIO_HOST", "localhost")
LM_STUDIO_PORT = int(os.getenv("LM_STUDIO_PORT", 1234))
LM_STUDIO_URL = f"http://{LM_STUDIO_HOST}:{LM_STUDIO_PORT}/v1"

# Configurazione dell'applicazione
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATA_REFRESH_INTERVAL = int(os.getenv("DATA_REFRESH_INTERVAL", 300))  # secondi
NEWS_REFRESH_INTERVAL = int(os.getenv("NEWS_REFRESH_INTERVAL", 1800))  # secondi
REPORT_GENERATION_INTERVAL = int(os.getenv("REPORT_GENERATION_INTERVAL", 3600))  # secondi

# Elenco di asset crypto da monitorare
CRYPTO_ASSETS = [
    "BTC", "ETH", "BNB", "XRP", "SOL", 
    "ADA", "DOGE", "SHIB", "MATIC", "DOT",
    "LTC", "AVAX", "LINK", "UNI", "XLM"
]

# Categorie di notizie da monitorare
NEWS_CATEGORIES = [
    "cryptocurrency", "blockchain", "bitcoin", "ethereum",
    "financial-markets", "economy", "fintech", "regulations"
]

# Intervalli per i dati di mercato
MARKET_DATA_INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"]

# Configurazione sicurezza
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", 100))  # richieste per minuto
ENABLE_SSL = os.getenv("ENABLE_SSL", "False").lower() == "true"
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "")
