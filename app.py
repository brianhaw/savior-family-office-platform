import os
import streamlit as st

from scoring.question_loader import load_questions
from scoring.business_quality import calculate_business_quality

# ==================================================
# PAGE SETTINGS
# ==================================================

st.set_page_config(
    page_title="Savior Family Office",
    page_icon="✝️",
    layout="wide"
)

# ==================================================
# LOGO / BRANDING
# ==================================================

logo_path = "data/assets/savior_logo.png"

if os.path.exists(logo_path):
    st.image(logo_path, width=300)
else:
    st.warning("Logo not found. Expected location: data/assets/savior_logo.png")

st.title("Savior Family Office")
st.subheader("Investment Evaluation Platform")

st.markdown("---")

# ==================================================
# LOAD QUESTIONS
# ==================================================

questions = load_questions()

responses = {}

st.header("Dynamic Investment Questionnaire")

# ==================================================
# BUILD QUESTIONS FROM CSV
# ==================================================

for _, row in questions.iterrows():

    qid = row["ID"]
    question = row["Question"]
    qtype = row["Type"]

    if qtype == "number":

        responses[qid] = st.number_input(
            label=question,
            min_value=0.0,
            step=1.0,
            key=qid
        )

    elif qtype == "currency":

        responses[qid] = st.number_input(
            label=question,
            min_value=0.0,
            step=10000.0,
            key=qid
        )

    elif qtype == "percent":

        responses[qid] = st.number_input(
            label=question,
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key=qid
        )

    else:

        responses[qid] = st.text_input(
            label=question,
            key=qid
        )

# ==================================================
# EVALUATE BUTTON
# ==================================================

if st.button("Evaluate Investment"):

    business_results = calculate_business_quality(
        responses
    )

    st.markdown("---")

    st.header("Investment Evaluation Results")

    score = business_results["business_quality_score"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Business Quality",
            score
        )

    with col2:
        st.metric(
            "Years Score",
            business_results["years_score"]
        )

    with col3:
        st.metric(
            "Revenue Score",
            business_results["revenue_score"]
        )

    with col4:
        st.metric(
            "Growth Score",
            business_results["growth_score"]
        )

    st.markdown("---")

    if score >= 8:

        st.success(
            "Recommendation: STRONG BUSINESS QUALITY"
        )

    elif score >= 6:

        st.warning(
            "Recommendation: MODERATE BUSINESS QUALITY"
        )

    else:

        st.error(
            "Recommendation: WEAK BUSINESS QUALITY"
        )

    st.subheader("Business Quality Details")

    st.json(business_results)

    st.subheader("Question Responses")

    st.json(responses)