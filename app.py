import os
from io import BytesIO
from datetime import datetime

import streamlit as st
import pandas as pd

from scoring.red_flag_research import generate_red_flag_searches

st.set_page_config(
    page_title="Savior Family Office",
    page_icon="✝️",
    layout="wide"
)

logo_path = os.path.join(os.path.dirname(__file__), "savior_logo.png")

if os.path.exists(logo_path):
    st.image(logo_path, width=300)

st.title("Savior Family Office")
st.subheader("Investment Evaluation Platform v2.0")
st.divider()


def score_financial_strength(revenue, revenue_growth, ebitda, fcf, debt, recurring_revenue):
    score = 0

    if revenue >= 5_000_000:
        score += 20
    elif revenue >= 1_000_000:
        score += 15
    elif revenue > 0:
        score += 8

    if revenue_growth >= 20:
        score += 15
    elif revenue_growth >= 10:
        score += 10
    elif revenue_growth > 0:
        score += 5

    if ebitda > 0:
        score += 20

    if fcf > 0:
        score += 20

    debt_to_ebitda = debt / ebitda if ebitda > 0 else 999

    if debt_to_ebitda <= 2:
        score += 15
    elif debt_to_ebitda <= 4:
        score += 8

    if recurring_revenue >= 60:
        score += 10
    elif recurring_revenue >= 30:
        score += 5

    return min(score, 100), debt_to_ebitda


def score_return_potential(projected_irr, payback_years):
    score = 0

    if projected_irr >= 30:
        score += 60
    elif projected_irr >= 20:
        score += 45
    elif projected_irr >= 12:
        score += 30
    elif projected_irr > 0:
        score += 15

    if payback_years <= 3:
        score += 40
    elif payback_years <= 5:
        score += 25
    elif payback_years <= 7:
        score += 10

    return min(score, 100)


def score_risk_quality(litigation, regulatory, key_person):
    avg_risk = (litigation + regulatory + key_person) / 3
    return max(0, 100 - (avg_risk * 10))


def classify_deal(score, hard_stop=False):
    if hard_stop:
        if score < 40:
            return "☠️ Snake Oil", "Reject"
        return "🐍 Snake", "Watchlist only"

    if score >= 85:
        return "🦄 Unicorn", "Proceed to full diligence"
    elif score >= 70:
        return "🐋 Whale", "Strong candidate for diligence"
    elif score >= 55:
        return "🐛 Caterpillar", "Promising but needs more proof"
    elif score >= 40:
        return "🐍 Snake", "High risk / watchlist only"
    else:
        return "☠️ Snake Oil", "Reject"


def assign_capital_tier(industry, pick_shovel, rollup, strategic_alignment):
    industry_lower = industry.lower()

    if any(x in industry_lower for x in ["treasury", "cash", "bond"]):
        return "Tier 1 – Preservation"

    if any(x in industry_lower for x in ["reit", "multifamily", "nnn", "real estate"]):
        return "Tier 2 – Compounding"

    if pick_shovel >= 8 or rollup >= 8:
        return "Tier 3 – Wealth Engine"

    if strategic_alignment >= 7:
        return "Tier 4 – Asymmetric Opportunity"

    return "Unclassified / Needs Review"


def generate_justification(company_name, score, classification, recommendation, strengths, risks, tier):
    return f"""
{company_name} received a Savior Score of {score:.1f} and was classified as {classification}.

Capital Allocation Bucket: {tier}

Recommended Action: {recommendation}.

Key Strengths:
{chr(10).join(["- " + s for s in strengths]) if strengths else "- No major strengths identified."}

Key Risks:
{chr(10).join(["- " + r for r in risks]) if risks else "- No major risks identified."}

Summary:
This evaluation reflects the Savior Family Office philosophy of prioritizing cash flow, durable businesses,
pick-and-shovel opportunities, roll-up potential, strategic alignment, and institutional safety.
"""


with st.expander("Definitions / How to Use This Model"):
    st.write("""
    This platform evaluates investments using the Savior Family Compound & Family Office philosophy.

    It prioritizes:
    - Cash flow
    - Financial strength
    - Low risk
    - Pick-and-shovel businesses
    - Roll-up potential
    - Strategic alignment
    - Sleep Well At Night safety

    Deal classifications:
    - 🦄 Unicorn = Exceptional
    - 🐋 Whale = Strong
    - 🐛 Caterpillar = Promising
    - 🐍 Snake = Risky
    - ☠️ Snake Oil = Avoid
    """)

st.header("Red Flag Research Engine")

company_name = st.text_input("Company Name")
website = st.text_input("Company Website")
ceo_name = st.text_input("CEO / Founder Name")
state = st.text_input("Company State")
industry = st.text_input("Industry")

if st.button("Run Red Flag Research"):
    searches = generate_red_flag_searches(
        company_name,
        website,
        ceo_name,
        state,
        industry
    )

    st.subheader("Research Checklist")

    for item in searches:
        st.markdown(
            f"**{item['Category']}** - "
            f"[{item['Search']}]({item['URL']})"
        )

