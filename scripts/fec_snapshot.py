"""FEC Campaign Finance Snapshot Generator."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

FEC_BASE_URL = "https://api.open.fec.gov/v1"


def get_api_key():
    return os.getenv("FEC_API_KEY", "DEMO_KEY")


def get_candidate_totals(candidate_id, api_key):
    url = f"{FEC_BASE_URL}/candidate/{candidate_id}/totals/"
    params = {"api_key": api_key, "cycle": 2026}
    response = requests.get(url, params=params)
    response.raise_for_status()
    results = response.json()["results"]
    if not results:
        raise ValueError(f"No financial data found for {candidate_id}")
    return results[0]


def get_itemized_contributions(candidate_id, api_key, max_pages=5):
    url = f"{FEC_BASE_URL}/schedules/schedule_a/"
    all_results = []
    params = {
        "api_key": api_key,
        "candidate_id": candidate_id,
        "two_year_transaction_period": 2026,
        "is_individual": True,
        "per_page": 100,
        "sort": "-contribution_receipt_amount",
    }

    for page in range(max_pages):
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        all_results.extend(data["results"])

        last_indexes = data["pagination"].get("last_indexes")
        if not last_indexes:
            break
        params["last_index"] = last_indexes.get("last_index")
        params["last_contribution_receipt_amount"] = last_indexes.get(
            "last_contribution_receipt_amount"
        )

    return all_results


def aggregate_top_donors(contributions, limit=20):
    donor_totals = {}
    for c in contributions:
        name = c.get("contributor_name", "UNKNOWN")
        employer = c.get("contributor_employer", "NOT PROVIDED")
        amount = c.get("contribution_receipt_amount", 0)
        if name not in donor_totals:
            donor_totals[name] = {"name": name, "employer": employer, "total": 0}
        donor_totals[name]["total"] += amount

    sorted_donors = sorted(donor_totals.values(), key=lambda d: d["total"], reverse=True)
    return sorted_donors[:limit]


def aggregate_by_employer(contributions):
    employer_totals = {}
    for c in contributions:
        employer = c.get("contributor_employer", "NOT PROVIDED")
        amount = c.get("contribution_receipt_amount", 0)
        if not employer or employer.strip() == "":
            employer = "NOT PROVIDED"
        employer = employer.upper().strip()
        employer_totals[employer] = employer_totals.get(employer, 0) + amount

    sorted_employers = sorted(
        [{"employer": k, "total": v} for k, v in employer_totals.items()],
        key=lambda e: e["total"],
        reverse=True,
    )
    return sorted_employers
