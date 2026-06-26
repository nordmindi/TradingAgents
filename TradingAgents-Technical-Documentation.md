# TradingAgents Technical Documentation

## Overview
TradingAgents is a multi-agent LLM framework designed for automated financial analysis and trading decision-making. It leverages **LangGraph** to coordinate a team of specialized AI agents through a multi-stage reasoning pipeline.

## Architecture: The Multi-Agent Pipeline
The framework follows a structured flow divided into four main phases:

### Phase 1: Analyst Team (Data Collection & Reporting)
Four specialized analysts collect data sequentially:
1.  **Market Analyst**: Focuses on technical analysis using price action and indicators (RSI, MACD, etc.).
2.  **Social Media Analyst**: Scrapes/analyzes sentiment from social media and news.
3.  **News Analyst**: Evaluates global macroeconomic trends and targeted company news.
4.  **Fundamentals Analyst**: Reviews financial statements (Balance Sheet, Cash Flow, Income Statement).

### Phase 2: Research Team (The Investment Debate)
This phase introduces a conflict-based reasoning model:
*   **Bull Researcher**: Tasked with building the strongest possible case for a "BUY".
*   **Bear Researcher**: Tasked with building the strongest possible case for a "SELL".
*   **Research Manager**: Acts as a judge, evaluates the debate, and produces a structured **Research Plan**.

### Phase 3: Trading Team (Transaction Proposal)
*   **Trader**: Takes the Research Plan and turns it into a concrete transaction proposal (BUY/SELL/HOLD) with specific entry/exit logic.

### Phase 4: Risk Management Team (Stress Testing)
The proposal is then stress-tested by three risk analysts:
*   **Aggressive Analyst**: Champions high-reward/high-risk opportunities.
*   **Conservative Analyst**: Focuses on capital preservation and downside risks.
*   **Neutral Analyst**: Provides a balanced, middle-ground perspective.
*   **Portfolio Manager (PM)**: The final decision-maker. The PM reviews the risk debate, the research plan, and **past lessons learned** from the memory log to deliver the final decision.

## Memory and Learning
The app uses a `TradingMemoryLog` system:
*   **Pending Entries**: Every decision is initially logged as "pending".
*   **Reflections**: After a few days (or on the next run), the system fetches the actual performance (Raw Return and Alpha Return vs. SPY).
*   **Self-Correction**: An LLM "Reflector" analyzes why the trade succeeded or failed. These reflections are injected into future **Portfolio Manager** prompts to ensure the agents learn from past mistakes.

## Key Data Sources
*   **yfinance**: Primary source for OHLCV data, fundamentals, and some news.
*   **Alpha Vantage**: Alternative data source for technical indicators and fundamentals.
*   **OpenRouter**: Used for fetching available LLM models.
*   **Tauric API**: Internal endpoint for project announcements.

## Core Prompts (Summary)
Each agent is driven by a specialized system prompt:
*   **Market Analyst**: Instructed to select up to 8 complementary technical indicators.
*   **Social Analyst**: Focused on "what people are saying" and sentiment trends.
*   **Research Manager**: Rated on a scale (Buy, Overweight, Hold, Underweight, Sell).
*   **PM**: Instructed to be decisive and ground every conclusion in specific evidence from the risk analysts.
