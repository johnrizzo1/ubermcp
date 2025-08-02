# Claude Desktop Integration Setup

This guide explains how to integrate the Uber MCP Server with Claude Desktop.

## Two Integration Options

### Option 1: Direct HTTP Connection (Recommended)
Connect Claude Desktop directly to your FastAPI server via HTTP/HTTPS.
See [CLAUDE_DESKTOP_REMOTE_SETUP.md](CLAUDE_DESKTOP_REMOTE_SETUP.md) for details.

### Option 2: Local stdio Bridge
Use a local bridge for stdio-based MCP communication (legacy approach).

## Prerequisites

1. Claude Desktop app installed
2. The FastAPI server must be running

## Setup Steps

### 1. Start the FastAPI Server

First, start the FastAPI server in a terminal:

```bash
cd /Users/jrizzo/Projects/ai/agents/ubermcp
nix run
# or
nix run .#serve
```

The server should start on http://localhost:8080

### 2. Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**On macOS:**
```bash
# Open Claude Desktop config
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Add this configuration:**
```json
{
  "mcpServers": {
    "uber-mcp-server": {
      "command": "/Users/jrizzo/Projects/ai/agents/ubermcp/run_mcp_bridge.sh"
    }
  }
}
```

If you already have other MCP servers configured, add it to the existing `mcpServers` object:
```json
{
  "mcpServers": {
    "existing-server": {
      "command": "..."
    },
    "uber-mcp-server": {
      "command": "/Users/jrizzo/Projects/ai/agents/ubermcp/run_mcp_bridge.sh"
    }
  }
}
```

### 3. Restart Claude Desktop

After updating the configuration, completely quit and restart Claude Desktop.

### 4. Verify Integration

In a new Claude conversation, you should see the Kubernetes tools available. Try asking:
- "What MCP tools are available?"
- "Can you list the Kubernetes pods?" (note: this requires kubectl/kubeconfig to be set up)

## Alternative Setup Methods

### Using nix run directly:

Instead of the shell script, you can configure Claude Desktop to use nix directly:

```json
{
  "mcpServers": {
    "uber-mcp-server": {
      "command": "nix",
      "args": ["run", "/Users/jrizzo/Projects/ai/agents/ubermcp#mcp-bridge"]
    }
  }
}
```

### Using absolute Python path:

If you prefer not to use the wrapper script:

```json
{
  "mcpServers": {
    "uber-mcp-server": {
      "command": "/usr/bin/env",
      "args": [
        "bash", 
        "-c", 
        "cd /Users/jrizzo/Projects/ai/agents/ubermcp && nix develop --command python src/mcp_stdio_bridge.py"
      ]
    }
  }
}
```

## Troubleshooting

### 1. Check if FastAPI server is running
```bash
curl http://localhost:8080/
```

### 2. Test the MCP bridge manually
```bash
cd /Users/jrizzo/Projects/ai/agents/ubermcp
./run_mcp_bridge.sh
# Type: {"jsonrpc": "2.0", "method": "initialize", "id": 1}
# You should see a response
```

### 3. Check logs
The MCP bridge logs to `/tmp/mcp_bridge.log`:
```bash
tail -f /tmp/mcp_bridge.log
```

### 4. Common Issues

- **"FastAPI server not running"**: Make sure to start the server with `nix run` first
- **"command not found"**: Make sure the path in claude_desktop_config.json is absolute
- **Tools not showing in Claude**: Restart Claude Desktop completely (Cmd+Q on macOS)

## Architecture

The integration works as follows:

1. Claude Desktop → MCP Bridge (stdio) → FastAPI Server (HTTP) → Kubernetes Tools
2. The MCP bridge translates between Claude's stdio protocol and our HTTP API
3. Both the FastAPI server and MCP bridge must be running

## Available Tools

Once integrated, you'll have access to these Kubernetes tools:
- kubernetespods - List pods
- kubernetesdeployments - List deployments  
- kubernetesservices - List services
- kubernetesingresses - List ingresses
- kubernetessecrets - List secrets
- kubernetespersistentvolumes - List PVs
- kubernetesjobs - List jobs
- kubernetescronjobs - List cron jobs
- kubernetesevents - List events
- kubernetesportforwarding - Manage port forwards (metadata only)

Each tool can be called with optional parameters like `namespace` for filtering.