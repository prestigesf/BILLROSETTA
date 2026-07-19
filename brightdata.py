"""Bright Data Web Unlocker client for Medicare rate lookup.

Medicare pays a CPT code at:

    [(work RVU x work GPCI) + (PE RVU x PE GPCI) + (MP RVU x MP GPCI)] x CF

RVUs are national per CPT; GPCIs vary by locality (derived from ZIP); CF is
set annually (CY2026 = $33.4009). CMS publishes all three, but the lookup
tool is a JavaScript SPA that returns nothing to a plain HTTP GET — which is
what Web Unlocker is for.

STATUS: the live path is UNVERIFIED. Request construction is covered by
test_brightdata.py, but no real call has been made because no token exists
yet. `parse_rate` in particular is written against an assumed page shape and
WILL need adjusting once a real response is in hand.
"""
import os
import re
from typing import Optional

import requests

WEB_UNLOCKER_ENDPOINT = "https://api.brightdata.com/request"
CMS_PFS_SEARCH = "https://www.cms.gov/medicare/physician-fee-schedule/search"

# CY2026 Physician Fee Schedule conversion factor.
CONVERSION_FACTOR_2026 = 33.4009

# Fallback rates used when no token is configured. Representative, not
# authoritative — see README.
STATIC_RATES = {
    "99214": 110.50,
    "99215": 150.75,
    "99283": 250.00,
    "80053": 45.00,
}
STATIC_DEFAULT = 125.00


class RateLookupError(RuntimeError):
    """Bright Data call failed or returned something unparseable."""


class BrightDataScraper:
    """Fetches Medicare reimbursement rates via Bright Data Web Unlocker.

    Falls back to a static table when no API key is configured, so the app
    stays runnable without credentials. Every result carries its provenance
    so callers can tell a live rate from a placeholder.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        zone: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("BRIGHT_DATA_API_KEY")
        self.zone = zone or os.getenv("BRIGHT_DATA_ZONE", "web_unlocker1")
        self.timeout = timeout

    @property
    def is_live(self) -> bool:
        """True when a real API key is present. Placeholder keys don't count."""
        return bool(self.api_key) and self.api_key not in ("DEMO_KEY", "")

    def get_rate(self, cpt_code: str, zip_code: str) -> dict:
        """Return {"rate": float, "source": str} for a CPT code in a ZIP.

        Never raises — falls back to the static table on any failure so a
        scrape problem degrades the answer instead of dropping the request.
        The "source" field says which path produced the number.
        """
        cpt = cpt_code.upper().strip()

        if not self.is_live:
            return {
                "rate": STATIC_RATES.get(cpt, STATIC_DEFAULT),
                "source": "static-fallback:no-api-key",
            }

        try:
            html = self._fetch(cpt, zip_code)
            rate = self.parse_rate(html)
            return {"rate": rate, "source": "brightdata-live"}
        except (requests.RequestException, RateLookupError) as exc:
            return {
                "rate": STATIC_RATES.get(cpt, STATIC_DEFAULT),
                "source": f"static-fallback:{type(exc).__name__}",
            }

    def _fetch(self, cpt_code: str, zip_code: str) -> str:
        """POST to Web Unlocker and return the raw page body."""
        target = f"{CMS_PFS_SEARCH}?Y=0&T=4&HT=0&CT=0&H1={cpt_code}&M=5&ZIP={zip_code}"
        response = requests.post(
            WEB_UNLOCKER_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            json={"zone": self.zone, "url": target, "format": "raw"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.text

    @staticmethod
    def parse_rate(html: str) -> float:
        """Pull the non-facility price out of a CMS PFS result page.

        UNVERIFIED against a real response — see module docstring.
        """
        match = re.search(
            r"non[- ]facility\s*(?:price|rate)[^0-9$]{0,40}\$?\s*([0-9,]+\.[0-9]{2})",
            html,
            re.IGNORECASE,
        )
        if not match:
            raise RateLookupError("no non-facility price found in response")
        return float(match.group(1).replace(",", ""))
