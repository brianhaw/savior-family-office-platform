"""Private Samson workspace, deployed separately from the Savior intake form."""

import os
from hashlib import sha256
from io import BytesIO

import pandas as pd
import streamlit as st

from scoring.samson import ask_samson, briefing_prompt, history_context
from scoring.discovery import latest_filings, lead_context
from scoring.portfolio_office import conversation_context
from scoring.web_discovery import THEMES, search_theme, web_context


st.set_page_config(page_title="Samson | Savior Family Office", page_icon="📖", layout="wide")
st.title("Samson")
st.caption("Private investment research workspace · no live feed or continuous monitoring is connected yet")
st.caption("Portfolio lens: Preservation 25% · Core compounding 25% · Wealth engine 35% · Capped asymmetric 15% (planning targets; actual holdings unverified)")


def secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default


api_key = os.environ.get("OPENAI_API_KEY") or secret("OPENAI_API_KEY")
standard_model = os.environ.get("SAMSON_MODEL") or secret("SAMSON_MODEL", "gpt-6-sol")
deep_model = os.environ.get("SAMSON_DEEP_MODEL") or secret("SAMSON_DEEP_MODEL", "gpt-6-astra")

if not api_key:
    st.warning("Configure OPENAI_API_KEY in this app's private deployment secrets to enable Samson.")

st.subheader("Internet discovery · four-tier themes")
st.caption("Recent news and optional wider-web matches are leads to inspect, not verified investment opportunities. Searches run only when requested.")
web_tier = st.selectbox("Portfolio tier to explore", list(THEMES))
web_theme = st.selectbox("Research theme", list(THEMES[web_tier]))
brave_key = os.environ.get("BRAVE_SEARCH_API_KEY") or secret("BRAVE_SEARCH_API_KEY")
st.caption("Public news search needs no key but may rate-limit shared traffic. Add BRAVE_SEARCH_API_KEY in private secrets for a separate wider web source.")
if st.button("Search Internet sources"):
    try:
        with st.spinner("Finding recent Internet coverage..."):
            found, search_errors = search_theme(web_tier, web_theme, brave_key)
        existing = {lead["url"]: lead for lead in st.session_state.get("web_leads", [])}
        for lead in found:
            existing[lead["url"]] = lead
        st.session_state.web_leads = list(existing.values())[-100:]
        st.session_state.web_last_scan = f"{web_tier} / {web_theme}"
        st.session_state.web_scan_message = f"Found {len(found)} distinct recent matches."
        for error in search_errors:
            st.warning(error)
        if not found and search_errors:
            st.session_state.web_scan_message = "No results were available from the configured sources on this attempt."
    except Exception as exc:
        st.error(f"Internet discovery failed: {exc}")
if st.session_state.get("web_scan_message"):
    st.success(st.session_state.web_scan_message)
if st.session_state.get("web_leads"):
    st.caption("Research queue for this browser session. Check the underlying article and original company or official source before treating any claim as fact.")
    st.session_state.setdefault("web_status", {})
    for i, lead in enumerate(reversed(st.session_state.web_leads)):
        with st.expander(f"{lead['title']} · {lead['theme']}"):
            st.write(f"{lead['provider']} · {lead['source']} · {lead['published']} · {lead['tier']}")
            st.link_button("Open source", lead["url"])
            choices = ["New", "Investigate", "Watch", "Dismiss"]
            current = st.session_state.web_status.get(lead["url"], "New")
            selected = st.selectbox("Research status", choices, index=choices.index(current), key=f"web_status_widget_{i}_{lead['url']}")
            st.session_state.web_status[lead["url"]] = selected
    st.caption("Statuses are session-only. Search results and statuses are not saved to the Portfolio Office export yet.")

st.divider()
st.subheader("Discovery · SEC filing leads")
st.caption("A recent filing is a research lead, not evidence of an attractive price or an investment recommendation.")
filing_form = st.selectbox(
    "Filing type",
    ["D", "8-K", "10-K", "10-Q"],
    help="D: private offering notice; 8-K: reported event; 10-K/10-Q: periodic reports.",
)
sec_user_agent = os.environ.get("SEC_USER_AGENT") or secret("SEC_USER_AGENT")
if not sec_user_agent:
    st.info("To scan EDGAR, set SEC_USER_AGENT in private secrets to an app name and contact email.")
if st.button("Scan recent SEC filings", disabled=not sec_user_agent):
    try:
        with st.spinner("Reading the official SEC filing feed..."):
            st.session_state.discovery_leads = latest_filings(filing_form, sec_user_agent)
            st.session_state.discovery_form = filing_form
    except Exception as exc:
        st.error(f"Discovery scan failed: {exc}")
