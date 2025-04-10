"""
Modulo per la generazione di report narrativi e dashboard.
"""
import json
import os
import re
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any, Optional
from loguru import logger

from visualization.chart_generator import ChartGenerator


class ReportBuilder:
    """Classe per la generazione di report narrativi e dashboard."""
    
    def __init__(self, output_dir: str = 'reports'):
        """
        Inizializza il builder di report.
        
        Args:
            output_dir: Directory di output per i report
        """
        self.output_dir = output_dir
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """Assicura che la directory di output esista."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_html_report(self, 
                           title: str,
                           content: str,
                           charts: List[Dict[str, Any]],
                           metadata: Dict[str, Any] = None) -> str:
        """
        Genera un report HTML con testo narrativo e grafici interattivi.
        
        Args:
            title: Titolo del report
            content: Contenuto testuale del report
            charts: Lista di grafici da includere
            metadata: Metadati aggiuntivi
            
        Returns:
            Percorso del file HTML generato
        """
        # Formatta la data corrente
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        # Pulisci il titolo per il nome del file
        clean_title = re.sub(r'[^\w\s-]', '', title.lower())
        clean_title = re.sub(r'[\s-]+', '-', clean_title)
        
        # Crea il nome file
        filename = f"{date_str}_{clean_title}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        # Formatta i metadati
        if metadata is None:
            metadata = {}
        
        metadata_html = ""
        if metadata:
            metadata_html = "<div class='metadata'><h3>Metadati del Report</h3><ul>"
            for key, value in metadata.items():
                if key != 'price_data' and key != 'market_trends' and key != 'news_themes':
                    if isinstance(value, list):
                        metadata_html += f"<li><strong>{key}:</strong> <ul>"
                        for item in value:
                            if isinstance(item, dict):
                                metadata_html += "<li>" + ", ".join([f"{k}: {v}" for k, v in item.items()]) + "</li>"
                            else:
                                metadata_html += f"<li>{item}</li>"
                        metadata_html += "</ul></li>"
                    else:
                        metadata_html += f"<li><strong>{key}:</strong> {value}</li>"
            metadata_html += "</ul></div>"
        
        # Converti markdown in HTML
        html_content = content.replace('\n', '<br>')
        
        # Aggiungi sezioni per i trend
        market_trends_html = ""
        if 'market_trends' in metadata and metadata['market_trends']:
            market_trends_html = "<div class='market-trends'><h3>Trend di Mercato</h3><ul>"
            for trend in metadata['market_trends']:
                confidence = trend.get('confidence', 0) * 100
                trend_class = "neutral"
                if trend.get('direction') == 'positive':
                    trend_class = "positive"
                elif trend.get('direction') == 'negative':
                    trend_class = "negative"
                
                market_trends_html += f"<li class='{trend_class}'><strong>{trend.get('trend', '')}</strong> " + \
                                     f"(Confidenza: {confidence:.1f}%, Asset: {', '.join(trend.get('assets', []))})</li>"
            market_trends_html += "</ul></div>"
        
        news_themes_html = ""
        if 'news_themes' in metadata and metadata['news_themes']:
            news_themes_html = "<div class='news-themes'><h3>Temi dalle Notizie</h3><ul>"
            for theme in metadata['news_themes']:
                frequency = theme.get('frequency', 0) * 100
                news_themes_html += f"<li><strong>{theme.get('theme', '')}</strong> " + \
                                   f"(Frequenza: {frequency:.1f}%, Asset: {', '.join(theme.get('assets', []))})</li>"
            news_themes_html += "</ul></div>"
        
        # Prepara i div per i grafici
        charts_html = ""
        plotly_dependencies = ""
        
        if charts:
            # Aggiungi dipendenze Plotly
            plotly_dependencies = """
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            """
            
            for i, chart in enumerate(charts):
                chart_id = chart.get('id', f'chart_{i}')
                chart_type = chart.get('type', 'plotly')
                
                if chart_type == 'plotly':
                    chart_json = chart.get('chart_json', '{}')
                    chart_options = json.dumps(chart.get('options', {}))
                    
                    charts_html += f"""
                    <div class="chart-container">
                        <div id="{chart_id}" class="chart"></div>
                        <script>
                            var plotData = {chart_json};
                            var plotOptions = {chart_options};
                            Plotly.newPlot('{chart_id}', plotData.data, plotData.layout, plotOptions);
                        </script>
                    </div>
                    """
        
        # Genera l'HTML completo
        html = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            {plotly_dependencies}
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .header {{
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 30px;
                }}
                .timestamp {{
                    color: #7f8c8d;
                    font-size: 0.9em;
                    margin-bottom: 20px;
                }}
                .content {{
                    margin-bottom: 30px;
                }}
                .chart-container {{
                    margin: 30px 0;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 15px;
                    background-color: #f9f9f9;
                }}
                .chart {{
                    width: 100%;
                    height: 500px;
                }}
                .metadata, .market-trends, .news-themes {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .positive {{
                    color: #27ae60;
                }}
                .negative {{
                    color: #c0392b;
                }}
                .neutral {{
                    color: #7f8c8d;
                }}
                .footer {{
                    margin-top: 50px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #7f8c8d;
                    border-top: 1px solid #e0e0e0;
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <div class="timestamp">Generato il {date_str} alle {time_str}</div>
            </div>
            
            <div class="content">
                {html_content}
            </div>
            
            {market_trends_html}
            {news_themes_html}
            
            {charts_html}
            
            {metadata_html}
            
            <div class="footer">
                <p>MarketMover Radar - Report generato automaticamente</p>
            </div>
        </body>
        </html>
        """
        
        # Scrivi il file HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Report HTML generato: {filepath}")
        return filepath

    def generate_dashboard(self, 
                         market_data: Dict[str, Any],
                         news_data: List[Dict[str, Any]],
                         analysis_results: Dict[str, Any]) -> str:
        """
        Genera un dashboard completo con dati di mercato, notizie e analisi.
        
        Args:
            market_data: Dati di mercato
            news_data: Dati di notizie
            analysis_results: Risultati dell'analisi
            
        Returns:
            Percorso del file dashboard
        """
        chart_generator = ChartGenerator()
        charts = []
        
        # 1. Crea grafici a candele per ogni asset
        for symbol, data in market_data.items():
            if data:
                candle_chart = chart_generator.create_candlestick_chart(
                    data, 
                    title=f"{symbol}/USD - Andamento Prezzo"
                )
                charts.append(candle_chart)
        
        # 2. Crea grafico di confronto tra asset
        comparison_chart = chart_generator.create_multi_asset_comparison(
            market_data,
            title="Confronto Performance Asset (Base 100)"
        )
        charts.append(comparison_chart)
        
        # 3. Crea matrice di correlazione
        correlation_chart = chart_generator.create_correlation_matrix(
            market_data,
            title="Matrice di Correlazione tra Asset"
        )
        charts.append(correlation_chart)
        
        # 4. Crea grafico di sentiment delle notizie
        sentiment_chart = chart_generator.create_news_sentiment_chart(
            news_data,
            title="Analisi del Sentiment delle Notizie"
        )
        charts.append(sentiment_chart)
        
        # Genera il report con i grafici
        title = analysis_results.get('title', "Analisi del Mercato Crypto")
        content = analysis_results.get('report', "Nessuna analisi disponibile")
        
        return self.generate_html_report(
            title=title,
            content=content,
            charts=charts,
            metadata=analysis_results
        )

    def generate_daily_report(self,
                           market_data: Dict[str, Any],
                           news_data: List[Dict[str, Any]],
                           analysis_results: Dict[str, Any]) -> str:
        """
        Genera un report giornaliero sintetico.
        
        Args:
            market_data: Dati di mercato
            news_data: Dati di notizie
            analysis_results: Risultati dell'analisi
            
        Returns:
            Percorso del file report
        """
        chart_generator = ChartGenerator()
        charts = []
        
        # 1. Crea un grafico di confronto tra i primi 5 asset
        top_assets = {}
        for symbol, data in list(market_data.items())[:5]:
            if data:
                top_assets[symbol] = data
        
        comparison_chart = chart_generator.create_multi_asset_comparison(
            top_assets,
            title="Top 5 Asset - Performance"
        )
        charts.append(comparison_chart)
        
        # 2. Crea grafico di sentiment delle notizie
        sentiment_chart = chart_generator.create_news_sentiment_chart(
            news_data[:30],  # Limita alle ultime 30 notizie
            title="Sentiment delle Notizie Recenti"
        )
        charts.append(sentiment_chart)
        
        # Genera il report con i grafici
        title = f"Report Giornaliero Crypto - {datetime.now().strftime('%d/%m/%Y')}"
        
        # Estrai il riepilogo dall'analisi completa
        summary = analysis_results.get('summary', "Nessun riepilogo disponibile")
        
        # Aggiungi una sezione con le notizie più rilevanti
        high_impact_news = analysis_results.get('high_impact_news', [])
        news_section = "\n\n## Notizie ad Alto Impatto\n\n"
        
        if high_impact_news:
            for news in high_impact_news[:5]:
                news_section += f"- **{news.get('title', 'N/A')}** - Impatto: {news.get('impact_score', 0):.2f}\n"
        else:
            news_section += "Nessuna notizia ad alto impatto identificata.\n"
        
        # Combina il contenuto
        content = f"## Riepilogo\n\n{summary}{news_section}"
        
        return self.generate_html_report(
            title=title,
            content=content,
            charts=charts,
            metadata=analysis_results
        )
