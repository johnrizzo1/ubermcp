# Uber MCP Server

A FastAPI-based MCP server that provides multiple tools for Kubernetes operations.

## Features

- FastAPI HTTP server with automatic API documentation
- Multiple Kubernetes management tools
- MCP (Model Context Protocol) bridge for Claude Desktop integration
- Test-driven development with 89%+ code coverage
- Nix-based development environment

## Quick Start

```bash
# Start the FastAPI server
nix run

# Server will be available at:
# - http://localhost:8080 - API root
# - http://localhost:8080/docs - Interactive API docs
# - http://localhost:8080/tools - List available tools
```

## Claude Desktop Integration

See [CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md) for detailed instructions on integrating with Claude Desktop.

## Project Plan

- [x] Initialize the project with a `README.md` file.
- [x] Create the `devenv.nix` file.
- [x] Create the `tools` directory.
- [x] Create the `.gitignore` file.
- [x] Create the `main.py` file with the FastAPI server.
- [x] Implement the dynamic tool loading mechanism in `main.py`.
- [x] Define a `BaseTool` class that all tools will inherit from.
- [x] Create an `example_tool.py` to demonstrate the tool creation process.
- [x] Configure `devenv.nix` to include Python, `fastapi`, and `uvicorn`.
- [x] Define the `start` script in `devenv.nix` to run the MCP server.
- [x] Add a `test` script placeholder to `devenv.nix` for future use.
- [x] Document the design of the tool system in the `README.md`.
- [x] Provide detailed instructions in the `README.md` on how to set up the environment, add new tools, and run the server.
- [x] Review and finalize the project structure and code.

## Design

The Uber MCP Server is designed to be a lightweight and extensible tool server. The core of the system is the `main.py` file, which uses FastAPI to create the web server. The server dynamically loads tools from the `tools` directory.

### Tool Discovery

At startup, the server scans the `tools` directory for Python files. It ignores any files that start with an underscore (e.g., `__init__.py`). For each valid tool file, it imports the module and inspects its members.

### Tool Registration

Any class that inherits from the `BaseTool` class is considered a tool. The server creates an instance of the tool and registers it as a FastAPI endpoint. The endpoint URL is derived from the tool's class name (e.g., `ExampleTool` becomes `/tools/example`).

### BaseTool Class

The `BaseTool` class provides the basic structure for all tools. It has two main components:

- `name`: A property that automatically generates the tool's name from its class name.
- `execute`: A method that must be implemented by the subclass. This method contains the tool's logic.

### Kubernetes Tools

The following Kubernetes-related tools are available:

- `KubernetesPodsTool`: Lists Kubernetes Pods.
- `KubernetesEventsTool`: Lists Kubernetes Events.
- `KubernetesDeploymentsTool`: Lists Kubernetes Deployments.
- `KubernetesServicesTool`: Lists Kubernetes Services.
- `KubernetesIngressesTool`: Lists Kubernetes Ingresses.
- `KubernetesSecretsTool`: Lists Kubernetes Secrets.
- `KubernetesPersistentVolumesTool`: Lists Kubernetes Persistent Volumes.
- `KubernetesJobsTool`: Lists Kubernetes Jobs.
- `KubernetesCronJobsTool`: Lists Kubernetes CronJobs.
- `KubernetesRoutesTool`: Placeholder for OpenShift Routes.
- `KubernetesPortForwardingTool`: Placeholder for Port Forwarding (requires asynchronous handling).

## Instructions

### Setup

1.  Install `devenv.sh` by following the instructions on their website.
2.  Run `devenv shell` to enter the development environment. This will install all the necessary dependencies.

### Adding a New Tool

1.  Create a new Python file in the `tools` directory (e.g., `my_tool.py`).
2.  In the new file, create a class that inherits from `BaseTool`.
3.  Implement the `execute` method in your class. This method should contain the logic for your tool.

**Example:**

```python
from src.base_tool import BaseTool

class MyTool(BaseTool):
    def execute(self):
        return {"message": "This is my new tool!"}
```

### Running the Server

1.  Enter the development environment by running `devenv shell`.
2.  Run `devenv up` to start the MCP server. The server will be available at `http://localhost:8080`.