if st.session_state.get("discovery_leads"):
    st.caption(f"Latest {st.session_state.discovery_form} leads. Retrieved on demand; no background scan is running.")
    for lead in st.session_state.discovery_leads:
        st.markdown(f"**[{lead['title']}]({lead['source_url']})** · filed/updated {lead['published'] or 'date unavailable'}")
    st.caption("Filing links are official SEC sources. Details, fit, risks, valuation, and investability still require review.")

st.divider()
st.subheader("Savior evaluations")
st.caption("Upload an exported Savior investment history for this session. Samson receives a summary of the latest 12 evaluations; this is not a durable portfolio record.")
uploaded = st.file_uploader("Savior investment history (.xlsx)", type="xlsx")
history = None
file_bytes = uploaded.getvalue() if uploaded is not None else None
file_fingerprint = sha256(file_bytes).hexdigest() if file_bytes is not None else None
if st.session_state.get("samson_file_fingerprint") != file_fingerprint:
    st.session_state.samson_file_fingerprint = file_fingerprint
    st.session_state.samson_messages = []
    st.session_state.samson_error = ""
if uploaded is not None:
    try:
        history = pd.read_excel(BytesIO(file_bytes), sheet_name="Investment Analyses")
        st.success(f"Loaded {len(history)} user-entered evaluations for this session.")
    except (ValueError, OSError, KeyError) as exc:
        st.error(f"Could not read the Savior export: {exc}")

context = history_context(history) + "\n\n" + lead_context(
    st.session_state.get("discovery_leads", []),
    st.session_state.get("discovery_form", filing_form),
)
context += "\n\n" + web_context([
    lead for lead in st.session_state.get("web_leads", [])
    if st.session_state.get("web_status", {}).get(lead["url"]) != "Dismiss"
])
if "office_policy" in st.session_state:
    st.page_link("pages/2_Portfolio_Office.py", label="Open Portfolio Office")
    include_office = st.checkbox(
        "Include my Portfolio Office session data in Samson's AI analysis",
        value=False,
        help="If selected, entered holdings, values, policy flags and recent decisions are sent to the configured OpenAI API with your question.",
    )
    if include_office:
        context += "\n\n" + conversation_context(
            st.session_state.office_holdings, st.session_state.office_policy,
            st.session_state.office_diligence, st.session_state.office_decisions,
        )
else:
    st.page_link("pages/2_Portfolio_Office.py", label="Set up Portfolio Office")
with st.expander("Data available to Samson"):
    st.text(context)

if "samson_messages" not in st.session_state:
    st.session_state.samson_messages = []
if "samson_error" not in st.session_state:
    st.session_state.samson_error = ""

st.subheader("Conversation")
for message in st.session_state.samson_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.session_state.samson_error:
    st.error(st.session_state.samson_error)

with st.form("samson_question", clear_on_submit=True):
    question = st.text_input("Ask about an opportunity, portfolio risk, or exit thesis")
    mode = st.radio(
        "Analysis depth",
        ["Standard (Sol, lower cost)", "Deep analysis (Astra, higher cost)"],
        horizontal=True,
    )
    sent = st.form_submit_button("Send to Samson", disabled=not api_key)

if sent and question.strip():
    st.session_state.samson_error = ""
    st.session_state.samson_messages.append({"role": "user", "content": question.strip()})
    try:
        with st.spinner("Samson is reviewing the available evidence (up to 45 seconds)..."):
            answer = ask_samson(
                st.session_state.samson_messages,
                context,
                api_key,
                deep_model if mode.startswith("Deep") else standard_model,
            )
        st.session_state.samson_messages.append({"role": "assistant", "content": answer})
    except Exception as exc:
        if getattr(exc, "code", None) == "credit_balance_exhausted" or "credit_balance_exhausted" in str(exc):
            st.session_state.samson_error = (
                "OpenAI API credit is exhausted. Add credit in your OpenAI API billing settings "
                "before sending another question. Your SEC scan works independently."
            )
        else:
            st.session_state.samson_error = f"Samson could not respond: {exc}"
    st.rerun()

with st.expander("Preview a briefing"):
    period = st.selectbox("Briefing", ["Morning", "Midday", "Evening"])
    if st.button("Generate preview", disabled=not api_key):
        try:
            with st.spinner("Preparing the briefing..."):
                st.markdown(ask_samson(
                    [{"role": "user", "content": briefing_prompt(period, context)}],
                    context,
                    api_key,
                    standard_model,
                ))
        except Exception as exc:
            st.error(f"Briefing could not be generated: {exc}")

st.info("Briefings are on demand. Research feeds, a private holdings database, and scheduled email delivery are still to be built.")
