import json
from unittest.mock import patch, MagicMock
from scripts.fec_snapshot import get_candidate_totals, get_itemized_contributions, aggregate_top_donors, aggregate_by_employer

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
