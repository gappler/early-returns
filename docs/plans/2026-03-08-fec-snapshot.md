# FEC Campaign Finance Snapshot — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python script that pulls campaign finance data from the FEC API for a given candidate and outputs a markdown snapshot report.

**Architecture:** Single script (`scripts/fec_snapshot.py`) using `requests` to hit three FEC API endpoint families. Config via `.env` with `python-dotenv`. Output to `reports/` as timestamped markdown. Tests use `pytest` with mocked HTTP responses.

**Tech Stack:** Python 3, requests, python-dotenv, pytest, unittest.mock

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore` (or modify if exists)

**Step 1: Create requirements.txt**

```
requests>=2.31.0
python-dotenv>=1.0.0
pytest>=7.4.0
```

**Step 2: Create .env.example**

```
FEC_API_KEY=your_api_key_here
```

**Step 3: Update .gitignore**

Add these entries:
```
.env
__pycache__/
*.pyc
reports/
```

**Step 4: Create virtual environment and install**

Run: `cd /Users/gregappler/Claude\ Code\ Projects/early-returns && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

**Step 5: Create reports directory with .gitkeep**

```bash
mkdir -p reports
touch reports/.gitkeep
```

**Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore reports/.gitkeep
git commit -m "feat: add project setup for FEC snapshot script"
```

---

### Task 2: FEC API Client — Candidate Totals

**Files:**
- Create: `scripts/fec_snapshot.py`
- Create: `tests/test_fec_snapshot.py`

**Step 1: Write the failing test**

```python
# tests/test_fec_snapshot.py
import json
from unittest.mock import patch, MagicMock
from scripts.fec_snapshot import get_candidate_totals

MOCK_TOTALS_RESPONSE = {
    "results": [
        {
            "receipts": 1500000.00,
            "disbursements": 800000.00,
            "cash_on_hand_end_period": 700000.00,
            "individual_contributions": 1200000.00,
            "contribution_refunds": 5000.00,
            "coverage_end_date": "2026-06-30",
            "cycle": 2026,
        }
    ]
}


