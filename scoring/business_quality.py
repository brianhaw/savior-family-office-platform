def score_years_in_business(years):
    if years >= 20:
        return 10
    elif years >= 10:
        return 8
    elif years >= 5:
        return 6
    elif years >= 2:
        return 3
    else:
        return 1


def score_revenue(revenue):
    if revenue >= 20_000_000:
        return 10
    elif revenue >= 5_000_000:
        return 8
    elif revenue >= 1_000_000:
        return 6
    elif revenue >= 500_000:
        return 4
    elif revenue > 0:
        return 2
    else:
        return 0


def score_growth(growth_percent):
    if growth_percent >= 50:
        return 10
    elif growth_percent >= 20:
        return 8
    elif growth_percent >= 10:
        return 6
    elif growth_percent >= 0:
        return 4
    else:
        return 1


def calculate_business_quality(responses):
    years = responses.get("BQ001", 0)
    revenue = responses.get("BQ002", 0)
    growth = responses.get("BQ003", 0)

    years_score = score_years_in_business(years)
    revenue_score = score_revenue(revenue)
    growth_score = score_growth(growth)

    final_score = round(
        (years_score * 0.35) +
        (revenue_score * 0.40) +
        (growth_score * 0.25),
        1
    )

    return {
        "years_score": years_score,
        "revenue_score": revenue_score,
        "growth_score": growth_score,
        "business_quality_score": final_score
    }