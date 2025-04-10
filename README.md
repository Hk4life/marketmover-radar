MarketMover Radar
MarketMover Radar is an advanced real-time monitoring system for crypto markets and financial news. It leverages large language models (LLMs) through integration with LM Studio to perform in-depth trend analysis, sentiment tracking, and automated reporting.

🚀 Key Features
📈 Live Data Aggregation from top crypto exchanges and news APIs

🧠 LLM-Powered Analysis with support for up to 128k token contexts via LM Studio

📊 Trend Detection using both technical indicators and sentiment signals

🧾 Narrative Reporting and interactive HTML graphs automatically generated

🔐 Built-In Security with API key encryption and rate limiting

🧰 Temporary Data Store optimized for high-speed reads/writes (Redis)

🧪 Modular Architecture designed for scalability and easy feature extension

📡 Advanced Monitoring with full logging and diagnostics

🛠 Installation
Clone the repository

bash
Copy
Edit
git clone https://github.com/Hk4life/marketmover-radar
cd marketmover-radar
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Download and set up LM Studio

Download LM Studio

Load a compatible model (recommended: LLaMA 3 70B or similar)

Launch the LM Studio server

Configure environment variables
Create a .env file in the main/ directory:

env
Copy
Edit
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

# App Config
LOG_LEVEL=INFO
DATA_REFRESH_INTERVAL=300
▶️ Usage
Start the application:
bash
Copy
Edit
python main.py
Optional startup flags:
bash
Copy
Edit
# Use a custom config file
python main.py --config config/custom_config.json

# Disable real-time websockets
python main.py --no-websockets

# Disable scheduled tasks
python main.py --no-scheduling
📂 Reports
Generated reports are saved in the reports/ folder as HTML files. Each report includes:

AI-generated narrative market analysis

Interactive visualizations of trends and signals

Sentiment summaries and price impact analysis

Forecasts based on aggregated data and model outputs

🧱 System Architecture
The system is built with loosely coupled, pluggable modules:

Collectors – Fetch live data from APIs (crypto, news, etc.)

Database – Fast temporary storage (Redis) for real-time access

Analysis Engine – Detects market trends and patterns

Visualization – Generates charts and narrative summaries

LLM Bridge – Connects to LM Studio for natural language processing

✅ Testing
Run unit tests with:

bash
Copy
Edit
python -m unittest discover tests
🧭 Planned Features
Multi-exchange and multi-asset support

Deep social media trend mining

Algorithmic trading bot integration

Real-time dashboard (web UI)

Custom event-based alerts and push notifications

🤝 Contribute
Pull requests, feature ideas, and feedback are always welcome!
