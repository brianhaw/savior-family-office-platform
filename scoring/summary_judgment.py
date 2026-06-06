def generate_summary_judgment(full_results):
    score = full_results["Overall Score"]
    recommendation = full_results["Recommendation"]
    red_flags = full_results["Red Flags"]

    strengths = []
    concerns = []

    if full_results["Business Quality Score"] >= 7:
        strengths.append("business quality appears strong")

    if full_results["Deal Quality Score"] >= 7:
        strengths.append("deal terms appear attractive")

    if full_results["Return Score"] >= 7:
        strengths.append("projected returns appear favorable")

    if full_results["Risk / Execution Score"] < 6:
        concerns.append("execution or risk profile is elevated")

    if full_results["Tax Efficiency Score"] < 6:
        concerns.append("tax efficiency may be weak")

    if full_results["Family Office Fit Score"] < 6:
        concerns.append("family office fit may be limited")

    if red_flags:
        concerns.append("red flags were identified that require further review")

    if recommendation in ["STRONG BUY", "BUY"]:
        opening = "This investment appears favorable based on the current scoring model."
    elif recommendation == "DUE DILIGENCE":
        opening = "This investment may be viable, but additional diligence is required before committing capital."
    elif recommendation == "WATCHLIST":
        opening = "This investment should remain under observation but does not yet justify immediate commitment."
    else:
        opening = "This investment does not appear attractive based on the current scoring model."

    judgment = opening

    if strengths:
        judgment += " Key strengths include " + ", ".join(strengths) + "."

    if concerns:
        judgment += " Key concerns include " + ", ".join(concerns) + "."

    judgment += f" The current overall score is {score}, producing a recommendation of {recommendation}."

    return judgment