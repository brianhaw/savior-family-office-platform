import os
from datetime import datetime

import streamlit as st
import pandas as pd

from scoring.question_loader import load_questions
from scoring.business_quality import calculate_business_quality
from scoring.red_flag_research import generate_red_flag_searches
from scoring.full_scoring_engine import calculate_full_score
from scoring.summary_judgment import generate_summary_judgment

st.set_page_config(
    page_title="Savior Family Office",
    page_icon="✝️",
    layout="wide"
)

logo_path = os.path.join(os.path.dirname(__file__), "savior_logo.png")

if os.path.exists(logo_path):
    st.image(logo_path, width=300)

st.title("Savior Family Office")
st.subheader("Investment Evaluation Platform")
st.divider()

with st.expander("Definitions / How to Use This Model"):
    st.write("""
    **EBITDA:** Earnings before interest, taxes, depreciation, and amortization. A proxy for operating profitability.

    **Debt to EBITDA:** Measures leverage. Higher values mean the company may be carrying too much debt.

    **Free Cash Flow:** Cash left after operating expenses and capital needs. Negative free cash flow is a warning sign.

    **Customer Concentration:** Risk from relying too heavily on one or a few customers.

    **Recurring Revenue:** Revenue that repeats predictably, such as subscriptions or contracts.

    **Projected ROI:** Estimated return on investment.

    **IRR:** Internal rate of return. Measures expected annualized return.

    **Break-Even Years:** How long it may take to recover the original investment.

    **NIMBY Risk:** Risk of public/community opposition.

    **Exit Friction:** How hard it may be to get out of the deal.

    **Contagion Risk:** Risk that this investment could damage existing businesses, reputation, liquidity, or operations.

    **SWAN Score:** Sleep Well At Night score. Higher means the investment feels safer and less stressful.
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

questions = load_questions()
responses = {}

st.header("Investment Questionnaire")

for _, row in questions.iterrows():
    qid = row["ID"]
    question = row["Question"]
    qtype = row["Type"]

    if qtype == "currency":
        responses[qid] = st.number_input(
            question,
            min_value=0.0,
            step=10000.0,
            key=qid
        )

    elif qtype == "percent":
        responses[qid] = st.number_input(
            question,
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key=qid
        )

    elif qtype == "score10":
        responses[qid] = st.slider(
            question,
            min_value=0,
            max_value=10,
            value=5,
            key=qid
        )

    elif qtype == "yesno":
        responses[qid] = st.checkbox(
            question,
            key=qid
        )

    else:
        responses[qid] = st.number_input(
            question,
            min_value=0.0,
            step=1.0,
            key=qid
        )

if st.button("Evaluate Investment"):
    business_results = calculate_business_quality(responses)
    full_results = calculate_full_score(responses)
    summary_judgment = generate_summary_judgment(full_results)

    st.divider()
    st.header("Investment Evaluation Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Business Quality",
            business_results["business_quality_score"]
        )

    with col2:
        st.metric(
            "Overall Score",
            full_results["Overall Score"]
        )

    with col3:
        st.metric(
            "Recommendation",
            full_results["Recommendation"]
        )

    st.subheader("Summary Judgment")
    st.write(summary_judgment)

    st.subheader("Composite Scores")
    st.json(full_results)

    if len(full_results["Red Flags"]) > 0:
        st.subheader("Red Flags")

        for flag in full_results["Red Flags"]:
            st.error(flag)

    else:
        st.success("No major red flags identified.")

    st.subheader("Detailed Responses")
    st.json(responses)

    history_row = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Company Name": company_name,
        "Website": website,
        "CEO / Founder": ceo_name,
        "State": state,
        "Industry": industry,
        "Overall Score": full_results["Overall Score"],
        "Recommendation": full_results["Recommendation"],
        "Summary Judgment": summary_judgment,
        "Red Flags": "; ".join(full_results["Red Flags"]),
        "Business Quality Score": full_results["Business Quality Score"],
        "Deal Quality Score": full_results["Deal Quality Score"],
        "Return Score": full_results["Return Score"],
        "Risk / Execution Score": full_results["Risk / Execution Score"],
        "Tax Efficiency Score": full_results["Tax Efficiency Score"],
        "Family Office Fit Score": full_results["Family Office Fit Score"]
    }

    history_df = pd.DataFrame([history_row])

    if os.path.exists("investment_history.csv"):
        existing = pd.read_csv("investment_history.csv")
        history_df = pd.concat(
            [existing, history_df],
            ignore_index=True
        )

    history_df.to_csv(
        "investment_history.csv",
        index=False
    )

    st.success("Investment saved to history.")

    csv_data = history_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Investment History",
        data=csv_data,
        file_name="investment_history.csv",
        mime="text/csv"
    )