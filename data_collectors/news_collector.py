"""
Modulo per la raccolta di notizie finanziarie e crypto da diverse fonti.
"""
import time
from typing import Dict, List, Any, Optional
import re
from datetime import datetime, timedelta
import requests
import feedparser
from newsapi import NewsApiClient
from loguru import logger

from config import NEWSAPI_KEY, CRYPTO_ASSETS, NEWS_CATEGORIES


class NewsCollector:
    """Classe per la raccolta di notizie finanziarie e crypto."""
    
    def __init__(self):
        """Inizializza i client per le API di notizie."""
        self.newsapi = None
        if NEWSAPI_KEY:
            self.newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
    
    def get_news_from_newsapi(self, 
                             query: str = "cryptocurrency OR bitcoin OR ethereum",
                             days_back: int = 2,
                             language: str = 'en',
                             sort_by: str = 'publishedAt') -> List[Dict[str, Any]]:
        """
        Recupera notizie da NewsAPI.
        
        Args:
            query: Query di ricerca
            days_back: Giorni indietro da cui recuperare notizie
            language: Lingua delle notizie
            sort_by: Criterio di ordinamento
            
        Returns:
            Lista di articoli di notizie
        """
        if not self.newsapi:
            logger.warning("NewsAPI non configurata, impossibile ottenere notizie")
            return []
        
        try:
            # Calcola la data di inizio
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # Richiesta a NewsAPI
            response = self.newsapi.get_everything(
                q=query,
                from_param=from_date,
                language=language,
                sort_by=sort_by
            )
            
            if 'articles' not in response or not response['articles']:
                logger.warning(f"Nessuna notizia trovata per la query: {query}")
                return []
            
            # Processa e arricchisce gli articoli
            processed_articles = []
            for article in response['articles']:
                # Identifica asset crypto menzionati
                mentioned_assets = []
                for asset in CRYPTO_ASSETS:
                    # Cerca menzioni del simbolo o del nome completo
                    if (asset in article.get('title', '') or 
                        asset in article.get('description', '') or
                        asset.lower() in article.get('content', '').lower()):
                        mentioned_assets.append(asset)
                
                # Identifica categorie dalle parole chiave
                categories = []
                content = (article.get('title', '') + ' ' + 
                          article.get('description', '') + ' ' + 
                          article.get('content', ''))
                content = content.lower()
                
                for category in NEWS_CATEGORIES:
                    if category.lower() in content:
                        categories.append(category)
                
                # Normalizza il formato della data
                published_at = article.get('publishedAt', '')
                timestamp = int(time.time())
                if published_at:
                    try:
                        dt = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                        timestamp = int(dt.timestamp())
                    except Exception:
                        pass
                
                # Crea articolo arricchito
                processed_article = {
                    'id': f"newsapi_{hash(article.get('url', ''))}",
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('content', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'NewsAPI'),
                    'published_at': published_at,
                    'timestamp': timestamp,
                    'related_assets': mentioned_assets,
                    'categories': categories,
                    'author': article.get('author', '')
                }
                
                processed_articles.append(processed_article)
            
            return processed_articles
        except Exception as e:
            logger.error(f"Errore nel recupero delle notizie da NewsAPI: {str(e)}")
            return []
    
    def get_news_from_rss(self, rss_url: str, max_items: int = 20) -> List[Dict[str, Any]]:
        """
        Recupera notizie da un feed RSS.
        
        Args:
            rss_url: URL del feed RSS
            max_items: Numero massimo di elementi da recuperare
            
        Returns:
            Lista di articoli di notizie
        """
        try:
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                logger.warning(f"Nessuna voce trovata nel feed RSS: {rss_url}")
                return []
            
            # Processa le voci del feed
            processed_articles = []
            for entry in feed.entries[:max_items]:
                # Identifica asset crypto menzionati
                mentioned_assets = []
                for asset in CRYPTO_ASSETS:
                    # Cerca menzioni del simbolo o del nome completo
                    if (asset in entry.get('title', '') or 
                        asset in entry.get('summary', '')):
                        mentioned_assets.append(asset)
                
                # Identifica categorie dalle parole chiave
                categories = []
                content = entry.get('title', '') + ' ' + entry.get('summary', '')
                content = content.lower()
                
                for category in NEWS_CATEGORIES:
                    if category.lower() in content:
                        categories.append(category)
                
                # Normalizza il formato della data
                published_at = entry.get('published', '')
                timestamp = int(time.time())
                if published_at:
                    try:
                        # Prova diversi formati di data
                        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%SZ"]:
                            try:
                                dt = datetime.strptime(published_at, fmt)
                                timestamp = int(dt.timestamp())
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                
                # Estrai il nome del feed come fonte
                feed_name = feed.feed.get('title', rss_url.split('//')[-1].split('/')[0])
                
                # Crea articolo arricchito
                processed_article = {
                    'id': f"rss_{hash(entry.get('link', ''))}",
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'source': feed_name,
                    'published_at': published_at,
                    'timestamp': timestamp,
                    'related_assets': mentioned_assets,
                    'categories': categories,
                    'author': entry.get('author', '')
                }
                
                processed_articles.append(processed_article)
            
            return processed_articles
        except Exception as e:
            logger.error(f"Errore nel recupero delle notizie dal feed RSS {rss_url}: {str(e)}")
            return []
    
    def extract_entities_from_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae entità e arricchisce i metadati di una notizia.
        
        Args:
            news_data: Dati della notizia
            
        Returns:
            Notizia arricchita con entità estratte
        """
        # Contenuto della notizia
        title = news_data.get('title', '')
        description = news_data.get('description', '')
        content = news_data.get('content', '')
        
        combined_text = f"{title} {description} {content}"
        
        # Pattern per l'estrazione di importi monetari
        money_pattern = r'\$\s?\d+(?:\.\d+)?(?:\s?[Mm]illion|\s?[Bb]illion)?|\d+(?:\.\d+)?\s?(?:USD|BTC|ETH)'
        money_mentions = re.findall(money_pattern, combined_text)
        
        # Pattern per l'estrazione di percentuali
        percentage_pattern = r'\d+(?:\.\d+)?%'
        percentage_mentions = re.findall(percentage_pattern, combined_text)
        
        # Pattern per eventi temporali
        time_pattern = r'(?:today|yesterday|last week|this month|next year)'
        time_mentions = re.findall(time_pattern, combined_text.lower())
        
        # Estrai termini di sentiment
        sentiment_terms = []
        positive_terms = ['bullish', 'surge', 'gain', 'rise', 'up', 'positive', 'growth', 'rally']
        negative_terms = ['bearish', 'crash', 'fall', 'drop', 'down', 'negative', 'decline', 'plunge']
        
        for term in positive_terms:
            if term in combined_text.lower():
                sentiment_terms.append((term, 'positive'))
        
        for term in negative_terms:
            if term in combined_text.lower():
                sentiment_terms.append((term, 'negative'))
        
        # Calcola un punteggio di sentiment grezzo
        sentiment_score = 0
        for term, sentiment in sentiment_terms:
            if sentiment == 'positive':
                sentiment_score += 1
            else:
                sentiment_score -= 1
        
        # Normalizza tra -1 e 1
        if sentiment_terms:
            sentiment_score = sentiment_score / len(sentiment_terms)
        
        # Aggiorna la notizia con le entità estratte
        enriched_news = news_data.copy()
        enriched_news['extracted_entities'] = {
            'money_mentions': money_mentions,
            'percentage_mentions': percentage_mentions,
            'time_mentions': time_mentions,
            'sentiment_terms': sentiment_terms,
            'sentiment_score': sentiment_score
        }
        
        return enriched_news


def collect_all_news() -> List[Dict[str, Any]]:
    """
    Funzione di utilità per raccogliere tutte le notizie da diverse fonti.
    
    Returns:
        Lista combinata di articoli di notizie
    """
    collector = NewsCollector()
    all_news = []
    
    # 1. Notizie da NewsAPI
    for query in [
        "cryptocurrency OR bitcoin OR ethereum",
        "blockchain technology",
        "crypto market analysis",
        "defi OR 'decentralized finance'",
        "nft OR 'non-fungible token'",
        "crypto regulation"
    ]:
        news = collector.get_news_from_newsapi(query=query, days_back=2)
        for article in news:
            # Arricchisci con estrazione di entità
            enriched_article = collector.extract_entities_from_news(article)
            all_news.append(enriched_article)
        
        # Pausa per rispettare i rate limit
        time.sleep(1)
    
    # 2. Notizie da feed RSS
    rss_feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptonews.com/news/feed/",
        "https://decrypt.co/feed",
        "https://blog.chain.link/rss/"
    ]
    
    for rss_url in rss_feeds:
        news = collector.get_news_from_rss(rss_url)
        for article in news:
            # Arricchisci con estrazione di entità
            enriched_article = collector.extract_entities_from_news(article)
            all_news.append(enriched_article)
        
        # Pausa per rispettare i rate limit
        time.sleep(1)
    
    # Rimuovi duplicati basati sull'URL
    unique_urls = set()
    unique_news = []
    
    for article in all_news:
        url = article.get('url', '')
        if url and url not in unique_urls:
            unique_urls.add(url)
            unique_news.append(article)
    
    return unique_news
