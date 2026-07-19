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

## Bright Data status — read this before trusting a number

The Web Unlocker integration is **written but not yet proven against the live
API**, because no token has been issued to this project yet.

What is tested (`test_brightdata.py`, 10 cases): request construction matches
Bright Data's documented Web Unlocker shape, auth header, zone and format
fields, response parsing, and fallback on timeout / junk response.

What is untested: the actual network call, and whether `parse_rate` matches
CMS's real HTML. The regex is written against an assumed page shape and
should be expected to need adjustment on first live run.

Without a token the app returns rates from a 4-entry static table
(99214=$110.50, 99215=$150.75, 99283=$250.00, 80053=$45.00, default $125.00).

**Every response says which path produced it.** Each line carries
`rate_source` (`brightdata-live` or `static-fallback:<reason>`) and the
payload carries `rates_are_live`. If that flag is false, the dollar figures
are placeholders and must not go into a real appeal.

To go live:

    export BRIGHT_DATA_API_KEY=<token>
    export BRIGHT_DATA_ZONE=<your web unlocker zone>

Then run one lookup and check `rate_source` is `brightdata-live` rather than
a fallback — that is the moment this becomes real, and it has not happened yet.

### Why scraping at all

Medicare pays a CPT at `[(work RVU x work GPCI) + (PE RVU x PE GPCI) +
(MP RVU x MP GPCI)] x CF`, where GPCIs vary by locality and CY2026's
conversion factor is $33.4009. CMS publishes this, but the lookup tool is a
JS SPA that returns nothing to plain HTTP — hence Web Unlocker. If CMS's bulk
RVU/GPCI files turn out to be easier to consume, that is the better path and
this client becomes unnecessary.

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
