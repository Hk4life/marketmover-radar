"""
Applicazione principale MarketMover Radar.
Monitora in tempo reale mercati crypto e notizie economiche utilizzando LM Studio.
"""
import os
import time
import json
import threading
import schedule
from typing import Dict, List, Any, Optional
import argparse
from loguru import logger

from config import (
    CRYPTO_ASSETS, DATA_REFRESH_INTERVAL, NEWS_REFRESH_INTERVAL,
    REPORT_GENERATION_INTERVAL, MARKET_DATA_INTERVALS
)
from database.db_manager import DatabaseManager
from data_collectors.crypto_collector import collect_all_crypto_data
from data_collectors.news_collector import collect_all_news
from data_collectors.websocket_handler import BinanceWebSocketClient
from analysis.trend_detector import TrendDetector
from analysis.llm_analyzer import LLMAnalyzer
from visualization.chart_generator import ChartGenerator
from visualization.report_builder import ReportBuilder
from utils.logger import setup_logging, structured_logger
from utils.security import SecurityManager, RateLimiter


class MarketMoverRadar:
    """Classe principale per l'applicazione MarketMover Radar."""
    
    def __init__(self, 
                config_file: Optional[str] = None,
                enable_websockets: bool = True,
                enable_scheduling: bool = True):
        """
        Inizializza l'applicazione MarketMover Radar.
        
        Args:
            config_file: Percorso al file di configurazione (opzionale)
            enable_websockets: Abilita o disabilita i websocket per dati in tempo reale
            enable_scheduling: Abilita o disabilita la pianificazione dei task
        """
        # Inizializza il logging
        setup_logging()
        logger.info("Inizializzazione MarketMover Radar")
        
        # Carica la configurazione
        if config_file and os.path.exists(config_file):
            self._load_config(config_file)
        
        # Inizializza i componenti
        self.db_manager = DatabaseManager()
        self.trend_detector = TrendDetector()
        
        # Inizializza l'analizzatore LLM
        try:
            self.llm_analyzer = LLMAnalyzer()
            self.llm_available = True
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del LLM: {str(e)}")
            self.llm_analyzer = None
            self.llm_available = False
        
        # Inizializza il builder di report
        self.report_builder = ReportBuilder()
        
        # Inizializza i websocket se abilitati
        self.enable_websockets = enable_websockets
        self.websocket_client = None
        if self.enable_websockets:
            try:
                self.websocket_client = BinanceWebSocketClient(
                    self.db_manager,
                    symbols=CRYPTO_ASSETS
                )
                logger.info("Client WebSocket inizializzato")
            except Exception as e:
                logger.error(f"Errore nell'inizializzazione del client WebSocket: {str(e)}")
                self.enable_websockets = False
        
        # Inizializza la pianificazione dei task
        self.enable_scheduling = enable_scheduling
        if self.enable_scheduling:
            self._setup_schedules()
        
        # Flag per lo stato dell'applicazione
        self.running = False
        
        logger.info("MarketMover Radar inizializzato con successo")
    
    def _load_config(self, config_file: str):
        """
        Carica la configurazione da un file JSON.
        
        Args:
            config_file: Percorso al file di configurazione
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Aggiorna le variabili di configurazione
            # Qui puoi sovrascrivere le configurazioni del modulo config.py
            
            logger.info(f"Configurazione caricata da {config_file}")
        except Exception as e:
            logger.error(f"Errore nel caricamento della configurazione: {str(e)}")
    
    def _setup_schedules(self):
        """Configura la pianificazione dei task ricorrenti."""
        # Aggiorna dati di mercato ogni DATA_REFRESH_INTERVAL secondi
        schedule.every(DATA_REFRESH_INTERVAL).seconds.do(self.update_market_data)
        
        # Aggiorna notizie ogni NEWS_REFRESH_INTERVAL secondi
        schedule.every(NEWS_REFRESH_INTERVAL).seconds.do(self.update_news_data)
        
        # Genera report ogni REPORT_GENERATION_INTERVAL secondi
        schedule.every(REPORT_GENERATION_INTERVAL).seconds.do(self.generate_analysis_report)
        
        # Genera report completo giornaliero alle 23:00
        schedule.every().day.at("23:00").do(self.generate_daily_report)
        
        logger.info("Task pianificati configurati")
    
    def start(self):
        """Avvia l'applicazione MarketMover Radar."""
        if self.running:
            logger.warning("MarketMover Radar è già in esecuzione")
            return
        
        self.running = True
        logger.info("Avvio MarketMover Radar")
        
        # Avvia i websocket se abilitati
        if self.enable_websockets and self.websocket_client:
            logger.info("Avvio dei WebSocket")
            self.websocket_client.start_ticker_stream()
            self.websocket_client.start_kline_stream('1m')
        
        # Carica dati iniziali
        logger.info("Caricamento dati iniziali")
        self.update_market_data()
        self.update_news_data()
        
        # Genera analisi iniziale
        if self.llm_available:
            logger.info("Generazione analisi iniziale")
            self.generate_analysis_report()
        
        # Avvia il thread di pianificazione se abilitato
        if self.enable_scheduling:
            self._start_scheduler_thread()
    
    def _start_scheduler_thread(self):
        """Avvia un thread separato per la pianificazione."""
        def run_scheduler():
            logger.info("Thread di pianificazione avviato")
            while self.running:
                schedule.run_pending()
                time.sleep(1)
            logger.info("Thread di pianificazione fermato")
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Thread di pianificazione avviato")
    
    def stop(self):
        """Ferma l'applicazione MarketMover Radar."""
        if not self.running:
            logger.warning("MarketMover Radar non è in esecuzione")
            return
        
        self.running = False
        logger.info("Arresto MarketMover Radar")
        
        # Ferma i websocket se abilitati
        if self.enable_websockets and self.websocket_client:
            self.websocket_client.stop()
        
        # Chiudi la connessione al database
        self.db_manager.close()
        
        logger.info("MarketMover Radar arrestato con successo")
    
    def update_market_data(self):
        """Aggiorna i dati di mercato."""
        logger.info("Aggiornamento dati di mercato")
        
        try:
            # Raccolta dati di mercato
            market_data = collect_all_crypto_data(CRYPTO_ASSETS)
            
            # Memorizza i dati nel database
            for symbol, data in market_data.items():
                # Memorizza dati di prezzo
                if data.get('price'):
                    self.db_manager.store_crypto_data(symbol, "1m", data['price'])
                
                # Memorizza dati OHLC per diversi intervalli
                for interval, ohlc_data in data.get('ohlc', {}).items():
                    for candle in ohlc_data:
                        self.db_manager.store_crypto_data(symbol, interval, candle)
            
            logger.info(f"Dati di mercato aggiornati per {len(market_data)} asset")
            structured_logger.log_market_event("ALL", "market_data_update", {"count": len(market_data)})
            
            return True
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento dei dati di mercato: {str(e)}")
            return False
    
    def update_news_data(self):
        """Aggiorna i dati delle notizie."""
        logger.info("Aggiornamento dati notizie")
        
        try:
            # Raccolta notizie
            news_data = collect_all_news()
            
            # Memorizza le notizie nel database
            for news in news_data:
                self.db_manager.store_news_data(news.get('source', 'unknown'), news)
            
            logger.info(f"Dati notizie aggiornati: {len(news_data)} nuovi articoli")
            structured_logger.log_event("news", "news_data_update", {"count": len(news_data)})
            
            return True
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento dei dati notizie: {str(e)}")
            return False
    
    def generate_analysis_report(self):
        """Genera un report di analisi utilizzando LLM."""
        logger.info("Generazione report di analisi")
        
        if not self.llm_available:
            logger.warning("LLM non disponibile, impossibile generare report")
            return None
        
        try:
            # Recupera dati dal database
            market_data = {}
            for symbol in CRYPTO_ASSETS:
                market_data[symbol] = self.db_manager.get_crypto_data(symbol, "1h", 100)
            
            news_data = self.db_manager.get_news_data(limit=100)
            
            # Analisi di mercato
            logger.info("Analisi di mercato in corso...")
            market_analysis = self.llm_analyzer.analyze_market_trends(market_data)
            
            # Analisi delle notizie
            logger.info("Analisi delle notizie in corso...")
            news_analysis = self.llm_analyzer.analyze_news(news_data)
            
            # Generazione report completo
            logger.info("Generazione report completo...")
            report = self.llm_analyzer.generate_comprehensive_report(
                market_analysis,
                news_analysis,
                market_data
            )
            
            # Memorizza il risultato nel database
            self.db_manager.store_analysis_result(report)
            
            # Genera report HTML
            chart_generator = ChartGenerator()
            charts = []
            
            # Aggiungi grafici a candele per i principali asset
            for symbol in CRYPTO_ASSETS[:5]:  # Limita ai primi 5
                if symbol in market_data and market_data[symbol]:
                    chart = chart_generator.create_candlestick_chart(
                        market_data[symbol],
                        title=f"{symbol}/USD Price Chart"
                    )
                    charts.append(chart)
            
            # Grafico di confronto tra asset
            comparison_chart = chart_generator.create_multi_asset_comparison(
                {s: market_data[s] for s in CRYPTO_ASSETS[:5] if s in market_data},
                title="Asset Performance Comparison"
            )
            charts.append(comparison_chart)
            
            # Grafico sentiment notizie
            sentiment_chart = chart_generator.create_news_sentiment_chart(
                news_data,
                title="News Sentiment Analysis"
            )
            charts.append(sentiment_chart)
            
            # Genera HTML
            report_file = self.report_builder.generate_html_report(
                report.get('title', 'Market Analysis Report'),
                report.get('report', 'No analysis available'),
                charts,
                report
            )
            
            logger.info(f"Report di analisi generato: {report_file}")
            structured_logger.log_event("analysis", "report_generated", {"file": report_file})
            
            return report_file
        except Exception as e:
            logger.error(f"Errore nella generazione del report di analisi: {str(e)}")
            return None
    
    def generate_daily_report(self):
        """Genera un report giornaliero completo."""
        logger.info("Generazione report giornaliero")
        
        if not self.llm_available:
            logger.warning("LLM non disponibile, impossibile generare report giornaliero")
            return None
        
        try:
            # Recupera i dati più completi per l'analisi
            market_data = {}
            for symbol in CRYPTO_ASSETS:
                market_data[symbol] = self.db_manager.get_crypto_data(symbol, "1d", 30)
            
            news_data = self.db_manager.get_news_data(limit=100)
            
            # Recupera l'ultima analisi o generane una nuova
            analysis_results = self.db_manager.get_latest_analysis()
            if not analysis_results:
                analysis_results = self.llm_analyzer.generate_comprehensive_report(
                    self.llm_analyzer.analyze_market_trends(market_data),
                    self.llm_analyzer.analyze_news(news_data),
                    market_data
                )
            
            # Genera il report giornaliero
            report_file = self.report_builder.generate_daily_report(
                market_data,
                news_data,
                analysis_results
            )
            
            logger.info(f"Report giornaliero generato: {report_file}")
            structured_logger.log_event("analysis", "daily_report_generated", {"file": report_file})
            
            return report_file
        except Exception as e:
            logger.error(f"Errore nella generazione del report giornaliero: {str(e)}")
            return None
    
    def analyze_specific_asset(self, symbol: str) -> Dict[str, Any]:
        """
        Analizza uno specifico asset.
        
        Args:
            symbol: Simbolo dell'asset
            
        Returns:
            Risultato dell'analisi
        """
        logger.info(f"Analisi specifica per {symbol}")
        
        if not self.llm_available:
            logger.warning("LLM non disponibile, impossibile analizzare asset")
            return {"error": "LLM non disponibile"}
        
        try:
            # Recupera dati per diversi intervalli
            intervals = ["1h", "4h", "1d"]
            data = {}
            
            for interval in intervals:
                data[interval] = self.db_manager.get_crypto_data(symbol, interval, 100)
            
            # Recupera notizie correlate
            news = self.db_manager.get_news_data(limit=20, asset=symbol)
            
            # Analisi tecnica
            results = {}
            for interval, interval_data in data.items():
                results[interval] = self.trend_detector.analyze_all_trends(interval_data)
            
            # Analisi LLM
            prompt = f"""
            Analizza i seguenti dati tecnici e notizie per {symbol} e fornisci un'analisi dettagliata.
            
            Dati tecnici:
            {json.dumps(results, indent=2)}
            
            Notizie correlate:
            {json.dumps([n.get('title', 'No title') for n in news], indent=2)}
            
            Fornisci:
            1. Riepilogo dell'andamento tecnico
            2. Identificazione dei livelli chiave di supporto e resistenza
            3. Correlazione con le notizie
            4. Previsione a breve termine
            """
            
            system_message = f"Sei un analista finanziario esperto specializzato in criptovalute, in particolare {symbol}."
            
            analysis = self.llm_analyzer._call_llm(prompt, system_message)
            
            return {
                "symbol": symbol,
                "technical_analysis": results,
                "news": news,
                "llm_analysis": analysis
            }
        except Exception as e:
            logger.error(f"Errore nell'analisi specifica per {symbol}: {str(e)}")
            return {"error": str(e)}


def main():
    """Funzione principale per l'esecuzione dell'applicazione."""
    parser = argparse.ArgumentParser(description='MarketMover Radar - Monitoraggio mercati crypto e notizie economiche')
    parser.add_argument('--config', help='Percorso al file di configurazione')
    parser.add_argument('--no-websockets', action='store_true', help='Disabilita i WebSocket')
    parser.add_argument('--no-scheduling', action='store_true', help='Disabilita la pianificazione automatica')
    
    args = parser.parse_args()
    
    app = MarketMoverRadar(
        config_file=args.config,
        enable_websockets=not args.no_websockets,
        enable_scheduling=not args.no_scheduling
    )
    
    try:
        app.start()
        
        # Mantieni in esecuzione il programma principale
        logger.info("MarketMover Radar in esecuzione. Premi Ctrl+C per uscire.")
        while app.running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interruzione richiesta dall'utente")
    finally:
        app.stop()


if __name__ == "__main__":
    main()
