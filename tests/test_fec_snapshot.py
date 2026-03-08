import json
from unittest.mock import patch, MagicMock
from scripts.fec_snapshot import get_candidate_totals, get_itemized_contributions, aggregate_top_donors, aggregate_by_employer, get_independent_expenditures, generate_report

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

    results = get_itemized_contributions("C00795211", "DEMO_KEY", max_pages=1)
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


def test_generate_report():
    totals = {
        "receipts": 1500000.00,
        "disbursements": 800000.00,
        "last_cash_on_hand_end_period": 700000.00,
        "individual_contributions": 1200000.00,
        "individual_itemized_contributions": 900000.00,
        "individual_unitemized_contributions": 300000.00,
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
    assert "$2,000" in report  # avg individual donation: 1200000 / 600
