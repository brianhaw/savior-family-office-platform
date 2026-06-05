import os
import streamlit as st
import pandas as pd

from scoring.question_loader import load_questions
from scoring.business_quality import calculate_business_quality
from scoring.red_flag_research import generate_red_flag_searches

st.set_page_config(
    page_title="Savior Family Office",
    page_icon="✝️",
    layout="wide"
)

# Logo
logo_path = os.path.join(os.path.dirname(__file__), "savior_logo.png")

if os.path.exists(logo_path):
    st.image(logo_path, width=300)

# Header
st.title("Savior Family Office")
st.subheader("Investment Evaluation Platform")
st.divider()

# Red Flag Research
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

    st.subheader("Red Flag Search Checklist")

    df = pd.DataFrame(searches)

    for _, row in df.iterrows():
        st.markdown(
            f"**{row['Category']}** — "
            f"[{row['Search']}]({row['URL']})"
        )

st.divider()

# Load Questions
questions = load_questions()
responses = {}

st.header("Dynamic Investment Questionnaire")

# Build Questionnaire
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

# Evaluate
if st.button("Evaluate Investment"):
    business_results = calculate_business_quality(responses)

    st.divider()
    st.header("Investment Evaluation Results")

    st.metric(
        "Business Quality Score",
        business_results["business_quality_score"]
    )

    score = business_results["business_quality_score"]

    if score >= 8:
        st.success("Recommendation: STRONG BUSINESS QUALITY")
    elif score >= 6:
        st.warning("Recommendation: MODERATE BUSINESS QUALITY")
    else:
        st.error("Recommendation: WEAK BUSINESS QUALITY")

    st.subheader("Business Quality Details")
    st.json(business_results)

    st.subheader("Question Responses")
    st.json(responses)