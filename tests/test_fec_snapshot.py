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
