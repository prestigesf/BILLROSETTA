"""Live integration test — hits the real Bright Data Web Unlocker API.

Skipped automatically unless BRIGHT_DATA_API_KEY and BRIGHT_DATA_ZONE are set.
Run manually with:
    pytest -m integration -s
"""
import os
import pytest

from brightdata import BrightDataScraper


@pytest.mark.integration
def test_live_brightdata_lookup():
    api_key = os.getenv("BRIGHT_DATA_API_KEY")
    zone = os.getenv("BRIGHT_DATA_ZONE")
    if not api_key or not zone:
        pytest.skip("BRIGHT_DATA_API_KEY / BRIGHT_DATA_ZONE not set")

    client = BrightDataScraper()
    result = client.get_rate("99214", "94110")

    assert result["source"] == "brightdata-live", (
        f"Expected 'brightdata-live', got '{result['source']}' — "
        "regex or URL likely needs adjustment against the real response."
    )
    assert isinstance(result["rate"], float)
    assert result["rate"] > 0
    print(f"\nLIVE: CPT 99214 @ 94110 = ${result['rate']:.2f} (source: {result['source']})")
