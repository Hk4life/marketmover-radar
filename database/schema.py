"""
Schema del database SQLite per MarketMover Radar.
"""
import sqlite3


def create_sqlite_tables(conn: sqlite3.Connection):
    """
    Crea le tabelle SQLite per il database.
    
    Args:
        conn: Connessione SQLite
    """
    cursor = conn.cursor()
    
    # Tabella per i dati crypto
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crypto_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        interval TEXT NOT NULL,
        price REAL NOT NULL,
        volume REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        timestamp INTEGER NOT NULL,
        data_json TEXT NOT NULL,
        UNIQUE(symbol, interval, timestamp)
    )
    ''')
    
    # Indici per ricerca rapida
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON crypto_data(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_crypto_interval ON crypto_data(interval)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_crypto_timestamp ON crypto_data(timestamp)')
    
    # Tabella per le notizie
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_id TEXT UNIQUE NOT NULL,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        url TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        data_json TEXT NOT NULL
    )
    ''')
    
    # Tabella per le categorie di notizie (relazione many-to-many)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_id TEXT NOT NULL,
        category TEXT NOT NULL,
        FOREIGN KEY (news_id) REFERENCES news_data(news_id) ON DELETE CASCADE,
        UNIQUE(news_id, category)
    )
    ''')
    
    # Tabella per gli asset correlati alle notizie (relazione many-to-many)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_id TEXT NOT NULL,
        asset TEXT NOT NULL,
        FOREIGN KEY (news_id) REFERENCES news_data(news_id) ON DELETE CASCADE,
        UNIQUE(news_id, asset)
    )
    ''')
    
    # Tabella per i risultati dell'analisi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        analysis_id TEXT UNIQUE NOT NULL,
        timestamp INTEGER NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        trends TEXT NOT NULL,
        data_json TEXT NOT NULL
    )
    ''')
    
    # Indici per le notizie
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news_data(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_source ON news_data(source)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_categories ON news_categories(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_assets ON news_assets(asset)')
    
    # Indici per l'analisi
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_timestamp ON analysis_results(timestamp)')
    
    conn.commit()
