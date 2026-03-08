"""FEC Campaign Finance Snapshot Generator."""

import os
import sys
from datetime import datetime
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


def get_independent_expenditures(candidate_id, api_key, max_pages=5):
    url = f"{FEC_BASE_URL}/schedules/schedule_e/"
    all_results = []
    params = {
        "api_key": api_key,
        "candidate_id": candidate_id,
        "cycle": 2026,
        "per_page": 100,
        "sort": "-expenditure_amount",
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
        params["last_expenditure_amount"] = last_indexes.get("last_expenditure_amount")

    return all_results


def format_currency(amount):
    return f"${amount:,.0f}"


def generate_report(
    candidate_id, candidate_name, race, totals, top_donors, employers,
    independent_expenditures, num_contributions,
):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    avg_donation = totals["receipts"] / num_contributions if num_contributions > 0 else 0

    lines = []
    lines.append(f"# {candidate_name} ({race})")
    lines.append(f"**FEC ID:** {candidate_id}  ")
    lines.append(f"**Report generated:** {now}  ")
    lines.append(f"**Data through:** {totals.get('coverage_end_date', 'N/A')}")
    lines.append("")

    # Section 1: Financial Summary
    lines.append("## Financial Summary")
    lines.append("")
    lines.append("| Metric | Amount |")
    lines.append("|--------|--------|")
    lines.append(f"| Total Raised | {format_currency(totals['receipts'])} |")
    lines.append(f"| Total Spent | {format_currency(totals['disbursements'])} |")
    lines.append(f"| Cash on Hand | {format_currency(totals['cash_on_hand_end_period'])} |")
    lines.append(f"| Avg Donation Size | {format_currency(avg_donation)} |")
    lines.append("")

    # Section 2: Top Donors
    lines.append("## Top Donors (Itemized >$200)")
    lines.append("")
    lines.append("| Rank | Name | Employer | Total |")
    lines.append("|------|------|----------|-------|")
    for i, donor in enumerate(top_donors, 1):
        lines.append(
            f"| {i} | {donor['name']} | {donor['employer']} | {format_currency(donor['total'])} |"
        )
    lines.append("")

    # Section 3: Donor Source by Employer
    lines.append("## Donor Source by Employer")
    lines.append("")
    lines.append("| Employer | Total |")
    lines.append("|----------|-------|")
    for emp in employers[:15]:
        lines.append(f"| {emp['employer']} | {format_currency(emp['total'])} |")
    lines.append("")

    # Section 4: Outside Money
    lines.append("## Independent Expenditures (Outside Money)")
    lines.append("")
    if independent_expenditures:
        lines.append("| Committee | Amount | Support/Oppose |")
        lines.append("|-----------|--------|----------------|")
        for ie in independent_expenditures:
            committee_name = ie.get("committee", {}).get("name", "UNKNOWN")
            amount = ie.get("expenditure_amount", 0)
            so = "Support" if ie.get("support_oppose_indicator") == "S" else "Oppose"
            lines.append(f"| {committee_name} | {format_currency(amount)} | {so} |")
    else:
        lines.append("No independent expenditures reported for this cycle.")
    lines.append("")

    lines.append("---")
    lines.append("*Source: FEC API | Generated by Early Returns*")

    return "\n".join(lines)


def run_snapshot(candidate_id, candidate_name, race):
    api_key = get_api_key()
    print(f"Fetching data for {candidate_name} ({race})...")

    print("  -> Candidate totals...")
    totals = get_candidate_totals(candidate_id, api_key)

    print("  -> Itemized contributions...")
    contributions = get_itemized_contributions(candidate_id, api_key)

    print("  -> Independent expenditures...")
    indie = get_independent_expenditures(candidate_id, api_key)

    top_donors = aggregate_top_donors(contributions)
    employers = aggregate_by_employer(contributions)

    report = generate_report(
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        race=race,
        totals=totals,
        top_donors=top_donors,
        employers=employers,
        independent_expenditures=indie,
        num_contributions=len(contributions),
    )

    os.makedirs("reports", exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"reports/{candidate_id}_{date_str}.md"
    with open(filename, "w") as f:
        f.write(report)

    print(f"\nReport saved to {filename}")
    return filename


if __name__ == "__main__":
    # Default test candidate: Don Davis, NC-01
    cid = sys.argv[1] if len(sys.argv) > 1 else "H8NC01087"
    name = sys.argv[2] if len(sys.argv) > 2 else "Don Davis"
    race = sys.argv[3] if len(sys.argv) > 3 else "NC-01"
    run_snapshot(cid, name, race)
