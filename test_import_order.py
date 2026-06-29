#!/usr/bin/env python3
"""
Test script to verify the import order issue.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== Testing import order issue ===")

# Test 1: Import DEFAULT_CONFIG first, then load dotenv (current behavior)
print("\n--- Test 1: Import first, then load dotenv ---")
from tradingagents.default_config import DEFAULT_CONFIG
print(f"DEFAULT_CONFIG before dotenv: {DEFAULT_CONFIG['llm_provider']}")

from dotenv import load_dotenv
load_dotenv()
print(f"DEFAULT_CONFIG after dotenv: {DEFAULT_CONFIG['llm_provider']}")
print(f"Direct env read after dotenv: {os.getenv('TRADINGAGENTS_LLM_PROVIDER')}")

# Test 2: Load dotenv first, then import DEFAULT_CONFIG (correct behavior)
print("\n--- Test 2: Load dotenv first, then import ---")
# Need to restart Python to test this properly, so let's simulate it
import subprocess
result = subprocess.run([
    sys.executable, "-c", 
    "import os; from dotenv import load_dotenv; load_dotenv(); from tradingagents.default_config import DEFAULT_CONFIG; print(f'DEFAULT_CONFIG with dotenv first: {DEFAULT_CONFIG[\"llm_provider\"]}')"
], capture_output=True, text=True, cwd=project_root)

print(result.stdout.strip())
if result.stderr:
    print(f"STDERR: {result.stderr}")