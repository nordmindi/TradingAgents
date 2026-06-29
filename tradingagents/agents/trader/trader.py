"""Trader: turns research synthesis into non-final execution context."""

from __future__ import annotations

import functools

from langchain_core.messages import AIMessage

from tradingagents.agents.schemas import TraderProposal, render_trader_proposal
from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_trader(llm):
    structured_llm = bind_structured(llm, TraderProposal, "Trader")

    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = build_instrument_context(company_name)
        investment_plan = state["investment_plan"]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a trading execution-context agent. "
                    "Do not issue Buy, Sell, Hold, or any final transaction recommendation. "
                    "Translate the research synthesis into non-final execution, risk, and sizing context."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Based on analysis by a team of analysts, here is a research "
                    f"synthesis tailored for {company_name}. {instrument_context} This synthesis incorporates "
                    f"insights from current technical market trends, macroeconomic indicators, and "
                    f"social media sentiment. Use this plan as a foundation for evaluating your next "
                    f"execution context.\n\nResearch Synthesis: {investment_plan}\n\n"
                    f"Provide context for the Portfolio Manager without issuing a transaction command."
                ),
            },
        ]

        trader_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            messages,
            render_trader_proposal,
            "Trader",
        )

        return {
            "messages": [AIMessage(content=trader_plan)],
            "trader_investment_plan": trader_plan,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
