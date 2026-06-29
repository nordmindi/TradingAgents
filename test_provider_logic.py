#!/usr/bin/env python3
"""
Test script to verify the provider selection logic.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.service.runner import ReportRequest

# Load environment variables
load_dotenv()

def test_build_config():
    """Test the build_config function with different scenarios."""
    
    # Import the function
    from tradingagents.service.runner import build_config
    
    # Test case 1: Environment provider set to ollama
    print("=== Test Case 1: Environment provider set to ollama ===")
    print(f"TRADINGAGENTS_LLM_PROVIDER from env: {os.getenv('TRADINGAGENTS_LLM_PROVIDER')}")
    print(f"TRADINGAGENTS_LLM_PROVIDER from env (repr): {repr(os.getenv('TRADINGAGENTS_LLM_PROVIDER'))}")
    print(f"DEFAULT_CONFIG llm_provider: {DEFAULT_CONFIG['llm_provider']}")
    print(f"DEFAULT_CONFIG llm_provider (repr): {repr(DEFAULT_CONFIG['llm_provider'])}")
    print(f"OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
    
    # Let's check if the DEFAULT_CONFIG is actually reading the env var
    env_provider = os.getenv("TRADINGAGENTS_LLM_PROVIDER", "openai")
    print(f"Direct env read: {env_provider}")
    
    # Let's also check the DEFAULT_CONFIG creation
    print("DEFAULT_CONFIG keys related to LLM:")
    for key in DEFAULT_CONFIG.keys():
        if 'llm' in key.lower() or 'provider' in key.lower():
            print(f"  {key}: {repr(DEFAULT_CONFIG[key])}")
    
    # Create a mock request with no provider specified
    request = ReportRequest(
        ticker="TEST",
        analysis_date="2024-01-01",
        selected_analysts=("market",)
    )
    
    # Build config
    config = build_config(request, "test-job-1")
    
    print(f"Final config provider: {config['llm_provider']}")
    print(f"Final config deep_think_llm: {config['deep_think_llm']}")
    print(f"Final config quick_think_llm: {config['quick_think_llm']}")
    
    # Test case 2: Request with explicit provider
    print("\n=== Test Case 2: Request with explicit provider ===")
    request_with_provider = ReportRequest(
        ticker="TEST",
        analysis_date="2024-01-01",
        selected_analysts=("market",),
        llm_provider="openai"
    )
    
    config2 = build_config(request_with_provider, "test-job-2")
    
    print(f"Request provider: {request_with_provider.llm_provider}")
    print(f"Final config provider: {config2['llm_provider']}")
    
    return config['llm_provider'] == 'ollama'

if __name__ == "__main__":
    result = test_build_config()
    print(f"\nTest result: {'PASS' if result else 'FAIL'}")
    sys.exit(0 if result else 1)