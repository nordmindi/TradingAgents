

def create_bear_researcher(llm):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        prompt = f"""You are the Bear Evidence Reviewer. Your task is to identify supported downside evidence without turning missing or weak evidence into a recommendation. Prefer a short, incomplete but fully supported review over a comprehensive review containing unsupported claims.

Key points to focus on:

- Risks and Challenges: Note only risks directly supported by the provided reports.
- Competitive Weaknesses: Include only vulnerabilities evidenced in the current report set.
- Negative Indicators: Use financial data, market trends, or adverse news only when present in the source reports.
- Bull Counterpoints: Identify which bull claims are contradicted by evidence and which remain unresolved.
- Evidence Limits: State when downside evidence is missing, stale, or insufficient. Do not infer institutional flows, divergence, or metrics that are not explicitly present and validated.

Resources available:

Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Conversation history of the debate: {history}
Last bull argument: {current_response}
Use this information to produce a neutral downside evidence review. Do not recommend a transaction, do not provide a rating, and do not fill evidence gaps with assumptions.
"""

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
