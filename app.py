import os
import streamlit as st

from question_loader import load_questions
from business_quality import calculate_business_quality

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Savior Family Office",
    page_icon="✝️",
    layout="wide"
)

# --------------------------------------------------
# LOGO
# --------------------------------------------------

logo_path = "savior_logo.png"

if os.path.exists(logo_path):
    st.image(logo_path, width=300)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("Savior Family Office")
st.subheader("Investment Evaluation Platform")

st.divider()

# --------------------------------------------------
# LOAD QUESTIONS
# --------------------------------------------------

questions = load_questions()

responses = {}

st.header("Dynamic Investment Questionnaire")

# --------------------------------------------------
# BUILD QUESTIONNAIRE
# --------------------------------------------------

for _, row in questions.iterrows():

    qid = row["ID"]
    question = row["Question"]

    responses[qid] = st.number_input(
        question,
        min_value=0.0,
        step=1.0,
        key=qid
    )

# --------------------------------------------------
# EVALUATE
# --------------------------------------------------

if st.button("Evaluate Investment"):

    business_results = calculate_business_quality(
        responses
    )

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