"""
TradingAgents Examples

This file demonstrates different ways to use TradingAgents:
1. Direct library usage (as shown in the original code)
2. Service API usage (recommended for multi-application deployments)

For service deployment, see DEPLOYMENT.md and the files in the k8s/ directory.
"""

# Example 1: Direct library usage (uncomment to run)
"""
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

# DEFAULT_CONFIG already applies TRADINGAGENTS_* env-var overrides
# (llm_provider, deep_think_llm, quick_think_llm, backend_url, etc.),
# so users can switch models or endpoints purely via .env without
# editing this script. Override individual keys here only when you
# want a hard-coded value that should ignore the environment.
config = DEFAULT_CONFIG.copy()

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
"""

# Example 2: Service API usage
"""
To run the service:

1. Set your API key:
   export TRADINGAGENTS_SERVICE_API_KEY=your-secret-key

2. Run the service:
   python scripts/run_service.py
   
   Or use the startup scripts:
   ./start-service.sh (Linux/Mac)
   start-service.bat (Windows)

3. Use the API:
   curl -X POST "http://localhost:8000/v1/reports" \
        -H "X-API-Key: your-secret-key" \
        -H "Content-Type: application/json" \
        -d '{
          "ticker": "NVDA",
          "analysis_date": "2026-05-07",
          "selected_analysts": ["market", "news", "fundamentals"]
        }'

For cloud deployment instructions, see DEPLOYMENT.md and k8s/README.md
"""
