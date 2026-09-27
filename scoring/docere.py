"""Docere's conversation and briefing context.

The model only sees data supplied here. It does not have market-data access.
"""

from datetime import datetime

from openai import OpenAI


INSTRUCTIONS = """You are Docere, the Savior Family Office investment research partner.
Have substantive, thoughtful conversations about finance, acquisitions, portfolio
construction, risk, valuation, and exits. Use the Savior questionnaire as the
decision framework: financial strength, return potential, risk quality, strategic
alignment, pick-and-shovel and roll-up potential, estate synergy, and sleep-well
quality. Treat scores as screening evidence, never as an instruction to trade.

The supplied investment history is user-entered evaluation data, not verified
holdings or live market data. Distinguish facts in that history, assumptions,
inferences, and information you lack. Never claim to have searched the web,
verified a regulation, checked a price, contacted a company, or monitored an
investment unless a dated source is explicitly supplied. Ask for jurisdiction
and date before making a current legal or policy assessment. Explain downside,
liquidity, concentration, incentives, and what could disprove a thesis.
For an actionable decision, identify what evidence and professional tax, legal,
or licensed investment review is still needed. Do not execute trades or promise
returns. Be direct, analytical, and conversational; avoid generic warnings.
"""


def history_context(history, limit=12):
    """Return a bounded, dated summary of prior evaluations, never secret fields."""
    if history is None or history.empty:
        return "No saved evaluations are available. No holdings have been verified."
    fields = [
        "Date", "Company Name", "Industry", "Savior Score", "Classification",
        "Recommendation", "Capital Tier", "Hard Stop Flags", "Revenue",
        "EBITDA", "Free Cash Flow", "Debt/EBITDA", "Projected IRR %",
        "Investment Amount",
    ]
    selected = [name for name in fields if name in history.columns]
    rows = history.tail(limit)[selected].fillna("").to_dict("records")
    return "Saved evaluations (user-entered, not verified holdings):\n" + "\n".join(
        str(row) for row in rows
    )


def ask_docere(messages, context, api_key, model="gpt-6-astra"):
    if not api_key:
        raise ValueError("Configure OPENAI_API_KEY to enable Docere.")
    if not messages or messages[-1]["role"] != "user":
        raise ValueError("A user message is required.")
    client = OpenAI(api_key=api_key, timeout=45.0, max_retries=0)
    response = client.responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=[
            {"role": "user", "content": "Investment context as of "
             + datetime.now().astimezone().isoformat(timespec="minutes")
             + ":\n" + context},
            *messages[-16:],
        ],
        store=False,
    )
    return response.output_text


def briefing_prompt(period, context):
    return (
        f"Prepare the {period} Savior Family Office briefing from the supplied "
        "evaluation history. Cover top opportunities, concerning changes visible "
        "in the history, portfolio data gaps, and three concrete research actions. "
        "If there is no new evidence, say so. Do not invent headlines, prices, "
        "holdings, or alerts.\n\n" + context
    )
