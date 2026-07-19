"""Tests for the Bright Data client.

Covers request construction, parsing, and fallback behaviour by stubbing the
HTTP layer. The live network path is NOT covered — that needs a real token.
"""
from unittest.mock import patch

import pytest
import requests

from brightdata import BrightDataScraper, RateLookupError


def test_no_key_uses_static_fallback():
    s = BrightDataScraper(api_key=None)
    result = s.get_rate("99214", "94110")
    assert result["rate"] == 110.50
    assert result["source"] == "static-fallback:no-api-key"


def test_demo_key_is_not_treated_as_live():
    assert not BrightDataScraper(api_key="DEMO_KEY").is_live


def test_unknown_cpt_gets_default_rate():
    result = BrightDataScraper(api_key=None).get_rate("00000", "94110")
    assert result["rate"] == 125.00


def test_request_is_built_correctly():
    """The Web Unlocker payload must match Bright Data's documented shape."""
    s = BrightDataScraper(api_key="test-key-123", zone="my_zone")

    with patch("brightdata.requests.post") as post:
        post.return_value.text = "Non-Facility Price: $110.50"
        post.return_value.raise_for_status.return_value = None
        result = s.get_rate("99214", "94110")

    args, kwargs = post.call_args
    assert args[0] == "https://api.brightdata.com/request"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key-123"
    assert kwargs["json"]["zone"] == "my_zone"
    assert kwargs["json"]["format"] == "raw"
    assert "99214" in kwargs["json"]["url"]
    assert "94110" in kwargs["json"]["url"]
    assert result == {"rate": 110.50, "source": "brightdata-live"}


def test_network_error_falls_back_not_raises():
    s = BrightDataScraper(api_key="test-key-123")
    with patch("brightdata.requests.post", side_effect=requests.Timeout()):
        result = s.get_rate("99214", "94110")
    assert result["rate"] == 110.50
    assert result["source"] == "static-fallback:Timeout"


def test_unparseable_response_falls_back():
    s = BrightDataScraper(api_key="test-key-123")
    with patch("brightdata.requests.post") as post:
        post.return_value.text = "<html>Access denied</html>"
        post.return_value.raise_for_status.return_value = None
        result = s.get_rate("99214", "94110")
    assert result["source"] == "static-fallback:RateLookupError"


@pytest.mark.parametrize(
    "html,expected",
    [
        ("Non-Facility Price: $110.50", 110.50),
        ("non facility rate $1,250.75", 1250.75),
        ("NON-FACILITY PRICE $45.00", 45.00),
    ],
)
def test_parse_rate_variants(html, expected):
    assert BrightDataScraper.parse_rate(html) == expected


def test_parse_rate_rejects_junk():
    with pytest.raises(RateLookupError):
        BrightDataScraper.parse_rate("<html>nothing here</html>")
