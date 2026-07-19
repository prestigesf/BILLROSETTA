"""End-to-end smoke test for BillRosetta Moss Bridge.
Runs standalone (`python verify_16_run.py`) or via pytest.
"""
import sys
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

SAMPLE = {
    "hospital_name": "SF General",
    "zip_code": "94110",
    "line_items": [
        {"cpt_code": "99214", "charged_amount": 850.00},
        {"cpt_code": "99215", "charged_amount": 1200.00},
        {"cpt_code": "99283", "charged_amount": 2400.00},
        {"cpt_code": "80053", "charged_amount": 320.00},
    ],
}
EXPECTED = (850 - 110.50) + (1200 - 150.75) + (2400 - 250.00) + (320 - 45.00)


def test_analyze_and_appeal():
    r = client.post("/api/v1/billrosetta/analyze-and-appeal", json=SAMPLE)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["hospital"] == "SF General"
    assert len(data["appeals_generated"]) == 4
    assert abs(data["total_identified_overcharge"] - EXPECTED) < 0.01
    for row in data["appeals_generated"]:
        assert row["appeal_text"].startswith("RE: Unauthorized Upcoding")


if __name__ == "__main__":
    test_analyze_and_appeal()
    print(f"[VERIFY] ALL CHECKS PASSED — total overcharge ${EXPECTED:.2f}")
    sys.exit(0)
