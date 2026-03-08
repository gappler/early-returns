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
