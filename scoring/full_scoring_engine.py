def clamp(value, low=0, high=10):
    return max(low, min(high, value))


def score_inverse_risk(value):
    return clamp(10 - value)


def calculate_full_score(responses):
    business_quality = responses.get("BQ001", 0)
    revenue = responses.get("BQ002", 0)
    growth = responses.get("BQ003", 0)
    ebitda = responses.get("BQ004", 0)
    fcf = responses.get("BQ006", 0)
    debt_to_ebitda = responses.get("BQ008", 0)

    ownership = responses.get("DQ002", 0)
    board_seat = responses.get("DQ005", False)
    voting_rights = responses.get("DQ006", False)

    roi = responses.get("RA001", 0)
    irr = responses.get("RA002", 0)
    break_even = responses.get("RA003", 0)

    litigation = responses.get("RISK001", 5)
    regulatory = responses.get("RISK002", 5)
    political = responses.get("RISK003", 5)
    nimby = responses.get("RISK004", 5)
    exit_friction = responses.get("RISK006", 5)
    contagion = responses.get("RISK007", 5)

    tax_shelter = responses.get("TAX002", 5)
    after_tax_roi = responses.get("TAX003", 0)

    strategic_fit = responses.get("FIT002", 5)
    domain = responses.get("FIT001", 5)
    time_burden = responses.get("FIT005", 0)
    swan = responses.get("FIT006", 5)

    business_score = clamp(
        (business_quality / 20 * 2)
        + (revenue / 20_000_000 * 2)
        + (growth / 50 * 2)
        + (ebitda / 5_000_000 * 2)
        + (1 if fcf > 0 else 0)
        + score_inverse_risk(debt_to_ebitda) * 0.1
    )

    deal_score = clamp(
        (ownership / 10 * 4)
        + (2 if board_seat else 0)
        + (2 if voting_rights else 0)
        + 2
    )

    return_score = clamp(
        (roi / 30 * 3)
        + (irr / 30 * 3)
        + score_inverse_risk(break_even) * 0.4
        + (after_tax_roi / 30 * 2)
    )

    risk_score = clamp(
        (
            score_inverse_risk(litigation)
            + score_inverse_risk(regulatory)
            + score_inverse_risk(political)
            + score_inverse_risk(nimby)
            + score_inverse_risk(exit_friction)
            + score_inverse_risk(contagion)
        ) / 6
    )

    tax_score = clamp((tax_shelter * 0.5) + (after_tax_roi / 30 * 5))

    fit_score = clamp(
        (strategic_fit * 0.35)
        + (domain * 0.30)
        + score_inverse_risk(time_burden / 10) * 0.15
        + (swan * 0.20)
    )

    overall = round(
        (business_score * 0.25)
        + (deal_score * 0.20)
        + (return_score * 0.20)
        + (risk_score * 0.15)
        + (tax_score * 0.10)
        + (fit_score * 0.10),
        1
    )

    red_flags = []

    if fcf < 0:
        red_flags.append("Negative free cash flow")

    if debt_to_ebitda > 6:
        red_flags.append("Debt / EBITDA greater than 6x")

    if ownership < 5:
        red_flags.append("Ownership stake below 5%")

    if break_even > 10:
        red_flags.append("Break-even period greater than 10 years")

    if regulatory >= 8:
        red_flags.append("High regulatory risk")

    if nimby >= 8:
        red_flags.append("High NIMBY / public opposition risk")

    if contagion >= 8:
        red_flags.append("High contagion risk to existing business")

    if exit_friction >= 8:
        red_flags.append("High exit friction")

    if overall >= 8.5:
        recommendation = "STRONG BUY"
    elif overall >= 7.5:
        recommendation = "BUY"
    elif overall >= 6.5:
        recommendation = "DUE DILIGENCE"
    elif overall >= 5:
        recommendation = "WATCHLIST"
    else:
        recommendation = "PASS"

    return {
        "Business Quality Score": round(business_score, 1),
        "Deal Quality Score": round(deal_score, 1),
        "Return Score": round(return_score, 1),
        "Risk / Execution Score": round(risk_score, 1),
        "Tax Efficiency Score": round(tax_score, 1),
        "Family Office Fit Score": round(fit_score, 1),
        "Overall Score": overall,
        "Recommendation": recommendation,
        "Red Flags": red_flags
    }