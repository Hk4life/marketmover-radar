MarketMover Radar 
is an advanced real-time monitoring system for crypto markets and financial news. It leverages large language models (LLMs) through integration with LM Studio to perform in-depth trend analysis, sentiment tracking, and automated reporting.

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


git clone https://github.com/Hk4life/marketmover-radar

cd marketmover-radar

Install dependencies

pip install -r requirements.txt

Download and set up LM Studio

Download LM Studio

Load a compatible model (recommended: LLaMA 3 70B or similar)

Launch the LM Studio server

Configure environment variables

Use .env file in the main/ directory to configure 


▶️ Usage

Start the application:

python main.py

Optional startup flags:

Use a custom config file

python main.py --config config/custom_config.json

Disable real-time websockets

python main.py --no-websockets

Disable scheduled tasks

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


🧭 Planned Features

Multi-exchange and multi-asset support

Deep social media trend mining

Algorithmic trading bot integration

Real-time dashboard (web UI)

Custom event-based alerts and push notifications

🤝 Contribute

Pull requests, feature ideas, and feedback are always welcome!
