"""Private session-based policy, holdings, diligence, scenario and decision workspace."""

from datetime import date, datetime
import json

import pandas as pd
import streamlit as st

from scoring.portfolio_office import (
    CHECKS, SHOCKS, TIERS, default_policy, stress, summarize, validate_snapshot,
)

st.set_page_config(page_title="Portfolio Office | Samson", page_icon="📊", layout="wide")
st.title("Portfolio Office")
st.caption("Four-tier investment process · draft session workspace")
st.warning(
    "Entries live only in this browser session and disappear when it ends. "
    "Export a copy if you need to keep them. This is not a reconciled account, "
    "secure document vault, or approved investment policy."
)

if "office_policy" not in st.session_state:
    st.session_state.office_policy = default_policy()
for field in ("holdings", "diligence", "decisions"):
    st.session_state.setdefault(f"office_{field}", [])

policy = st.session_state.office_policy
holdings = st.session_state.office_holdings
tab_policy, tab_holdings, tab_diligence, tab_scenarios, tab_decisions, tab_backup = st.tabs(
    ["Policy", "Holdings", "Diligence", "Stress tests", "Decisions", "Export / import"]
)

with tab_policy:
    st.subheader("Investment policy · draft")
    st.caption("The four-tier targets are a planning reference. Approval and the underlying holdings remain separate.")
    with st.form("policy_form"):
        target_cols = st.columns(4)
        targets = {
            tier: target_cols[i].number_input(tier, 0.0, 100.0, float(policy["targets"][tier]), step=1.0)
            for i, tier in enumerate(TIERS)
        }
        a, b, c = st.columns(3)
        drift = a.number_input("Allowed tier drift (percentage points)", 0.0, 50.0, float(policy["drift_pp"]))
        max_position = b.number_input("Maximum single position (% of recorded assets)", 0.0, 100.0, float(policy["max_position_pct"]))
        liquidity_months = c.number_input("Cash reserve (months of spending)", 0.0, 120.0, float(policy["liquidity_months"]))
        annual_need = st.number_input("Annual family and operating cash need ($)", min_value=0.0, value=float(policy["annual_cash_need"]), step=10000.0)
        notes = st.text_area("Exclusions, leverage rules, approval authority, and other policy notes", value=policy["notes"])
        approved_by = st.text_input("Approved by (leave blank while draft)", value=policy.get("approved_by", ""))
        saved = st.form_submit_button("Save policy in this session")
    if saved:
        if abs(sum(targets.values()) - 100) > 0.01:
            st.error("Tier targets must add to 100%.")
        else:
            st.session_state.office_policy = {
                "targets": targets, "drift_pp": drift, "max_position_pct": max_position,
                "liquidity_months": liquidity_months, "annual_cash_need": annual_need,
                "notes": notes, "approved_by": approved_by,
                "approved_on": date.today().isoformat() if approved_by else "",
            }
            st.success("Policy saved for this session.")

with tab_holdings:
    st.subheader("Whole-portfolio inventory")
    st.caption("Record all four tiers, liabilities and unfunded commitments. Values are self-entered until independently reconciled.")
    with st.form("add_holding", clear_on_submit=True):
        name = st.text_input("Asset or business name")
        tier = st.selectbox("Tier", list(TIERS))
        a, b, c = st.columns(3)
        value = a.number_input("Current recorded value ($)", min_value=0.0, step=10000.0)
        debt = b.number_input("Associated debt ($; memo field)", min_value=0.0, step=10000.0)
        unfunded = c.number_input("Unfunded commitment ($)", min_value=0.0, step=10000.0)
        a, b, c = st.columns(3)
        valuation_date = a.date_input("Valuation date", value=date.today())
        liquid_30d = b.checkbox("Accessible within 30 days")
        verified = c.checkbox("Reconciled to independent statement")
        entity = st.text_input("Owning entity or account")
        source = st.text_input("Valuation source / statement reference")
        added = st.form_submit_button("Add holding")
    if added:
        if not name.strip():
            st.error("Enter an asset name.")
        else:
            holdings.append({
                "name": name.strip(), "tier": tier, "value": value, "debt": debt,
                "unfunded": unfunded, "valuation_date": valuation_date.isoformat(),
                "liquid_30d": liquid_30d, "verified": verified,
                "entity": entity.strip(), "source": source.strip(),
            })
            st.rerun()
    if holdings:
        st.dataframe(pd.DataFrame(holdings), hide_index=True)
        chosen = st.selectbox("Remove an incorrect entry", range(len(holdings)),
                              format_func=lambda i: f"{i + 1}. {holdings[i]['name']}")
        if st.button("Remove selected holding"):
            holdings.pop(chosen)
            st.rerun()
        report = summarize(holdings, st.session_state.office_policy)
        a, b, c, d = st.columns(4)
        a.metric("Recorded asset value", f"${report['total_recorded']:,.0f}")
        b.metric("30-day accessible", f"${report['liquid_30d']:,.0f}")
        c.metric("Unfunded commitments", f"${report['unfunded']:,.0f}")
        d.metric("Associated debt (memo)", f"${report['debt']:,.0f}")
        st.table(pd.DataFrame([
            {"Tier": tier, "Target %": st.session_state.office_policy["targets"][tier],
             "Recorded %": round(report["weights"][tier], 1), "Recorded value": report["by_tier"][tier]}
            for tier in TIERS
        ]))
        for flag in report["flags"]:
            st.warning(flag)
        st.caption("Recorded asset value is not net worth: debts are shown separately, and values may be stale or unverified.")
    else:
        st.info("No holdings recorded. Samson cannot calculate actual tier weights yet.")

