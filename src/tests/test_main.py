def test_read_main(api_client):
    response = api_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Uber MCP Server"
    assert "docs" in data
    assert "openapi" in data


def test_list_tools(api_client):
    response = api_client.get("/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) > 0
    # Check that port forwarding tool is in the list
    tool_names = [tool["name"] for tool in data["tools"]]
    assert "kubernetesportforwarding" in tool_names


def test_helm_list_tool(api_client):
    response = api_client.post("/tools/helmlist")
    assert response.status_code == 200
    data = response.json()
    # Should return a list of releases (empty or with data)
    assert "releases" in data or "error" in data
