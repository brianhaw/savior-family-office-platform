"""Transparent session-based portfolio calculations for Samson's office prototype."""

from datetime import date
from math import isfinite

TIERS = {
    "1 · Capital Preservation": 25.0,
    "2 · Core Compounding": 25.0,
    "3 · Proven Wealth Builders": 35.0,
    "4 · Asymmetric Opportunities": 15.0,
}

CHECKS = (
    "Identity and ownership", "Audited or independently checked financials",
    "Management and incentives", "Customer demand and concentration",
    "Legal and regulatory", "Valuation and terms", "Fees and conflicts",
    "Liquidity and exit rights", "Savior hard stops", "Portfolio fit and funding",
)

SHOCKS = {
    "Recession illustration": (-5, -25, -40, -65),
    "Rate and credit squeeze illustration": (-3, -20, -35, -50),
    "Custom": (0, 0, 0, 0),
}


def default_policy():
    return {
        "targets": dict(TIERS), "drift_pp": 5.0,
        "max_position_pct": 15.0, "liquidity_months": 12.0,
        "annual_cash_need": 0.0, "notes": "Draft policy; requires owner approval.",
        "approved_by": "", "approved_on": "",
    }


def _money(value):
    number = float(value)
    if not isfinite(number) or number < 0:
        raise ValueError("Amounts must be finite and nonnegative")
    return number


def summarize(holdings, policy):
    """Use recorded values only; label incomplete and unverified inputs."""
    values = {tier: 0.0 for tier in TIERS}
    liquid = 0.0
    unfunded = 0.0
    total_debt = 0.0
    for holding in holdings:
        tier = holding["tier"]
        if tier not in TIERS:
            raise ValueError(f"Unknown tier: {tier}")
        value = _money(holding["value"])
        values[tier] += value
        if holding.get("liquid_30d"):
            liquid += value
        unfunded += _money(holding.get("unfunded", 0))
        total_debt += _money(holding.get("debt", 0))
    total = sum(values.values())
    weights = {tier: 100 * value / total if total else 0 for tier, value in values.items()}
    flags = []
    if total:
        for tier, weight in weights.items():
            if abs(weight - float(policy["targets"][tier])) > float(policy["drift_pp"]):
                flags.append(f"{tier}: {weight:.1f}% is outside the target band")
        for holding in holdings:
            if 100 * float(holding["value"]) / total > float(policy["max_position_pct"]):
                flags.append(f"{holding['name']}: recorded position exceeds the single-position limit")
    annual = _money(policy["annual_cash_need"])
    required = annual * float(policy["liquidity_months"]) / 12 + unfunded
    if annual or unfunded:
        if liquid < required:
            flags.append("Recorded 30-day liquidity is below cash needs plus unfunded commitments")
    else:
        flags.append("Cash needs are unknown; liquidity coverage cannot be assessed")
    if any(not h.get("verified") for h in holdings):
        flags.append("Some holding values are unverified")
    if any(h.get("valuation_date", "") < date.today().isoformat()[:7] for h in holdings):
        flags.append("Some valuations predate the current month")
    return {
        "total_recorded": total, "by_tier": values, "weights": weights,
        "liquid_30d": liquid, "unfunded": unfunded, "debt": total_debt,
        "required_liquidity": required, "flags": flags,
    }


def stress(holdings, shocks):
    """Apply user-visible illustrative shocks to recorded values, without prediction."""
    current = sum(_money(h["value"]) for h in holdings)
    impact = {tier: 0.0 for tier in TIERS}
    for holding in holdings:
        tier = holding["tier"]
        shock = float(shocks[tier])
        if not isfinite(shock) or shock < -100:
            raise ValueError("Shock must be finite and at least -100%")
        impact[tier] += _money(holding["value"]) * shock / 100
    return {
        "before": current, "change": sum(impact.values()),
        "after": current + sum(impact.values()), "tier_change": impact,
    }


def validate_snapshot(data):
    """Reject malformed imports before replacing the user's session state."""
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ValueError("Unsupported Portfolio Office export")
    policy = data.get("policy")
    if not isinstance(policy, dict) or set(policy.get("targets", {})) != set(TIERS):
        raise ValueError("Invalid tier policy")
    if abs(sum(float(x) for x in policy["targets"].values()) - 100) > 0.01:
        raise ValueError("Tier targets must add to 100%")
    for target in policy["targets"].values():
        if _money(target) > 100:
            raise ValueError("Tier targets must be between 0 and 100%")
    for key in ("drift_pp", "max_position_pct", "liquidity_months", "annual_cash_need"):
        _money(policy[key])
    for field in ("holdings", "diligence", "decisions"):
        if not isinstance(data.get(field), list) or len(data[field]) > 1000:
            raise ValueError(f"Invalid {field} list")
    for holding in data["holdings"]:
        if not isinstance(holding, dict) or not isinstance(holding.get("name"), str):
            raise ValueError("Invalid holding")
    for field in ("diligence", "decisions"):
        if any(not isinstance(item, dict) for item in data[field]):
            raise ValueError(f"Invalid {field} entry")
    summarize(data["holdings"], policy)
    return {key: data[key] for key in ("policy", "holdings", "diligence", "decisions")}


def conversation_context(holdings, policy, diligence, decisions):
    """Bounded user-entered office context, included only by explicit UI choice."""
    report = summarize(holdings, policy)
    lines = [
        "User-entered, session-only Portfolio Office data; not independently verified:",
        f"Policy approval: {policy.get('approved_by') or 'draft / unapproved'}",
        f"Tier targets: {policy['targets']}",
        f"Recorded value: {report['total_recorded']:.0f}; 30-day accessible: {report['liquid_30d']:.0f}; "
        f"unfunded: {report['unfunded']:.0f}; associated debt: {report['debt']:.0f}",
        f"Recorded tier weights: {report['weights']}",
        f"Policy/data flags: {report['flags']}",
    ]
    for holding in holdings[-30:]:
        lines.append(f"Holding: {holding['name']} | {holding['tier']} | value {holding['value']} "
                     f"as of {holding.get('valuation_date', '?')} | verified {holding.get('verified', False)}")
    for item in diligence[-8:]:
        lines.append(f"Diligence: {item.get('candidate', '')} | {item.get('checks', {})} | "
                     f"evidence {item.get('evidence', '')}")
    for item in decisions[-8:]:
        lines.append(f"Decision: {item.get('candidate', '')} | {item.get('action', '')} | "
                     f"review {item.get('review_date', '')} | thesis {item.get('thesis', '')[:400]}")
    return "\n".join(lines)
