"""Transfer only sourced lead facts into Savior's questionnaire widgets."""


def prepare_prefill(lead, evidence=None):
    values = {"savior_company_name": lead.get("candidate_name") or "",
              "savior_revenue": 0.0, "savior_revenue_growth": 0.0,
              "savior_free_cash_flow": 0.0}
    sources = [lead["url"]] if lead.get("url") else []
    verified = []
    if evidence:
        values["savior_company_name"] = evidence.get("registrant") or values["savior_company_name"]
        if evidence.get("revenue"):
            values["savior_revenue"] = float(evidence["revenue"]["value"])
            verified.append("Annual revenue")
        if evidence.get("growth_pct") is not None:
            values["savior_revenue_growth"] = float(evidence["growth_pct"])
            verified.append("Revenue growth")
        if evidence.get("fcf"):
            values["savior_free_cash_flow"] = float(evidence["fcf"]["value"])
            verified.append("Free cash flow (operating cash less property/equipment purchases)")
        if evidence.get("source"):
            sources.insert(0, evidence["source"])
    return {"values": values, "sources": sources, "verified": verified,
            "company": values["savior_company_name"]}
