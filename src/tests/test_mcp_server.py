"""Tests for MCP Server implementation."""


class TestMCPServer:
    """Test cases for MCP Server endpoints."""

    def test_mcp_initialize(self, api_client):
        """Test MCP initialization."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
            "id": 1,
        }

        response = api_client.post("/mcp/v1/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert data["result"]["protocolVersion"] == "2024-11-05"
        assert data["result"]["serverInfo"]["name"] == "uber-mcp-server"

    def test_mcp_tools_list(self, api_client):
        """Test listing MCP tools."""
        request = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}

        response = api_client.post("/mcp/v1/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert "result" in data
        assert "tools" in data["result"]
        assert len(data["result"]["tools"]) > 0

        # Check that port forwarding tool is present
        tool_names = [tool["name"] for tool in data["result"]["tools"]]
        assert "kubernetesportforwarding" in tool_names

    def test_mcp_tool_call(self, api_client):
        """Test calling a tool via MCP."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "helmlist", "arguments": {}},
            "id": 3,
        }

        response = api_client.post("/mcp/v1/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 3
        assert "result" in data
        assert "content" in data["result"]
        assert len(data["result"]["content"]) > 0
        assert data["result"]["content"][0]["type"] == "text"

    def test_mcp_invalid_method(self, api_client):
        """Test invalid MCP method."""
        request = {"jsonrpc": "2.0", "method": "invalid/method", "params": {}, "id": 4}

        response = api_client.post("/mcp/v1/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 4
        assert "error" in data
        assert data["error"]["code"] == -32601
        assert "Method not found" in data["error"]["message"]

    def test_mcp_tool_not_found(self, api_client):
        """Test calling non-existent tool."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "nonexistent", "arguments": {}},
            "id": 5,
        }

        response = api_client.post("/mcp/v1/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 5
        assert "error" in data
        assert data["error"]["code"] == -32602
        assert "Tool not found" in data["error"]["message"]

    def test_mcp_parse_error(self, api_client):
        """Test invalid JSON."""
        response = api_client.post(
            "/mcp/v1/message",
            content=b"invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "error" in data
        assert data["error"]["code"] == -32700
        assert "Parse error" in data["error"]["message"]
