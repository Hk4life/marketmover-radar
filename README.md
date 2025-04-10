An advanced system for real-time monitoring of crypto markets and economic news, with LLM-based analysis via integration with LM Studio.

Key Features
Real-time data collection from crypto exchanges and financial news sources
Temporary database optimized for fast data storage and retrieval
Advanced LLM analytics via LM Studio, with support for up to 128k tokens
Detect emerging trends through technical and sentiment analysis
Generate narrative reports and interactive graphs
Built-in security systems with encryption and rate limiting
Advanced monitoring and logging to track system operation
Modular and scalable architecture for future extensions
Installation
Clone the repository:
git clone https://github.com/Hk4life/marketmover-radar
cd marketmover-radar
Install dependencies:
pip install -r requirements.txt
Download and configure LM Studio:

Download LM Studio
Upload a compatible model (recommended: Llama 3 70B or similar)
Start the LM Studio server
Configure environment variables (create a .env file in the directory main):

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

# App Configuration
LOG_LEVEL=INFO
DATA_REFRESH_INTERVAL=300
Usage
Starting the application
python main.py
Startup options
# Use a custom configuration file
python main.py --config config/custom_config.json

# Disable websockets for real-time data
python main.py --no-websockets

# Disable automatic task scheduling
python main.py --no-scheduling
Generated reports
Generated reports are saved in the reports/ directory in HTML format. They include:

Narrative market analysis based on collected data
Interactive charts to visualize trends and correlations
News sentiment and price impact
Short-term forecasts based on analyzed data
System architecture
MarketMover Radar is structured in independent modules that communicate with each other:

Collectors: Retrieve data from external APIs (crypto, news)
Database: Store and manage collected data
Analysis: Process data to identify trends and patterns
Visualization: Generate interactive charts and reports
LLM Integration: Connect to LM Studio for advanced analysis
Testing
Run unit tests:

python -m unittest discover tests

Future extensions
Support for multiple exchanges and assets
Advanced social media and sentiment analysis
Integration with algorithmic trading systems
Real-time web dashboards
Custom notifications on significant events
Contribute
Contributions are welcome!
