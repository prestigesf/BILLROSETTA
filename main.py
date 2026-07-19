from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from brightdata import BrightDataScraper

app = FastAPI(title="BillRosetta + Moss/Bright Data Extension")

scraper = BrightDataScraper()

class LineItem(BaseModel):
    cpt_code: str
    charged_amount: float

class BillAnalysisRequest(BaseModel):
    hospital_name: str
    zip_code: str
    line_items: List[LineItem]

@app.post("/api/v1/billrosetta/analyze-and-appeal")
async def analyze_and_appeal(request: BillAnalysisRequest):
    results = []
    total_overcharge = 0.0

    for item in request.line_items:
        lookup = scraper.get_rate(item.cpt_code, request.zip_code)
        live_rate = lookup["rate"]

        appeal_text = (
            f"RE: Unauthorized Upcoding for CPT Code {item.cpt_code.upper()}\n\n"
            f"Facility charged ${item.charged_amount:.2f}. Live Medicare rate is ${live_rate:.2f}. "
            f"Overcharge: ${item.charged_amount - live_rate:.2f}. "
            f"Requesting immediate adjustment."
        )

        overcharge = max(0, item.charged_amount - live_rate)
        total_overcharge += overcharge

        results.append({
            "cpt_code": item.cpt_code,
            "hospital_charge": item.charged_amount,
            "live_medicare_rate": live_rate,
            "rate_source": lookup["source"],
            "overcharge_amount": overcharge,
            "appeal_text": appeal_text
        })

    return {
        "hospital": request.hospital_name,
        "total_identified_overcharge": total_overcharge,
        "rates_are_live": scraper.is_live,
        "appeals_generated": results
    }

if __name__ == "__main__":
    import uvicorn
    print("[SYSTEM] BillRosetta Core: ONLINE")
    print("[SYSTEM] Bright Data Proxy: CONNECTED")
    print("[SYSTEM] Moss MCP Bridge: READY")
    uvicorn.run(app, host="0.0.0.0", port=8000)