with tab_diligence:
    st.subheader("Candidate diligence")
    st.caption("Unknown means further review. A checked item is a recorded judgment, not an independent verification.")
    with st.form("diligence_form", clear_on_submit=True):
        candidate = st.text_input("Candidate or deal")
        candidate_tier = st.selectbox("Proposed tier", list(TIERS))
        evidence = st.text_input("Primary evidence link or document reference")
        findings = {check: st.selectbox(check, ["Unknown", "Pass", "Concern", "Hard stop"]) for check in CHECKS}
        notes = st.text_area("Evidence, unresolved questions, and next diligence step")
        logged = st.form_submit_button("Record diligence snapshot")
    if logged:
        if not candidate.strip():
            st.error("Enter a candidate name.")
        else:
            st.session_state.office_diligence.append({
                "candidate": candidate.strip(), "tier": candidate_tier,
                "as_of": datetime.now().astimezone().isoformat(timespec="seconds"),
                "evidence": evidence.strip(), "checks": findings, "notes": notes.strip(),
            })
            st.success("Snapshot recorded for this session.")
    for item in reversed(st.session_state.office_diligence):
        with st.expander(f"{item['candidate']} · {item['tier']} · {item['as_of']}"):
            st.write({"Evidence": item["evidence"], "Notes": item["notes"], "Checks": item["checks"]})
            if "Hard stop" in item["checks"].values():
                st.error("Hard stop recorded: do not advance without resolving the reason.")

with tab_scenarios:
    st.subheader("Whole-portfolio stress illustrations")
    st.caption("These are user-selected hypothetical shocks to recorded values, not forecasts or loss limits. Private valuations may react slowly in practice.")
    preset = st.selectbox("Scenario", list(SHOCKS))
    shocks = {tier: st.slider(f"{tier} value change (%)", -100, 100, int(SHOCKS[preset][i]), key=f"shock_{i}_{preset}")
              for i, tier in enumerate(TIERS)}
    if holdings:
        result = stress(holdings, shocks)
        a, b, c = st.columns(3)
        a.metric("Recorded before", f"${result['before']:,.0f}")
        b.metric("Illustrative change", f"${result['change']:,.0f}")
        c.metric("Illustrative after", f"${result['after']:,.0f}")
        st.table(pd.DataFrame([{"Tier": tier, "Shock %": shocks[tier], "Value change": result["tier_change"][tier]} for tier in TIERS]))
        st.caption("Associated debt, capital calls, cash needs, taxes, and asset-specific losses are not included in the arithmetic above. Review them separately in Holdings.")
    else:
        st.info("Enter holdings to see a portfolio-wide illustration.")

with tab_decisions:
    st.subheader("Investment committee decision log")
    with st.form("decision_form", clear_on_submit=True):
        candidate = st.text_input("Asset or proposed investment")
        action = st.selectbox("Decision", ["Investigate", "Defer", "Reject", "Approve for separate execution review", "Review reduction / exit"])
        thesis = st.text_area("Thesis and supporting evidence")
        disconfirm = st.text_area("What would disprove this thesis?")
        source = st.text_input("Evidence URL or document reference")
        funding = st.text_input("Proposed size and funding source")
        reviewer = st.text_input("Reviewer or committee")
        review_date = st.date_input("Next review date", value=date.today())
        recorded = st.form_submit_button("Record decision")
    if recorded:
        if not candidate.strip() or not thesis.strip():
            st.error("Enter the investment and a thesis.")
        else:
            st.session_state.office_decisions.append({
                "candidate": candidate.strip(), "action": action, "thesis": thesis.strip(),
                "disconfirming_test": disconfirm.strip(), "source": source.strip(),
                "funding": funding.strip(), "reviewer": reviewer.strip(),
                "review_date": review_date.isoformat(),
                "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            })
            st.success("Decision recorded for this session. Approval here does not execute a transaction.")
    for item in reversed(st.session_state.office_decisions):
        with st.expander(f"{item['candidate']} · {item['action']} · review {item['review_date']}"):
            st.json(item)

with tab_backup:
    st.subheader("Export or restore this session")
    snapshot = {
        "schema": 1, "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "policy": st.session_state.office_policy, "holdings": st.session_state.office_holdings,
        "diligence": st.session_state.office_diligence, "decisions": st.session_state.office_decisions,
    }
    st.download_button("Download private JSON copy", json.dumps(snapshot, indent=2).encode(),
                       file_name="samson_portfolio_office.json", mime="application/json")
    st.caption("The downloaded file may contain sensitive financial information. Keep it in a private location; do not commit it to GitHub.")
    uploaded = st.file_uploader("Restore a prior Portfolio Office JSON export", type="json", max_upload_size=5)
    if st.button("Restore and replace this session", disabled=uploaded is None):
        try:
            restored = validate_snapshot(json.loads(uploaded.getvalue()))
            for field, value in restored.items():
                st.session_state[f"office_{field}"] = value
            st.rerun()
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            st.error(f"Could not restore the export: {exc}")
