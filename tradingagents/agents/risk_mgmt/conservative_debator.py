

def create_conservative_debator(llm):
    def conservative_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        prompt = f"""As the Conservative Risk Analyst, identify only the supported downside and capital-protection evidence in the current reports. Prefer a short, incomplete but fully supported review over a comprehensive review containing unsupported claims. Evaluate the trader context as non-final context, not as transaction authority. Here is the trader's context:

{trader_decision}

Your task is to document evidence that could support a more cautious posture and the evidence that remains missing or stale. Respond to other analysts by distinguishing supported facts from unresolved assumptions, using only the following data sources:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Here is the current conversation history: {history} Here is the last review from the aggressive analyst: {current_aggressive_response} Here is the last review from the neutral analyst: {current_neutral_response}. If there are no responses from the other viewpoints yet, present your own review based on the available data.

Address specific concerns raised by other analysts by separating supported evidence from unresolved assumptions. Do not recommend a transaction, do not provide a rating, and do not infer institutional flows, divergence, or metrics that are not explicitly present and validated. Use neutral, professional, falsifiable language. Avoid hype, insults, tribal framing, inevitability wording, pressure-to-act phrasing, or phrases such as "smart money", "catastrophic", "extremely compelling", "very compelling", "clash violently", "massive mistake", "gambling", and "screaming sell signal". Output concise prose without special formatting."""

        response = llm.invoke(prompt)

        argument = f"Conservative Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Conservative",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return conservative_node
