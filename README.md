# BillRosetta Moss Bridge

Hackathon submission — Moss + Bright Data track.
Extension of BillRosetta (PrestigeSF) that prices a hospital bill against
Medicare reimbursement rates and drafts a line-by-line appeal packet.

## What works today

Send a bill (hospital, ZIP, CPT line-items) and get back, per line:
the Medicare reimbursement rate, the overcharge in dollars, and drafted
appeal letter text — plus the total identified overcharge.

Two ways in, both verified:

- **HTTP** — `POST /api/v1/billrosetta/analyze-and-appeal` (FastAPI, `main.py`)
- **MCP** — `analyze_bill` tool over stdio (`server.py`), so an agent in
  Claude Desktop or Cursor can hand over a parsed bill and get the appeal
  packet back in one call

## What is mocked

**Medicare rates are not live.** `scrape_live_medicare_rate` returns values
from a 4-entry static table (99214=$110.50, 99215=$150.75, 99283=$250.00,
80053=$45.00) and falls back to $125.00 for anything else. No network call is
made. `requests` and `BRIGHT_DATA_API_KEY` are wired up in the class but
currently unused — the Bright Data lookup is the next piece of work, not a
finished one. Treat the dollar figures as illustrative.

## Stack

- FastAPI — HTTP surface
- mcp[cli] — Model Context Protocol server (stdio transport)
- pydantic — request/response schema
- uvicorn — ASGI runner
- requests — reserved for the Bright Data client (not yet called)

Note: `requirements.txt` pins fastapi 0.111 / pydantic 2.7.4, which have no
wheels for Python 3.14. The installed venv runs newer versions (fastapi
0.139.2, pydantic 2.13.4). Re-pin before handing this to anyone else.

## Run

    python -m venv venv
    source venv/Scripts/activate       # git-bash on Windows
    pip install -r requirements.txt "mcp[cli]"

    python main.py                     # HTTP server on :8000
    python server.py                   # MCP server on stdio

The two are independent — `server.py` calls the analysis logic in-process and
does **not** need `main.py` running.

## Verify

    python -m pytest -q                # unit + import smoke tests
    python verify_mcp.py               # full MCP client session over stdio

`verify_mcp.py` spawns `server.py` as a subprocess, speaks MCP to it the way a
real client does, lists tools, calls `analyze_bill`, and asserts the returned
overcharge math.

## Register as an MCP server

Claude Desktop / Cursor config:

    {
      "mcpServers": {
        "billrosetta": {
          "command": "C:/Users/prest/Projects/billrosetta-moss-bridge/venv/Scripts/python.exe",
          "args": ["C:/Users/prest/Projects/billrosetta-moss-bridge/server.py"]
        }
      }
    }

## Sample HTTP call

    curl -X POST http://localhost:8000/api/v1/billrosetta/analyze-and-appeal \
      -H "Content-Type: application/json" \
      -d '{
        "hospital_name": "SF General",
        "zip_code": "94110",
        "line_items": [
          {"cpt_code": "99214", "charged_amount": 850.00},
          {"cpt_code": "80053", "charged_amount": 320.00}
        ]
      }'

## Next

1. Real Bright Data lookup behind `scrape_live_medicare_rate` — needs a token
   and a decision on the rate source for CPT + ZIP.
2. Re-pin `requirements.txt` to the versions actually installed.
3. Appeal text is a single hardcoded template ("RE: Unauthorized Upcoding")
   applied to every line regardless of the discrepancy type.

## Owner

PrestigeSF · Nicholle Simon · billrosetta.com
