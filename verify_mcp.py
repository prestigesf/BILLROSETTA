"""Verify server.py over a real MCP stdio session.

Spawns server.py as a subprocess, speaks MCP to it as a client would,
lists tools, calls analyze_bill, and asserts the returned payload.
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).parent

SAMPLE = {
    "hospital_name": "SF General",
    "zip_code": "94110",
    "line_items": [
        {"cpt_code": "99214", "charged_amount": 850.00},
        {"cpt_code": "80053", "charged_amount": 320.00},
    ],
}
EXPECTED = (850 - 110.50) + (320 - 45.00)


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "server.py")],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"[MCP] tools exposed: {names}")
            assert "analyze_bill" in names, names

            schema = tools.tools[0].inputSchema
            print(f"[MCP] input schema keys: {sorted(schema['properties'])}")

            result = await session.call_tool("analyze_bill", SAMPLE)
            assert not result.isError, result.content

            data = json.loads(result.content[0].text)
            print(f"[MCP] hospital          = {data['hospital']}")
            print(f"[MCP] appeals_generated = {len(data['appeals_generated'])}")
            print(f"[MCP] total_overcharge  = ${data['total_identified_overcharge']:.2f}")
            print(f"[MCP] expected          = ${EXPECTED:.2f}")

            assert len(data["appeals_generated"]) == 2
            assert abs(data["total_identified_overcharge"] - EXPECTED) < 0.01
            for row in data["appeals_generated"]:
                assert row["appeal_text"].startswith("RE: Unauthorized Upcoding")

    print("\n[MCP] ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
