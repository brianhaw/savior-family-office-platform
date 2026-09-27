"""Evidence gate between a web mention and a Savior investment evaluation."""

SAVIOR_INPUTS = {
    "Financial strength": (
        "Annual revenue", "Revenue growth", "EBITDA", "Free cash flow",
        "Debt", "Recurring revenue",
    ),
    "Deal economics": (
        "Investment amount and entry price", "Equity stake", "Projected IRR",
        "Payback period",
    ),
    "Management and fit": (
        "Founder character", "Financial transparency", "Strategic alignment",
        "Pick-and-shovel fit", "Roll-up potential", "Estate synergy",
        "Sleep-well assessment",
    ),
    "Risk": ("Litigation", "Regulatory exposure", "Key-person dependence"),
}

HARD_STOPS = (
    "Founder character below 7", "Financial transparency below 6",
    "Sleep-well score below 5", "Litigation risk above 7",
    "Regulatory risk above 8", "Debt/EBITDA above 5",
    "Negative free cash flow",
)


def web_lead_screen(lead):
    """A search hit supplies no verified questionnaire inputs or deal terms."""
    return {
        "company": lead.get("candidate_name") or "Name unconfirmed",
        "savior_rating": "Unrated — financial and diligence evidence missing",
        "profit_probability": "Not estimable — entry price, terms and horizon missing",
        "risk": "Unassessed — hard stops need evidence",
        "known_inputs": 0,
        "total_inputs": sum(map(len, SAVIOR_INPUTS.values())),
        "unknown_by_category": SAVIOR_INPUTS,
        "unknown_hard_stops": HARD_STOPS,
    }
