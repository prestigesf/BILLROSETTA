"""Smoke test: server.py imports and exposes analyze_bill as an MCP tool."""
def test_server_exposes_tool():
    import server
    assert hasattr(server, "mcp")
    assert callable(server.analyze_bill)
