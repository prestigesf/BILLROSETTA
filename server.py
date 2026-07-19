"""MCP server exposing BillRosetta bill analysis as an agent tool.

Runs standalone over stdio — does NOT require main.py to be serving on :8000.
It calls the same analysis logic in-process, so there is one thing to start,
not two.

Register with an MCP client (Claude Desktop, Cursor) as:

    {
      "mcpServers": {
        "billrosetta": {
          "command": "C:/Users/prest/Projects/billrosetta-moss-bridge/venv/Scripts/python.exe",
          "args": ["C:/Users/prest/Projects/billrosetta-moss-bridge/server.py"]
        }
      }
    }
"""
from typing import List

from mcp.server.fastmcp import FastMCP

from main import BillAnalysisRequest, LineItem, analyze_and_appeal

mcp = FastMCP("BillRosetta")


@mcp.tool()
async def analyze_bill(
    hospital_name: str,
    zip_code: str,
    line_items: List[dict],
) -> dict:
    """Analyze a hospital bill for overcharges and draft appeal letters.

    Compares each charged line against the Medicare reimbursement rate for its
    CPT code and returns the per-line overcharge plus ready-to-send appeal text.

    Args:
        hospital_name: Facility named on the bill, e.g. "SF General".
        zip_code: 5-digit ZIP of the facility — rates are region-specific.
        line_items: One dict per billed line, each with "cpt_code" (str) and
            "charged_amount" (float), e.g.
            [{"cpt_code": "99214", "charged_amount": 850.00}]

    Note: Medicare rates are currently served from a small static table, not a
    live lookup. Figures are representative, not authoritative — verify before
    sending an appeal.
    """
    request = BillAnalysisRequest(
        hospital_name=hospital_name,
        zip_code=zip_code,
        line_items=[LineItem(**item) for item in line_items],
    )
    return await analyze_and_appeal(request)


if __name__ == "__main__":
    mcp.run(transport="stdio")