st.divider()
st.header("Investment Questionnaire")

col1, col2 = st.columns(2)

with col1:
    revenue = st.number_input("Annual Revenue", min_value=0.0, step=100000.0)
    revenue_growth = st.number_input("Revenue Growth %", min_value=-100.0, max_value=500.0, step=1.0)
    ebitda = st.number_input("EBITDA", min_value=-100000000.0, step=100000.0)
    free_cash_flow = st.number_input("Free Cash Flow", min_value=-100000000.0, step=100000.0)
    debt = st.number_input("Debt", min_value=0.0, step=100000.0)
    recurring_revenue = st.number_input("Recurring Revenue %", min_value=0.0, max_value=100.0, step=1.0)

with col2:
    investment_amount = st.number_input("Investment Amount Needed", min_value=0.0, step=100000.0)
    equity_stake = st.number_input("Equity Stake %", min_value=0.0, max_value=100.0, step=1.0)
    projected_irr = st.number_input("Projected IRR %", min_value=0.0, max_value=500.0, step=1.0)
    payback_years = st.number_input("Payback Period Years", min_value=0.0, step=0.5)

st.subheader("Quality Scores")

q1, q2, q3 = st.columns(3)

with q1:
    founder_character = st.slider("Founder Character Score", 0, 10, 5)
    financial_transparency = st.slider("Financial Transparency Score", 0, 10, 5)
    strategic_alignment = st.slider("Strategic Alignment Score", 0, 10, 5)

with q2:
    pick_shovel = st.slider("Pick-and-Shovel Score", 0, 10, 5)
    rollup_potential = st.slider("Roll-Up Potential Score", 0, 10, 5)
    estate_synergy = st.slider("Estate Synergy Score", 0, 10, 5)

with q3:
    sleep_well = st.slider("Sleep Well At Night Score", 0, 10, 5)
    litigation_risk = st.slider("Litigation Risk Score", 0, 10, 5)
    regulatory_risk = st.slider("Regulatory Risk Score", 0, 10, 5)
    key_person_risk = st.slider("Key Person Risk Score", 0, 10, 5)

