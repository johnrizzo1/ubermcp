# Claude Desktop Remote MCP Server Setup

This guide explains how to connect Claude Desktop directly to your FastAPI MCP server.

## Overview

Your server now supports the MCP (Model Context Protocol) with Streamable HTTP transport, allowing Claude Desktop to connect directly without needing a separate bridge.

## Setup Steps

### 1. Start the FastAPI Server

```bash
cd /Users/jrizzo/Projects/ai/agents/ubermcp
nix run
```

The server will start on http://localhost:8080 with MCP endpoints at:
- `/mcp/v1/message` - Main MCP endpoint

### 2. Configure Claude Desktop for Remote Server

**On macOS:**
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add this configuration for a local server:
```json
{
  "mcpServers": {
    "uber-mcp-server": {
      "url": "http://localhost:8080/mcp/v1/message",
      "transport": "http"
    }
  }
}
```

### 3. For Remote/Cloud Deployment

If you deploy your server to a cloud provider with HTTPS:

```json
{
  "mcpServers": {
    "uber-mcp-server": {
      "url": "https://your-server.com/mcp/v1/message",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

Completely quit and restart Claude Desktop to load the new configuration.

## Testing the Integration

1. Open a new Claude conversation
2. The Kubernetes tools should be available
3. Try commands like:
   - "List the Kubernetes pods"
   - "Show me the Kubernetes services"
   - "Set up port forwarding to pod nginx in namespace default"

## Architecture

```
Claude Desktop ←→ HTTP/HTTPS ←→ FastAPI MCP Server ←→ Kubernetes Tools
```

The server implements the MCP Streamable HTTP transport, which uses standard HTTP POST requests with JSON-RPC 2.0 messages.

## API Endpoints

Your server exposes:
- `GET /` - Server info
- `GET /docs` - Interactive API documentation
- `GET /tools` - List available tools
- `POST /tools/{tool_name}` - Direct tool execution
- `POST /mcp/v1/message` - MCP protocol endpoint

## Security Considerations

1. **Local Development**: The server binds to all interfaces (0.0.0.0). For local use only, consider binding to 127.0.0.1.

2. **Production Deployment**:
   - Use HTTPS with valid certificates
   - Implement authentication (Bearer tokens, API keys)
   - Restrict CORS origins (currently set to "*")
   - Use environment-specific configuration

3. **Authentication**: Add authentication middleware:
   ```python
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   
   security = HTTPBearer()
   
   @app.post("/mcp/v1/message")
   async def handle_message(
       request: Request,
       credentials: HTTPAuthorizationCredentials = Depends(security)
   ):
       # Validate token
       if credentials.credentials != "your-secret-token":
           raise HTTPException(status_code=401)
   ```

## Troubleshooting

### Server not accessible
- Check if the server is running: `curl http://localhost:8080/`
- Check firewall settings
- Verify the URL in Claude Desktop config

### Tools not showing in Claude
- Restart Claude Desktop completely
- Check the MCP endpoint: `curl -X POST http://localhost:8080/mcp/v1/message -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'`

### Authentication errors
- Verify the Authorization header format
- Check server logs for authentication failures

## Deployment Options

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Functions
The server can be deployed to:
- AWS Lambda (with API Gateway)
- Google Cloud Run
- Azure Functions
- Vercel/Netlify Functions

Each platform may require slight modifications for serverless compatibility.

## Advanced Features

### Custom Tool Schemas
The MCP server automatically generates tool schemas. You can customize them in `mcp_server.py`:

```python
if tool.name == "your_tool":
    tool_schema["inputSchema"] = {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Parameter description"},
            "param2": {"type": "integer", "minimum": 0}
        },
        "required": ["param1"]
    }
```

### Streaming Responses
For long-running operations, consider implementing streaming responses using Server-Sent Events or WebSockets.

## Next Steps

1. Add authentication for production use
2. Deploy to a cloud provider with HTTPS
3. Implement rate limiting
4. Add monitoring and logging
5. Create custom tool schemas for better Claude integration