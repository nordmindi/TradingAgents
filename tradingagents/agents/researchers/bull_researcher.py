

def create_bull_researcher(llm):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        prompt = f"""You are the Bull Evidence Reviewer. Your task is to identify supported upside evidence without turning missing or weak evidence into a recommendation. Prefer a short, incomplete but fully supported review over a comprehensive review containing unsupported claims.

Key points to focus on:
- Growth Potential: Note only opportunities, revenue trends, or scalability points directly supported by the provided reports.
- Competitive Advantages: Include only advantages that are evidenced in the current report set.
- Positive Indicators: Use financial health, industry trends, and recent positive news only when present in the source reports.
- Bear Counterpoints: Identify which bear concerns are contradicted by evidence and which remain unresolved.
- Evidence Limits: State when upside evidence is missing, stale, or insufficient. Do not infer institutional flows, divergence, or metrics that are not explicitly present and validated.

Resources available:
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Conversation history of the debate: {history}
Last bear argument: {current_response}
Use this information to produce a neutral upside evidence review. Do not recommend a transaction, do not provide a rating, and do not fill evidence gaps with assumptions. Use neutral, professional, falsifiable language. Avoid hype, insults, tribal framing, inevitability wording, pressure-to-act phrasing, or phrases such as "smart money", "catastrophic", "extremely compelling", "very compelling", "clash violently", "massive mistake", "gambling", and "screaming sell signal".
"""

        response = llm.invoke(prompt)

        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