if st.button("Evaluate Investment"):
    financial_score, debt_to_ebitda = score_financial_strength(
        revenue,
        revenue_growth,
        ebitda,
        free_cash_flow,
        debt,
        recurring_revenue
    )

    return_score = score_return_potential(projected_irr, payback_years)
    risk_score = score_risk_quality(litigation_risk, regulatory_risk, key_person_risk)

    strategic_score = strategic_alignment * 10
    pick_rollup_score = ((pick_shovel + rollup_potential) / 2) * 10
    legacy_sleep_score = sleep_well * 10
    estate_score = estate_synergy * 10

    savior_score = (
        financial_score * 0.25 +
        return_score * 0.15 +
        risk_score * 0.20 +
        strategic_score * 0.15 +
        pick_rollup_score * 0.20 +
        estate_score * 0.025 +
        legacy_sleep_score * 0.025
    )

    hard_stop_flags = []

    if founder_character < 7:
        hard_stop_flags.append("Founder Character below 7")
    if financial_transparency < 6:
        hard_stop_flags.append("Financial Transparency below 6")
    if sleep_well < 5:
        hard_stop_flags.append("Sleep Well At Night below 5")
    if litigation_risk > 7:
        hard_stop_flags.append("Litigation Risk above 7")
    if regulatory_risk > 8:
        hard_stop_flags.append("Regulatory Risk above 8")
    if debt_to_ebitda > 5 and ebitda > 0:
        hard_stop_flags.append("Debt/EBITDA above 5")
    if free_cash_flow < 0:
        hard_stop_flags.append("Negative Free Cash Flow")

    hard_stop = len(hard_stop_flags) > 0

    classification, recommendation = classify_deal(savior_score, hard_stop)

    tier = assign_capital_tier(
        industry,
        pick_shovel,
        rollup_potential,
        strategic_alignment
    )

    strengths = []
    risks = []

    if financial_score >= 75:
        strengths.append("Strong financial profile")
    if recurring_revenue >= 60:
        strengths.append("High recurring revenue")
    if free_cash_flow > 0:
        strengths.append("Positive free cash flow")
    if pick_shovel >= 8:
        strengths.append("Strong pick-and-shovel characteristics")
    if rollup_potential >= 8:
        strengths.append("Strong roll-up potential")
    if strategic_alignment >= 8:
        strengths.append("Strong Family Office strategic alignment")

    if debt_to_ebitda > 4:
        risks.append("High leverage")
    if litigation_risk > 6:
        risks.append("Elevated litigation risk")
    if regulatory_risk > 6:
        risks.append("Elevated regulatory risk")
    if key_person_risk > 6:
        risks.append("Key person dependency risk")
    if free_cash_flow < 0:
        risks.append("Negative free cash flow")

    justification = generate_justification(
        company_name,
        savior_score,
        classification,
        recommendation,
        strengths,
        risks,
        tier
    )

    commandment_results = {
        "Solves a real problem": strategic_alignment >= 6,
        "Generates cash flow": free_cash_flow > 0 or ebitda > 0,
        "Understandable business": financial_transparency >= 6,
        "Needed during recession": pick_shovel >= 7,
        "Needed in 20 years": pick_shovel >= 7 or rollup_potential >= 7,
        "Improves the institution": strategic_alignment >= 7,
        "Sleep well at night": sleep_well >= 5
    }

    commandment_pass_count = sum(commandment_results.values())
    commandment_status = "PASS" if commandment_pass_count >= 5 else "FAIL"

    st.divider()
    st.header("Investment Evaluation Results")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Savior Score", f"{savior_score:.1f}")
    col2.metric("Classification", classification)
    col3.metric("Capital Tier", tier)
    col4.metric("Commandment Test", f"{commandment_status} ({commandment_pass_count}/7)")

    st.subheader("Recommendation")
    st.success(recommendation) if "Proceed" in recommendation or "Strong" in recommendation else st.warning(recommendation)

    st.subheader("Justification Summary")
    st.write(justification)

    st.subheader("Savior Commandment Test")
    for item, passed in commandment_results.items():
        if passed:
            st.success(f"✓ {item}")
        else:
            st.error(f"✗ {item}")

    if hard_stop_flags:
        st.subheader("Hard Stop Flags")
        for flag in hard_stop_flags:
            st.error(flag)

    st.subheader("Score Breakdown")
    score_breakdown = {
        "Financial Strength": financial_score,
        "Return Potential": return_score,
        "Risk Quality": risk_score,
        "Strategic Alignment": strategic_score,
        "Pick-and-Shovel / Roll-Up": pick_rollup_score,
        "Estate Synergy": estate_score,
        "Sleep Well At Night": legacy_sleep_score
    }

    st.json(score_breakdown)

    row = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Company Name": company_name,
        "Website": website,
        "CEO / Founder": ceo_name,
        "State": state,
        "Industry": industry,
        "Revenue": revenue,
        "Revenue Growth %": revenue_growth,
        "EBITDA": ebitda,
        "Free Cash Flow": free_cash_flow,
        "Debt": debt,
        "Debt/EBITDA": debt_to_ebitda,
        "Recurring Revenue %": recurring_revenue,
        "Investment Amount": investment_amount,
        "Equity Stake %": equity_stake,
        "Projected IRR %": projected_irr,
        "Payback Years": payback_years,
        "Founder Character": founder_character,
        "Financial Transparency": financial_transparency,
        "Strategic Alignment": strategic_alignment,
        "Pick-and-Shovel": pick_shovel,
        "Roll-Up Potential": rollup_potential,
        "Estate Synergy": estate_synergy,
        "Sleep Well At Night": sleep_well,
        "Litigation Risk": litigation_risk,
        "Regulatory Risk": regulatory_risk,
        "Key Person Risk": key_person_risk,
        "Savior Score": savior_score,
        "Classification": classification,
        "Recommendation": recommendation,
        "Capital Tier": tier,
        "Commandment Test": commandment_status,
        "Hard Stop Flags": "; ".join(hard_stop_flags),
        "Justification Summary": justification
    }

    history_path = "investment_history.xlsx"

    new_df = pd.DataFrame([row])

    if os.path.exists(history_path):
        existing_df = pd.read_excel(history_path, sheet_name="Investment Analyses")
        history_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        history_df = new_df

    dashboard_df = pd.DataFrame({
        "Metric": [
            "Deals Evaluated",
            "Average Savior Score",
            "Unicorns",
            "Whales",
            "Caterpillars",
            "Snakes",
            "Snake Oil"
        ],
        "Value": [
            len(history_df),
            round(history_df["Savior Score"].mean(), 2),
            history_df["Classification"].str.contains("Unicorn").sum(),
            history_df["Classification"].str.contains("Whale").sum(),
            history_df["Classification"].str.contains("Caterpillar").sum(),
            history_df["Classification"].str.contains("Snake").sum(),
            history_df["Classification"].str.contains("Snake Oil").sum()
        ]
    })

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        history_df.to_excel(writer, index=False, sheet_name="Investment Analyses")
        new_df.to_excel(writer, index=False, sheet_name="Latest Evaluation")
        pd.DataFrame([score_breakdown]).to_excel(writer, index=False, sheet_name="Score Breakdown")
        pd.DataFrame([{"Justification Summary": justification}]).to_excel(writer, index=False, sheet_name="Justification")
        dashboard_df.to_excel(writer, index=False, sheet_name="Portfolio Dashboard")

    excel_data = output.getvalue()

    with open(history_path, "wb") as f:
        f.write(excel_data)

    st.success("Investment saved to Excel history.")

    st.download_button(
        label="Download Excel Investment History",
        data=excel_data,
        file_name="savior_investment_history.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )