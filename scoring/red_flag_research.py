from urllib.parse import quote_plus


def build_search_url(query):
    return "https://www.google.com/search?q=" + quote_plus(query)


def generate_red_flag_searches(company_name, website, ceo_name, state, industry):
    searches = []

    base_terms = [
        "lawsuit",
        "SEC enforcement",
        "fraud",
        "bankruptcy",
        "complaints",
        "BBB complaints",
        "regulatory action",
        "bad reviews",
        "criminal",
        "civil case"
    ]

    for term in base_terms:
        searches.append({
            "Category": "Company Red Flags",
            "Search": f"{company_name} {term}",
            "URL": build_search_url(f"{company_name} {term}")
        })

    if website:
        searches.append({
            "Category": "Website / Domain",
            "Search": f"site:{website} lawsuit OR complaint OR fraud",
            "URL": build_search_url(f"site:{website} lawsuit OR complaint OR fraud")
        })

    if ceo_name:
        executive_terms = [
            "lawsuit",
            "fraud",
            "SEC",
            "FINRA",
            "bankruptcy",
            "criminal",
            "complaints",
            "failed company"
        ]

        for term in executive_terms:
            searches.append({
                "Category": "CEO / Founder Red Flags",
                "Search": f"{ceo_name} {term}",
                "URL": build_search_url(f"{ceo_name} {term}")
            })

    if state:
        searches.append({
            "Category": "State / Licensing",
            "Search": f"{company_name} {state} license violation",
            "URL": build_search_url(f"{company_name} {state} license violation")
        })

    if industry:
        searches.append({
            "Category": "Industry-Specific",
            "Search": f"{company_name} {industry} regulatory violation",
            "URL": build_search_url(f"{company_name} {industry} regulatory violation")
        })

    searches.append({
        "Category": "SEC EDGAR",
        "Search": f"{company_name} SEC EDGAR",
        "URL": build_search_url(f"{company_name} SEC EDGAR")
    })

    searches.append({
        "Category": "Court Records",
        "Search": f"{company_name} CourtListener lawsuit",
        "URL": build_search_url(f"{company_name} CourtListener lawsuit")
    })

    searches.append({
        "Category": "Sanctions / Watchlists",
        "Search": f"{company_name} OFAC sanctions",
        "URL": build_search_url(f"{company_name} OFAC sanctions")
    })

    return searches