@patch("scripts.fec_snapshot.requests.get")
def test_get_candidate_totals(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_TOTALS_RESPONSE
    mock_get.return_value = mock_response

    result = get_candidate_totals("H8NC01087", "DEMO_KEY")

    assert result["receipts"] == 1500000.00
    assert result["disbursements"] == 800000.00
    assert result["cash_on_hand_end_period"] == 700000.00
    mock_get.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/gregappler/Claude\ Code\ Projects/early-returns && python -m pytest tests/test_fec_snapshot.py::test_get_candidate_totals -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

```python
# scripts/fec_snapshot.py
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
```

Also create `scripts/__init__.py` and `tests/__init__.py` (empty files) so imports work.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_fec_snapshot.py::test_get_candidate_totals -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/ tests/
git commit -m "feat: add FEC candidate totals retrieval"
```

---

### Task 3: Schedule A — Itemized Contributions (Top Donors + Industry)

**Files:**
- Modify: `scripts/fec_snapshot.py`
- Modify: `tests/test_fec_snapshot.py`

**Step 1: Write the failing tests**

Add to `tests/test_fec_snapshot.py`:

```python
from scripts.fec_snapshot import get_itemized_contributions, aggregate_top_donors, aggregate_by_employer

MOCK_SCHEDULE_A_PAGE1 = {
    "results": [
        {"contributor_name": "SMITH, JOHN", "contributor_employer": "ACME CORP", "contribution_receipt_amount": 2900.00},
        {"contributor_name": "DOE, JANE", "contributor_employer": "ACME CORP", "contribution_receipt_amount": 1500.00},
        {"contributor_name": "SMITH, JOHN", "contributor_employer": "ACME CORP", "contribution_receipt_amount": 500.00},
        {"contributor_name": "WILLIAMS, BOB", "contributor_employer": "STATE UNIVERSITY", "contribution_receipt_amount": 1000.00},
    ],
    "pagination": {"last_indexes": None, "pages": 1},
}


@patch("scripts.fec_snapshot.requests.get")
def test_get_itemized_contributions(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_SCHEDULE_A_PAGE1
    mock_get.return_value = mock_response

    results = get_itemized_contributions("H8NC01087", "DEMO_KEY", max_pages=1)
    assert len(results) == 4


def test_aggregate_top_donors():
    contributions = [
        {"contributor_name": "SMITH, JOHN", "contributor_employer": "ACME CORP", "contribution_receipt_amount": 2900.00},
        {"contributor_name": "SMITH, JOHN", "contributor_employer": "ACME CORP", "contribution_receipt_amount": 500.00},
        {"contributor_name": "DOE, JANE", "contributor_employer": "ACME CORP", "contribution_receipt_amount": 1500.00},
    ]
    top = aggregate_top_donors(contributions, limit=2)
    assert top[0]["name"] == "SMITH, JOHN"
    assert top[0]["total"] == 3400.00
    assert top[1]["name"] == "DOE, JANE"
    assert len(top) == 2


def test_aggregate_by_employer():
    contributions = [
        {"contributor_name": "SMITH, JOHN", "contributor_employer": "ACME CORP", "contribution_receipt_amount": 2900.00},
        {"contributor_name": "DOE, JANE", "contributor_employer": "ACME CORP", "contribution_receipt_amount": 1500.00},
        {"contributor_name": "WILLIAMS, BOB", "contributor_employer": "STATE UNIVERSITY", "contribution_receipt_amount": 1000.00},
    ]
    result = aggregate_by_employer(contributions)
    assert result[0]["employer"] == "ACME CORP"
    assert result[0]["total"] == 4400.00
    assert result[1]["employer"] == "STATE UNIVERSITY"
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_fec_snapshot.py -k "schedule_a or top_donors or employer" -v`
Expected: FAIL — functions not defined

**Step 3: Write implementation**

Add to `scripts/fec_snapshot.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_fec_snapshot.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add scripts/fec_snapshot.py tests/test_fec_snapshot.py
git commit -m "feat: add itemized contributions with donor and employer aggregation"
```

---

### Task 4: Schedule E — Independent Expenditures

**Files:**
- Modify: `scripts/fec_snapshot.py`
- Modify: `tests/test_fec_snapshot.py`

**Step 1: Write the failing test**

Add to `tests/test_fec_snapshot.py`:

```python
from scripts.fec_snapshot import get_independent_expenditures

MOCK_SCHEDULE_E_RESPONSE = {
    "results": [
        {
            "committee": {"name": "AMERICANS FOR PROSPERITY"},
            "expenditure_amount": 250000.00,
            "support_oppose_indicator": "O",
            "expenditure_description": "TV ADS",
        },
        {
            "committee": {"name": "HOUSE MAJORITY PAC"},
            "expenditure_amount": 500000.00,
            "support_oppose_indicator": "S",
            "expenditure_description": "DIGITAL ADS",
        },
    ],
    "pagination": {"last_indexes": None, "pages": 1},
}


@patch("scripts.fec_snapshot.requests.get")
def test_get_independent_expenditures(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_SCHEDULE_E_RESPONSE
    mock_get.return_value = mock_response

    result = get_independent_expenditures("H8NC01087", "DEMO_KEY")
    assert len(result) == 2
    assert result[0]["committee"]["name"] == "AMERICANS FOR PROSPERITY"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fec_snapshot.py::test_get_independent_expenditures -v`
Expected: FAIL

**Step 3: Write implementation**

Add to `scripts/fec_snapshot.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_fec_snapshot.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add scripts/fec_snapshot.py tests/test_fec_snapshot.py
git commit -m "feat: add independent expenditures retrieval"
```

---

### Task 5: Markdown Report Generator

**Files:**
- Modify: `scripts/fec_snapshot.py`
- Modify: `tests/test_fec_snapshot.py`

**Step 1: Write the failing test**

Add to `tests/test_fec_snapshot.py`:

```python
from scripts.fec_snapshot import generate_report


def test_generate_report():
    totals = {
        "receipts": 1500000.00,
        "disbursements": 800000.00,
        "cash_on_hand_end_period": 700000.00,
        "individual_contributions": 1200000.00,
        "coverage_end_date": "2026-06-30",
    }
    top_donors = [
        {"name": "SMITH, JOHN", "employer": "ACME CORP", "total": 3400.00},
        {"name": "DOE, JANE", "employer": "ACME CORP", "total": 1500.00},
    ]
    employers = [
        {"employer": "ACME CORP", "total": 4900.00},
        {"employer": "STATE UNIVERSITY", "total": 1000.00},
    ]
    indie_expends = [
        {
            "committee": {"name": "HOUSE MAJORITY PAC"},
            "expenditure_amount": 500000.00,
            "support_oppose_indicator": "S",
        },
        {
            "committee": {"name": "AMERICANS FOR PROSPERITY"},
            "expenditure_amount": 250000.00,
            "support_oppose_indicator": "O",
        },
    ]
    num_contributions = 600

    report = generate_report(
        candidate_id="H8NC01087",
        candidate_name="Don Davis",
        race="NC-01",
        totals=totals,
        top_donors=top_donors,
        employers=employers,
        independent_expenditures=indie_expends,
        num_contributions=num_contributions,
    )

    assert "# Don Davis (NC-01)" in report
    assert "$1,500,000" in report
    assert "$700,000" in report
    assert "SMITH, JOHN" in report
    assert "ACME CORP" in report
    assert "HOUSE MAJORITY PAC" in report
    assert "Support" in report
    assert "Oppose" in report
    assert "$2,500" in report  # average donor size: 1500000 / 600
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fec_snapshot.py::test_generate_report -v`
Expected: FAIL

**Step 3: Write implementation**

Add to `scripts/fec_snapshot.py`:

```python
from datetime import datetime


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
    lines.append(f"| Metric | Amount |")
    lines.append(f"|--------|--------|")
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
    lines.append(f"*Source: FEC API | Generated by Early Returns*")

    return "\n".join(lines)
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_fec_snapshot.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add scripts/fec_snapshot.py tests/test_fec_snapshot.py
git commit -m "feat: add markdown report generator"
```

---

### Task 6: Main Entry Point + File Output

**Files:**
- Modify: `scripts/fec_snapshot.py`

**Step 1: Add main function and CLI entry point**

Add to `scripts/fec_snapshot.py`:

```python
import sys


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
```

**Step 2: Test manually**

Run: `cd /Users/gregappler/Claude\ Code\ Projects/early-returns && python -m scripts.fec_snapshot`

Expected: Script runs, prints progress, saves report to `reports/H8NC01087_2026-03-08.md`

**Step 3: Commit**

```bash
git add scripts/fec_snapshot.py
git commit -m "feat: add CLI entry point and file output"
```

---
