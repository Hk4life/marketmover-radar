"""
Modulo per la generazione di grafici interattivi.
"""
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger


class ChartGenerator:
    """Classe per la generazione di grafici basati sui dati di mercato."""
    
    @staticmethod
    def create_candlestick_chart(data: List[Dict[str, Any]], title: str = "Candlestick Chart") -> Dict[str, Any]:
        """
        Crea un grafico a candele interattivo.
        
        Args:
            data: Lista di dati OHLC
            title: Titolo del grafico
            
        Returns:
            Dizionario con il grafico JSON e opzioni
        """
        if not data:
            return {"error": "Nessun dato disponibile per il grafico"}
        
        # Crea dataframe
        df = pd.DataFrame(data)
        
        # Assicuriamoci che tutte le colonne necessarie siano presenti
        required_cols = ['timestamp', 'open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            # Aggiungi colonne mancanti con valori predefiniti
            for col in required_cols:
                if col not in df.columns:
                    if col == 'timestamp':
                        df[col] = range(len(df))
                    else:
                        df[col] = df.get('close', 0)
        
        # Converti timestamp in datetime
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Crea subplot con due grafici
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                         vertical_spacing=0.02, 
                         row_heights=[0.7, 0.3],
                         subplot_titles=(title, 'Volume'))
        
        # Aggiungi candlestick
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="OHLC"
            ),
            row=1, col=1
        )
        
        # Aggiungi SMA 20
        if len(df) >= 20:
            df['sma20'] = df['close'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['sma20'],
                    line=dict(color='blue', width=1),
                    name="SMA 20"
                ),
                row=1, col=1
            )
        
        # Aggiungi SMA 50
        if len(df) >= 50:
            df['sma50'] = df['close'].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['sma50'],
                    line=dict(color='orange', width=1),
                    name="SMA 50"
                ),
                row=1, col=1
            )
        
        # Aggiungi volume
        if 'volume' in df.columns:
            colors = ['red' if row['open'] > row['close'] else 'green' for _, row in df.iterrows()]
            fig.add_trace(
                go.Bar(
                    x=df['date'],
                    y=df['volume'],
                    marker_color=colors,
                    name="Volume"
                ),
                row=2, col=1
            )
        
        # Personalizza layout
        fig.update_layout(
            title=title,
            yaxis_title='Price',
            xaxis_rangeslider_visible=False,
            height=600,
            template='plotly_white'
        )
        
        fig.update_xaxes(
            rangeslider_visible=False,
            rangebreaks=[
                dict(bounds=["sat", "mon"])  # Nascondi weekend
            ]
        )
        
        return {
            "id": "candlestick_chart",
            "chart_json": fig.to_json(),
            "type": "plotly",
            "options": {
                "responsive": True,
                "displayModeBar": True,
                "displaylogo": False
            }
        }
    
    @staticmethod
    def create_multi_asset_comparison(data: Dict[str, List[Dict[str, Any]]], title: str = "Multi-Asset Comparison") -> Dict[str, Any]:
        """
        Crea un grafico di confronto per più asset.
        
        Args:
            data: Dizionario con dati per diversi asset
            title: Titolo del grafico
            
        Returns:
            Dizionario con il grafico JSON e opzioni
        """
        if not data:
            return {"error": "Nessun dato disponibile per il grafico"}
        
        # Crea figura
        fig = go.Figure()
        
        # Normalizza i dati per confronto (base 100)
        normalized_data = {}
        start_date = None
        
        for asset, asset_data in data.items():
            if not asset_data:
                continue
            
            # Crea dataframe
            df = pd.DataFrame(asset_data)
            
            # Controlla colonne necessarie
            if 'timestamp' not in df.columns or 'close' not in df.columns:
                continue
            
            # Converti timestamp in datetime
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Ordina per data
            df = df.sort_values('date')
            
            # Normalizza al primo valore (base 100)
            first_value = df['close'].iloc[0]
            df['normalized'] = (df['close'] / first_value) * 100
            
            # Aggiungi al grafico
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['normalized'],
                    mode='lines',
                    name=asset
                )
            )
            
            # Registra la prima data per allineamento
            if start_date is None or df['date'].min() < start_date:
                start_date = df['date'].min()
        
        # Personalizza layout
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Normalized Price (Base 100)',
            height=500,
            template='plotly_white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return {
            "id": "multi_asset_chart",
            "chart_json": fig.to_json(),
            "type": "plotly",
            "options": {
                "responsive": True,
                "displayModeBar": True,
                "displaylogo": False
            }
        }
    
    @staticmethod
    def create_market_heatmap(data: Dict[str, Dict[str, Any]], title: str = "Market Heatmap") -> Dict[str, Any]:
        """
        Crea una mappa di calore del mercato basata sulle variazioni di prezzo.
        
        Args:
            data: Dizionario con dati per diversi asset
            title: Titolo del grafico
            
        Returns:
            Dizionario con il grafico JSON e opzioni
        """
        if not data:
            return {"error": "Nessun dato disponibile per il grafico"}
        
        # Prepara i dati per la mappa di calore
        assets = []
        changes = []
        prices = []
        market_caps = []
        
        for asset, asset_data in data.items():
            # Verifica se ci sono dati di mercato disponibili
            if not asset_data or 'price_data' not in asset_data or not asset_data['price_data']:
                continue
            
            price_data = asset_data['price_data']
            
            # Ottieni il prezzo corrente e la variazione
            current_price = price_data.get('close', 0)
            price_change = price_data.get('price_change_percentage_24h', 0)
            market_cap = price_data.get('market_cap', 1000000)  # Valore predefinito
            
            assets.append(asset)
            changes.append(price_change)
            prices.append(current_price)
            market_caps.append(market_cap)
        
        if not assets:
            return {"error": "Dati insufficienti per la mappa di calore"}
        
        # Normalizza le capitalizzazioni di mercato per dimensioni
        min_size = 20
        max_size = 100
        
        if market_caps and max(market_caps) > min(market_caps):
            normalized_sizes = [(cap - min(market_caps)) / (max(market_caps) - min(market_caps)) * (max_size - min_size) + min_size for cap in market_caps]
        else:
            normalized_sizes = [50] * len(market_caps)
        
        # Crea la mappa di calore
        fig = go.Figure()
        
        # Aggiungi rettangoli colorati
        for i, asset in enumerate(assets):
            change = changes[i]
            price = prices[i]
            size = normalized_sizes[i]
            
            # Scala di colore: rosso per negativo, verde per positivo
            color = f"rgb({min(255, int(255 * min(1, abs(change) / 10 if change < 0 else 0)))}, {min(255, int(255 * min(1, change / 10 if change > 0 else 0)))}, 0)"
            
            fig.add_trace(
                go.Scatter(
                    x=[0],
                    y=[0],
                    mode='markers',
                    marker=dict(
                        size=size,
                        color=color,
                        opacity=0.8
                    ),
                    text=f"{asset}: ${price:.2f} ({change:+.2f}%)",
                    name=asset
                )
            )
        
        # Personalizza layout
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=False,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                visible=False
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                visible=False
            )
        )
        
        return {
            "id": "market_heatmap",
            "chart_json": fig.to_json(),
            "type": "plotly",
            "options": {
                "responsive": True,
                "displayModeBar": False,
                "displaylogo": False
            }
        }
    
    @staticmethod
    def create_news_sentiment_chart(data: List[Dict[str, Any]], title: str = "News Sentiment Analysis") -> Dict[str, Any]:
        """
        Crea un grafico di analisi del sentiment delle notizie.
        
        Args:
            data: Lista di notizie con dati di sentiment
            title: Titolo del grafico
            
        Returns:
            Dizionario con il grafico JSON e opzioni
        """
        if not data:
            return {"error": "Nessun dato disponibile per il grafico"}
        
        # Prepara i dati
        sources = []
        sentiments = []
        titles = []
        timestamps = []
        
        for news in data:
            # Estrai i dati necessari
            sentiment = news.get('extracted_entities', {}).get('sentiment_score', 0)
            source = news.get('source', 'Unknown')
            title_text = news.get('title', 'No title')
            timestamp = news.get('timestamp', 0)
            
            sources.append(source)
            sentiments.append(sentiment)
            titles.append(title_text)
            timestamps.append(timestamp)
        
        # Converti timestamp in datetime
        dates = pd.to_datetime(timestamps, unit='s')
        
        # Crea dataframe
        df = pd.DataFrame({
            'date': dates,
            'source': sources,
            'sentiment': sentiments,
            'title': titles
        })
        
        # Ordina per data
        df = df.sort_values('date')
        
        # Calcola media mobile del sentiment
        df['sentiment_ma'] = df['sentiment'].rolling(window=10).mean()
        
        # Crea il grafico
        fig = go.Figure()
        
        # Aggiungi scatter plot di sentiment
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['sentiment'],
                mode='markers',
                name='News Sentiment',
                marker=dict(
                    size=10,
                    color=df['sentiment'],
                    colorscale='RdYlGn',
                    cmin=-1,
                    cmax=1,
                    showscale=True,
                    colorbar=dict(
                        title='Sentiment'
                    )
                ),
                text=df['title'],
                hovertemplate='<b>%{text}</b><br>Source: %{customdata}<br>Sentiment: %{y:.2f}<br>Date: %{x}<extra></extra>',
                customdata=df['source']
            )
        )
        
        # Aggiungi linea di trend
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['sentiment_ma'],
                mode='lines',
                name='Sentiment Trend',
                line=dict(
                    color='black',
                    width=2
                )
            )
        )
        
        # Aggiungi linee di riferimento
        fig.add_shape(
            type='line',
            x0=df['date'].min(),
            x1=df['date'].max(),
            y0=0,
            y1=0,
            line=dict(
                color='gray',
                width=1,
                dash='dash'
            )
        )
        
        # Personalizza layout
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Sentiment (-1 to +1)',
            height=500,
            template='plotly_white',
            yaxis=dict(
                range=[-1.1, 1.1]
            )
        )
        
        return {
            "id": "news_sentiment_chart",
            "chart_json": fig.to_json(),
            "type": "plotly",
            "options": {
                "responsive": True,
                "displayModeBar": True,
                "displaylogo": False
            }
        }
    
    @staticmethod
    def create_correlation_matrix(data: Dict[str, List[Dict[str, Any]]], title: str = "Asset Correlation Matrix") -> Dict[str, Any]:
        """
        Crea una matrice di correlazione tra asset.
        
        Args:
            data: Dizionario con dati per diversi asset
            title: Titolo del grafico
            
        Returns:
            Dizionario con il grafico JSON e opzioni
        """
        if not data or len(data) < 2:
            return {"error": "Dati insufficienti per la matrice di correlazione"}
        
        # Prepara DataFrame per le correlazioni
        price_data = {}
        
        for asset, asset_data in data.items():
            if not asset_data:
                continue
            
            # Crea dataframe
            df = pd.DataFrame(asset_data)
            
            # Controlla colonne necessarie
            if 'timestamp' not in df.columns or 'close' not in df.columns:
                continue
            
            # Converti timestamp in datetime e imposta come indice
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.set_index('date')
            
            # Aggiungi al dizionario dei prezzi
            price_data[asset] = df['close']
        
        if len(price_data) < 2:
            return {"error": "Dati insufficienti per la matrice di correlazione"}
        
        # Crea DataFrame combinato
        combined_df = pd.DataFrame(price_data)
        
        # Calcola la matrice di correlazione
        corr_matrix = combined_df.corr()
        
        # Crea la heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu_r',
            zmin=-1,
            zmax=1,
            text=[[f"{val:.2f}" for val in row] for row in corr_matrix.values],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        # Personalizza layout
        fig.update_layout(
            title=title,
            height=500,
            template='plotly_white',
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            xaxis_tickangle=-45
        )
        
        return {
            "id": "correlation_matrix",
            "chart_json": fig.to_json(),
            "type": "plotly",
            "options": {
                "responsive": True,
                "displayModeBar": True,
                "displaylogo": False
            }
        }
