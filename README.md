# MarketMover Radar

Un sistema avanzato per il monitoraggio in tempo reale dei mercati crypto e delle notizie economiche, con analisi basata su LLM tramite integrazione con LM Studio.

## Caratteristiche principali

- **Raccolta dati in tempo reale** da exchange crypto e fonti di notizie finanziarie
- **Database temporaneo ottimizzato** per archiviazione e recupero rapido dei dati
- **Analisi avanzata con LLM** tramite LM Studio, con supporto per contesti fino a 128k tokens
- **Rilevamento trend emergenti** attraverso analisi tecnica e di sentiment
- **Generazione report narrativi** e grafici interattivi
- **Sistemi di sicurezza integrati** con crittografia e rate limiting
- **Monitoraggio e logging avanzato** per tracciare il funzionamento del sistema
- **Architettura modulare e scalabile** per estensioni future

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/Hk4life/marketmover-radar
cd marketmover-radar
Installa le dipendenze:
pip install -r requirements.txt
Scarica e configura LM Studio:

Scarica LM Studio
Carica un modello compatibile (consigliato: Llama 3 70B o simili)
Avvia il server LM Studio
Configura le variabili d'ambiente (crea un file .env nella directory principale):

# API Keys
COINGECKO_API_KEY=your_key_here
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
NEWSAPI_KEY=your_key_here

# Database
USE_REDIS=True
REDIS_HOST=localhost
REDIS_PORT=6379

# LM Studio
LM_STUDIO_HOST=localhost
LM_STUDIO_PORT=1234

# Configurazione app
LOG_LEVEL=INFO
DATA_REFRESH_INTERVAL=300
Utilizzo
Avvio dell'applicazione
python main.py
Opzioni di avvio
# Usa un file di configurazione personalizzato
python main.py --config config/custom_config.json

# Disabilita i websocket per dati in tempo reale
python main.py --no-websockets

# Disabilita la pianificazione automatica delle attività
python main.py --no-scheduling
Report generati
I report generati sono salvati nella directory reports/ in formato HTML. Includono:

Analisi narrativa del mercato basata sui dati raccolti
Grafici interattivi per visualizzare trend e correlazioni
Sentiment delle notizie e impatto sui prezzi
Previsioni a breve termine basate sui dati analizzati
Architettura del sistema
MarketMover Radar è strutturato in moduli indipendenti che comunicano tra loro:

Collectors: Recuperano dati da API esterne (crypto, notizie)
Database: Archivia e gestisce i dati raccolti
Analysis: Elabora i dati per identificare trend e pattern
Visualization: Genera grafici interattivi e report
LLM Integration: Si connette a LM Studio per l'analisi avanzata
Testing
Esegui i test unitari:

python -m unittest discover tests

Estensioni future
Supporto per più exchange e asset
Analisi avanzata di social media e sentiment
Integrazione con sistemi di trading algoritmico
Dashboard web in tempo reale
Notifiche personalizzate su eventi significativi
Contribuire
I contributi sono benvenuti! Per favore, leggi le linee guida per i contributi nel file CONTRIBUTING.md.

Licenza
Questo progetto è rilasciato sotto licenza MIT. Vedi il file LICENSE per maggiori dettagli.


Tutti questi file lavorano insieme per creare un sistema completo che:
1. Raccoglie dati da mercati crypto e notizie finanziarie
2. Normalizza e archivia questi dati in un database temporaneo (Redis o SQLite)
3. Utilizza LM Studio per analizzare i dati e generare insight significativi
4. Crea report narrativi con grafici interattivi
5. Assicura robustezza, sicurezza e scalabilità

Il sistema è progettato per essere modulare, quindi puoi facilmente estenderlo o modificarlo per soddisfare esigenze specifiche.