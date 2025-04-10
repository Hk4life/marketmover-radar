"""
Modulo per l'analisi dei dati utilizzando LM Studio.
"""
import json
from typing import Dict, List, Any, Optional
import requests
from loguru import logger

from config import LM_STUDIO_URL


class LLMAnalyzer:
    """Classe per l'analisi di dati crypto e notizie tramite LLM."""
    
    def __init__(self, server_url: str = LM_STUDIO_URL):
        """
        Inizializza l'analizzatore LLM.
        
        Args:
            server_url: URL del server LM Studio
        """
        self.server_url = server_url
        self.test_connection()
    
    def test_connection(self):
        """Testa la connessione a LM Studio."""
        try:
            response = requests.get(f"{self.server_url}/models")
            if response.status_code == 200:
                models = response.json().get('data', [])
                if models:
                    model_names = [model.get('id') for model in models]
                    logger.info(f"Connessione a LM Studio stabilita. Modelli disponibili: {model_names}")
                else:
                    logger.warning("Connessione a LM Studio stabilita, ma nessun modello disponibile.")
            else:
                logger.error(f"Errore nella connessione a LM Studio: {response.status_code}")
                logger.error(f"Risposta: {response.text}")
        except Exception as e:
            logger.error(f"Errore nella connessione a LM Studio: {str(e)}")
            raise
    
    def _call_llm(self, prompt: str, system_message: str = "", temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Chiama il modello LLM tramite LM Studio.
        
        Args:
            prompt: Testo prompt
            system_message: Messaggio di sistema
            temperature: Temperatura di generazione
            max_tokens: Numero massimo di token da generare
            
        Returns:
            Testo generato dal modello
        """
        try:
            payload = {
                "model": "local-model",  # Usa il modello attualmente caricato
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                f"{self.server_url}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content']
                else:
                    logger.error("Risposta LLM non valida")
                    return ""
            else:
                logger.error(f"Errore nella chiamata LLM: {response.status_code}")
                logger.error(f"Risposta: {response.text}")
                return f"Errore nella chiamata LLM: {response.status_code}"
        except Exception as e:
            logger.error(f"Errore nella chiamata LLM: {str(e)}")
            return f"Errore nella chiamata LLM: {str(e)}"
    
    def analyze_market_trends(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizza i trend di mercato usando LLM.
        
        Args:
            market_data: Dati di mercato
            
        Returns:
            Risultato dell'analisi
        """
        # Prepara un riepilogo dei dati di mercato per il prompt
        market_summary = []
        
        for symbol, data in market_data.items():
            if not data:
                continue
            
            # Estrai dati rilevanti
            current_price = data[-1].get('close', 0) if data else 0
            prev_price = data[0].get('close', 0) if data else 0
            price_change = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
            
            high = max([candle.get('high', 0) for candle in data]) if data else 0
            low = min([candle.get('low', 0) for candle in data]) if data else 0
            
            market_summary.append(
                f"{symbol}: Prezzo attuale ${current_price:.2f}, Variazione {price_change:.2f}%, "
                f"Max ${high:.2f}, Min ${low:.2f}"
            )
        
        # Crea prompt per LLM
        prompt = f"""
        Sei un analista finanziario esperto di criptovalute. Analizza i seguenti dati di mercato e identifica trend significativi, pattern e correlazioni.
        
        Dati di mercato:
        {chr(10).join(market_summary)}
        
        Fornisci un'analisi che includa:
        1. Principali trend identificati
        2. Correlazioni tra asset
        3. Asset con performance migliore e peggiore
        4. Previsione dell'andamento a breve termine (24-48 ore)
        5. Segnali tecnici rilevanti
        
        Sii specifico, basandoti sui dati forniti e sul contesto attuale del mercato crypto.
        """
        
        system_message = """
        Sei un analista finanziario esperto specializzato in mercati crypto. Fornisci analisi approfondite, basate sui dati e con tono professionale.
        Non esagerare nelle previsioni e indica sempre il livello di incertezza. Identifica pattern reali nei dati senza sovrinterpretare.
        """
        
        # Chiama LLM per l'analisi
        analysis_text = self._call_llm(prompt, system_message)
        
        # Estrai insight strutturati
        trends = []
        correlations = []
        top_performers = []
        worst_performers = []
        
        # Estrai trend usando un secondo prompt
        trends_prompt = f"""
        Dai seguenti dati di mercato e dalla seguente analisi, estrai una lista di trend specifici in formato JSON:
        
        Dati di mercato:
        {chr(10).join(market_summary)}
        
        Analisi:
        {analysis_text}
        
        Restituisci un array JSON di trend nel formato:
        [
            {{"trend": "BTC in fase di consolidamento", "confidence": 0.85, "assets": ["BTC"], "direction": "neutral"}},
            {{"trend": "Forte correlazione tra ETH e SOL", "confidence": 0.75, "assets": ["ETH", "SOL"], "direction": "positive"}}
        ]
        
        Considera solo trend significativi e assegna un livello di confidenza realistico (0-1).
        La direzione può essere "positive", "negative" o "neutral".
        """
        
        try:
            trends_json = self._call_llm(trends_prompt)
            
            # Estrai JSON dalla risposta
            json_start = trends_json.find('[')
            json_end = trends_json.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = trends_json[json_start:json_end]
                trends = json.loads(json_str)
            else:
                logger.warning("Formato JSON non trovato nella risposta sui trend")
        except Exception as e:
            logger.error(f"Errore nell'estrazione dei trend: {str(e)}")
        
        return {
            "analysis": analysis_text,
            "trends": trends,
            "correlations": correlations,
            "top_performers": top_performers,
            "worst_performers": worst_performers
        }
    
    def analyze_news(self, news_data: List[Dict[str, Any]], limit: int = 30) -> Dict[str, Any]:
        """
        Analizza le notizie usando LLM.
        
        Args:
            news_data: Lista di articoli di notizie
            limit: Numero massimo di notizie da analizzare
            
        Returns:
            Risultato dell'analisi
        """
        # Limita il numero di notizie per evitare token troppo lunghi
        news_to_analyze = news_data[:limit]
        
        # Prepara un riepilogo delle notizie per il prompt
        news_summary = []
        
        for i, news in enumerate(news_to_analyze):
            title = news.get('title', 'No title')
            source = news.get('source', 'Unknown')
            sentiment_score = news.get('extracted_entities', {}).get('sentiment_score', 0)
            
            # Formatta il sentiment come stringa
            sentiment_str = "neutral"
            if sentiment_score > 0.2:
                sentiment_str = "positive"
            elif sentiment_score < -0.2:
                sentiment_str = "negative"
            
            # Aggiungi gli asset correlati
            related_assets = news.get('related_assets', [])
            assets_str = ", ".join(related_assets) if related_assets else "N/A"
            
            news_summary.append(
                f"{i+1}. {title} (Fonte: {source}, Sentiment: {sentiment_str}, Asset: {assets_str})"
            )
        
        # Crea prompt per LLM
        prompt = f"""
        Sei un analista di notizie finanziarie specializzato in criptovalute. Analizza le seguenti notizie recenti e identifica temi ricorrenti, sentiment di mercato e potenziali impatti sui prezzi.
        
        Notizie recenti:
        {chr(10).join(news_summary)}
        
        Fornisci un'analisi che includa:
        1. Principali temi emergenti
        2. Sentiment generale del mercato basato sulle notizie
        3. Notizie ad alto impatto che potrebbero influenzare significativamente i prezzi
        4. Asset più menzionati e contesto delle menzioni
        5. Eventi normativi o macroeconomici significativi
        
        Sii specifico, basandoti sulle notizie fornite e sul contesto attuale del mercato crypto.
        """
        
        system_message = """
        Sei un analista di notizie finanziarie esperto specializzato in mercati crypto. Fornisci analisi approfondite, basate sulle notizie con tono professionale.
        Identifica temi reali senza sovrinterpretare e distingui tra fatti verificati e speculazioni. Mantieni un approccio equilibrato e obiettivo.
        """
        
        # Chiama LLM per l'analisi
        analysis_text = self._call_llm(prompt, system_message)
        
        # Estrai insight strutturati
        key_themes_prompt = f"""
        Dalle seguenti notizie e dalla seguente analisi, estrai:
        1. Un elenco di temi chiave in formato JSON
        2. Un punteggio di sentiment generale da -1 (molto negativo) a 1 (molto positivo)
        3. Una lista delle notizie ad alto impatto con relativo punteggio di impatto
        
        Notizie:
        {chr(10).join(news_summary[:10])}
        
        Analisi:
        {analysis_text}
        
        Restituisci in formato JSON:
        {{
            "themes": [
                {{"theme": "Adozione istituzionale", "frequency": 0.75, "assets": ["BTC", "ETH"]}},
                {{"theme": "Regolamentazione", "frequency": 0.4, "assets": ["XRP", "BNB"]}}
            ],
            "overall_sentiment": 0.2,
            "high_impact_news": [
                {{"title": "SEC approva ETF Bitcoin", "impact_score": 0.9, "assets": ["BTC"]}}
            ]
        }}
        """
        
        insights = {
            "themes": [],
            "overall_sentiment": 0,
            "high_impact_news": []
        }
        
        try:
            insights_json = self._call_llm(key_themes_prompt)
            
            # Estrai JSON dalla risposta
            json_start = insights_json.find('{')
            json_end = insights_json.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = insights_json[json_start:json_end]
                insights = json.loads(json_str)
            else:
                logger.warning("Formato JSON non trovato nella risposta sugli insights")
        except Exception as e:
            logger.error(f"Errore nell'estrazione degli insights: {str(e)}")
        
        return {
            "analysis": analysis_text,
            "themes": insights.get("themes", []),
            "sentiment": insights.get("overall_sentiment", 0),
            "high_impact_news": insights.get("high_impact_news", [])
        }
    
    def generate_comprehensive_report(self, 
                                    market_analysis: Dict[str, Any],
                                    news_analysis: Dict[str, Any],
                                    market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un report completo combinando analisi di mercato e notizie.
        
        Args:
            market_analysis: Risultato dell'analisi di mercato
            news_analysis: Risultato dell'analisi delle notizie
            market_data: Dati di mercato originali
            
        Returns:
            Report completo
        """
        # Estrai tendenze di mercato e notizie
        market_trends = market_analysis.get("trends", [])
        news_themes = news_analysis.get("themes", [])
        
        # Crea un riepilogo dei dati principali
        symbols = list(market_data.keys())
        price_summary = []
        
        for symbol in symbols:
            data = market_data.get(symbol, [])
            if not data:
                continue
            
            current_price = data[-1].get('close', 0) if data else 0
            prev_price = data[0].get('close', 0) if data else 0
            price_change = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
            
            price_summary.append(f"{symbol}: ${current_price:.2f} ({price_change:+.2f}%)")
        
        # Crea prompt per LLM
        prompt = f"""
        Sei un analista finanziario senior specializzato in criptovalute. Compila un report di mercato completo basato sulle seguenti analisi di mercato e notizie.
        
        Riepilogo prezzi attuali:
        {chr(10).join(price_summary)}
        
        Analisi tecnica di mercato:
        {market_analysis.get('analysis', 'Nessuna analisi disponibile')}
        
        Analisi delle notizie:
        {news_analysis.get('analysis', 'Nessuna analisi disponibile')}
        
        Trend di mercato identificati:
        {json.dumps(market_trends, indent=2)}
        
        Temi principali dalle notizie:
        {json.dumps(news_themes, indent=2)}
        
        Sentiment generale del mercato: {news_analysis.get('sentiment', 0)}
        
        Genera un report completo che include:
        1. Titolo accattivante e riassuntivo della situazione attuale
        2. Riepilogo esecutivo (massimo 3 paragrafi)
        3. Analisi tecnica di mercato approfondita
        4. Impatto delle notizie recenti sui prezzi
        5. Correlazioni tra trend tecnici e temi delle notizie
        6. Previsioni a breve termine (24-72 ore)
        7. Asset da monitorare con particolare attenzione
        8. Consigli strategici (senza raccomandazioni di investimento specifiche)
        9. Conclusioni
        
        Il report deve essere scritto in stile professionale ma accessibile, con una struttura chiara e comprensibile.
        """
        
        system_message = """
        Sei un analista finanziario esperto che produce report di mercato crypto di alta qualità.
        I tuoi report sono noti per la profondità di analisi, la chiarezza espositiva e l'equilibrio tra dati tecnici e contestualizzazione.
        Evita di fare previsioni troppo precise su prezzi futuri, ma offri indicazioni di trend generali con i relativi livelli di confidenza.
        """
        
        # Chiama LLM per la generazione del report
        report_text = self._call_llm(prompt, system_message, temperature=0.5, max_tokens=3000)
        
        # Estrai titolo e riepilogo
        title = ""
        summary = ""
        
        lines = report_text.split('\n')
        if lines:
            # Cerca il titolo nelle prime righe
            for i, line in enumerate(lines[:5]):
                if line.strip() and not line.startswith('#'):
                    title = line.strip()
                    break
            
            # Cerca il riepilogo dopo il titolo
            summary_start = None
            summary_end = None
            
            for i, line in enumerate(lines):
                if 'riepilogo' in line.lower() or 'executive summary' in line.lower() or 'sommario' in line.lower():
                    summary_start = i + 1
                elif summary_start and not summary_end and (i > summary_start + 5) and (line.strip() == '' or any(keyword in line.lower() for keyword in ['analisi', 'impatto', 'mercato', 'tecnica'])):
                    summary_end = i
                    break
            
            if summary_start and summary_end:
                summary = '\n'.join(lines[summary_start:summary_end]).strip()
            elif summary_start:
                summary = '\n'.join(lines[summary_start:summary_start+3]).strip()
        
        # Generiamo anche gli approfondimenti specifici
        insights_prompt = f"""
        Dato il seguente report di mercato crypto, estrai:
        1. Una lista di asset da monitorare con relative motivazioni
        2. Una lista di rischi chiave nel breve termine
        3. Una lista di opportunità potenziali
        
        Report:
        {report_text}
        
        Restituisci in formato JSON:
        {{
            "assets_to_watch": [
                {{"asset": "BTC", "reason": "Test di supporto critico a $50,000", "sentiment": "cautious"}}
            ],
            "key_risks": [
                {{"risk": "Incertezza regolatoria negli USA", "impact": "high", "probability": "medium"}}
            ],
            "opportunities": [
                {{"opportunity": "Accumulo durante correzione", "assets": ["ETH", "SOL"], "timeframe": "short"}}
            ]
        }}
        """
        
        insights = {
            "assets_to_watch": [],
            "key_risks": [],
            "opportunities": []
        }
        
        try:
            insights_json = self._call_llm(insights_prompt)
            
            # Estrai JSON dalla risposta
            json_start = insights_json.find('{')
            json_end = insights_json.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = insights_json[json_start:json_end]
                insights = json.loads(json_str)
            else:
                logger.warning("Formato JSON non trovato nella risposta sugli insights specifici")
        except Exception as e:
            logger.error(f"Errore nell'estrazione degli insights specifici: {str(e)}")
        
        return {
            "title": title or "Analisi del Mercato Crypto",
            "summary": summary or "Riepilogo non disponibile",
            "report": report_text,
            "assets_to_watch": insights.get("assets_to_watch", []),
            "key_risks": insights.get("key_risks", []),
            "opportunities": insights.get("opportunities", []),
            "market_trends": market_trends,
            "news_themes": news_themes,
            "price_data": {symbol: market_data.get(symbol, [])[-1] if market_data.get(symbol) else {} for symbol in symbols}
        }
