import os
import streamlit as st
import pandas as pd

from scoring.question_loader import load_questions
from scoring.business_quality import calculate_business_quality
from scoring.red_flag_research import generate_red_flag_searches
from scoring.full_scoring_engine import calculate_full_score

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

    st.divider()
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

    save_df = pd.DataFrame([responses])

    if os.path.exists("investment_history.csv"):
        existing = pd.read_csv("investment_history.csv")
        save_df = pd.concat(
            [existing, save_df],
            ignore_index=True
        )

    save_df.to_csv(
        "investment_history.csv",
        index=False
    )

    st.success("Investment saved to history.")

    csv_data = save_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Investment History",
        data=csv_data,
        file_name="investment_history.csv",
        mime="text/csv"
    )