"""
Modulo per il rilevamento di trend nei dati di mercato.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger


class TrendDetector:
    """Classe per il rilevamento di trend nei dati di mercato."""
    
    def __init__(self):
        """Inizializza il rilevatore di trend."""
        pass
    
    def detect_price_trends(self, data: List[Dict[str, Any]], window: int = 5) -> Dict[str, Any]:
        """
        Rileva trend di prezzo semplici.
        
        Args:
            data: Lista di dati OHLC
            window: Dimensione della finestra per medie mobili
            
        Returns:
            Dizionario con trend rilevati
        """
        if not data or len(data) < window:
            return {"trend": "unknown", "strength": 0, "support": 0, "resistance": 0}
        
        # Converti in DataFrame per analisi più semplice
        df = pd.DataFrame(data)
        
        # Assicurati che ci siano le colonne necessarie
        required_cols = ['close', 'high', 'low']
        if not all(col in df.columns for col in required_cols):
            return {"trend": "unknown", "strength": 0, "support": 0, "resistance": 0}
        
        # Calcola la media mobile
        df['sma'] = df['close'].rolling(window=window).mean()
        
        # Calcola la tendenza della SMA
        if len(df) > window:
            last_sma = df['sma'].iloc[-1]
            prev_sma = df['sma'].iloc[-window]
            
            if last_sma > prev_sma:
                trend = "uptrend"
                strength = min(1.0, (last_sma - prev_sma) / prev_sma * 5) if prev_sma > 0 else 0.5
            elif last_sma < prev_sma:
                trend = "downtrend"
                strength = min(1.0, (prev_sma - last_sma) / prev_sma * 5) if prev_sma > 0 else 0.5
            else:
                trend = "sideways"
                strength = 0.1
        else:
            trend = "unknown"
            strength = 0
        
        # Identificazione di supporti e resistenze
        recent_data = df.tail(20)  # Usa gli ultimi 20 punti
        
        # Resistenza: massimo recente
        resistance = recent_data['high'].max()
        
        # Supporto: minimo recente
        support = recent_data['low'].min()
        
        # Calcola la distanza percentuale dal prezzo attuale
        last_close = df['close'].iloc[-1]
        
        resistance_distance = (resistance - last_close) / last_close * 100 if last_close > 0 else 0
        support_distance = (last_close - support) / last_close * 100 if last_close > 0 else 0
        
        return {
            "trend": trend,
            "strength": float(strength),
            "last_close": float(last_close),
            "support": float(support),
            "resistance": float(resistance),
            "support_distance": float(support_distance),
            "resistance_distance": float(resistance_distance)
        }
    
    def detect_volume_trends(self, data: List[Dict[str, Any]], window: int = 5) -> Dict[str, Any]:
        """
        Rileva trend di volume.
        
        Args:
            data: Lista di dati OHLC
            window: Dimensione della finestra per medie mobili
            
        Returns:
            Dizionario con trend di volume rilevati
        """
        if not data or len(data) < window or 'volume' not in data[0]:
            return {"trend": "unknown", "strength": 0}
        
        # Converti in DataFrame
        df = pd.DataFrame(data)
        
        # Calcola la media mobile del volume
        df['volume_sma'] = df['volume'].rolling(window=window).mean()
        
        # Calcola la tendenza del volume
        if len(df) > window:
            last_vol_sma = df['volume_sma'].iloc[-1]
            prev_vol_sma = df['volume_sma'].iloc[-window]
            
            if last_vol_sma > prev_vol_sma * 1.2:  # +20% di volume
                trend = "increasing"
                strength = min(1.0, (last_vol_sma - prev_vol_sma) / prev_vol_sma) if prev_vol_sma > 0 else 0.5
            elif last_vol_sma < prev_vol_sma * 0.8:  # -20% di volume
                trend = "decreasing"
                strength = min(1.0, (prev_vol_sma - last_vol_sma) / prev_vol_sma) if prev_vol_sma > 0 else 0.5
            else:
                trend = "stable"
                strength = 0.1
        else:
            trend = "unknown"
            strength = 0
        
        # Calcola il rapporto tra volume e variazione di prezzo
        price_changes = []
        volumes = []
        
        for i in range(1, len(df)):
            price_change = abs(df['close'].iloc[i] - df['close'].iloc[i-1])
            volume = df['volume'].iloc[i]
            
            if df['close'].iloc[i-1] > 0:
                price_changes.append(price_change / df['close'].iloc[i-1])
                volumes.append(volume)
        
        # Calcola correlazione tra variazione di prezzo e volume
        correlation = 0
        if len(price_changes) > 5 and len(volumes) > 5:
            correlation = np.corrcoef(price_changes, volumes)[0, 1]
            # Gestisci NaN
            if np.isnan(correlation):
                correlation = 0
        
        return {
            "trend": trend,
            "strength": float(strength),
            "avg_volume": float(df['volume'].mean()) if len(df) > 0 else 0,
            "price_volume_correlation": float(correlation)
        }
    
    def detect_momentum(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcola indicatori di momentum.
        
        Args:
            data: Lista di dati OHLC
            
        Returns:
            Dizionario con indicatori di momentum
        """
        if not data or len(data) < 14:
            return {"rsi": 0, "momentum": 0}
        
        # Converti in DataFrame
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp')  # Assicura l'ordine cronologico
        
        # Calcola RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calcola momentum (variazione percentuale su 10 periodi)
        momentum = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10] if df['close'].iloc[-10] > 0 else 0
        
        # Calcola MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        # Determina il trend di momentum
        momentum_trend = "neutral"
        if rsi.iloc[-1] > 70:
            momentum_trend = "overbought"
        elif rsi.iloc[-1] < 30:
            momentum_trend = "oversold"
        elif rsi.iloc[-1] > 50 and rsi.iloc[-2] <= 50:
            momentum_trend = "bullish_crossover"
        elif rsi.iloc[-1] < 50 and rsi.iloc[-2] >= 50:
            momentum_trend = "bearish_crossover"
        
        # Determina il trend MACD
        macd_trend = "neutral"
        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            macd_trend = "bullish_crossover"
        elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
            macd_trend = "bearish_crossover"
        elif macd.iloc[-1] > 0:
            macd_trend = "bullish"
        elif macd.iloc[-1] < 0:
            macd_trend = "bearish"
        
        return {
            "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
            "macd": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0,
            "macd_signal": float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else 0,
            "macd_histogram": float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0,
            "momentum": float(momentum),
            "momentum_trend": momentum_trend,
            "macd_trend": macd_trend
        }
    
    def detect_volatility(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcola metriche di volatilità.
        
        Args:
            data: Lista di dati OHLC
            
        Returns:
            Dizionario con metriche di volatilità
        """
        if not data or len(data) < 5:
            return {"volatility": 0, "atr": 0}
        
        # Converti in DataFrame
        df = pd.DataFrame(data)
        
        # Calcola la volatilità (deviazione standard dei rendimenti)
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * (252 ** 0.5)  # Annualizzata
        
        # Calcola l'ATR (Average True Range)
        df['hl'] = df['high'] - df['low']
        df['hc'] = abs(df['high'] - df['close'].shift(1))
        df['lc'] = abs(df['low'] - df['close'].shift(1))
        
        df['tr'] = df[['hl', 'hc', 'lc']].max(axis=1)
        atr = df['tr'].rolling(window=14).mean().iloc[-1]
        
        # Calcola Bollinger Bands
        sma20 = df['close'].rolling(window=20).mean().iloc[-1]
        std20 = df['close'].rolling(window=20).std().iloc[-1]
        
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)
        
        # Calcola la posizione del prezzo nelle bande
        last_close = df['close'].iloc[-1]
        bb_position = (last_close - lower_band) / (upper_band - lower_band) if (upper_band - lower_band) > 0 else 0.5
        
        # Determina il trend di volatilità
        recent_vol = df['tr'].rolling(window=5).mean().iloc[-1]
        older_vol = df['tr'].rolling(window=14).mean().iloc[-5] if len(df) >= 19 else recent_vol
        
        vol_trend = "stable"
        if recent_vol > older_vol * 1.2:
            vol_trend = "increasing"
        elif recent_vol < older_vol * 0.8:
            vol_trend = "decreasing"
        
        return {
            "volatility": float(volatility) if not pd.isna(volatility) else 0,
            "atr": float(atr) if not pd.isna(atr) else 0,
            "bollinger_width": float((upper_band - lower_band) / sma20) if sma20 > 0 else 0,
            "bollinger_position": float(bb_position),
            "volatility_trend": vol_trend
        }
    
    def analyze_all_trends(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analizza tutti i tipi di trend per un insieme di dati.
        
        Args:
            data: Lista di dati OHLC
            
        Returns:
            Dizionario con tutti i trend analizzati
        """
        price_trends = self.detect_price_trends(data)
        volume_trends = self.detect_volume_trends(data)
        momentum = self.detect_momentum(data)
        volatility = self.detect_volatility(data)
        
        # Combina tutti i risultati
        return {
            "price": price_trends,
            "volume": volume_trends,
            "momentum": momentum,
            "volatility": volatility
        }
