# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPORTANT: Test-Driven Development (TDD) Practices

This project follows strict TDD practices. Always follow this workflow:

1. **RED**: Write failing tests FIRST before any implementation
2. **GREEN**: Write minimal code to make tests pass
3. **REFACTOR**: Improve code quality while keeping tests green
4. **VERIFY**: Run `test` command after EVERY change (from within devenv shell)

### TDD Workflow Example
```bash
# Enter the devenv shell first
devenv shell

# 1. Write test first (it should fail)
test

# 2. Implement feature to make test pass
test

# 3. Refactor if needed
format
lint
typecheck
test

# 4. Or run all checks at once
check

# 5. Commit only when all tests pass

# For continuous testing (test watcher):
# Use ./watch_tests.sh or nix run .#test-watch
```


### Testing Requirements
- Minimum 80% code coverage is REQUIRED
- All new features must have tests written FIRST
- Run tests after each implementation step
- Never commit code with failing tests

Refer to IMPLEMENTATION_PLAN.md for the detailed project roadmap.

## Project Overview

This is a FastAPI-based MCP (Model Context Protocol) Server that provides Kubernetes management tools as HTTP API endpoints. The server uses a modular tool-based architecture where each tool inherits from `BaseTool` and is exposed as a POST endpoint.

## Key Commands

### Development Environment Setup
```bash
# Enter the development environment (installs dependencies)
nix develop

# You are now in the nix shell where you can run commands directly
```

### Running Commands

#### Using Nix apps (recommended):
```bash
nix run .#test          # Run tests with coverage
nix run .#test-watch    # Run tests in watch mode
nix run .#format        # Format code with black & isort
nix run .#lint          # Run code quality checks
nix run .#check         # Run ALL checks at once
nix run .#serve         # Start the FastAPI server
nix build               # Build the Python package
```

#### Direct commands (from within nix develop):
```bash
pytest                  # Run tests
black src/              # Format with black
isort src/              # Sort imports
pylint src/             # Run pylint
mypy src/               # Run type checking
```

### Testing
```bash
# Run all tests with coverage (80% minimum)
nix run .#test

# Run tests in watch mode
nix run .#test-watch

# Run a single test file (from within nix develop)
pytest src/tests/test_specific.py -v
```

### Code Quality
```bash
# Format code with black & isort
nix run .#format

# Run all code quality checks
nix run .#lint

# Run ALL checks including tests
nix run .#check
```

### Server Commands
```bash
# Start the FastAPI server
nix run .#serve
# or
nix run

# Build the Python package
nix build

# The server runs on http://localhost:8080
```

### Building and Packaging
```bash
# Build the package
nix build

# The built package will be in ./result/
```

## Architecture

### Tool System
- All tools inherit from `BaseTool` (defined in `src/base_tool.py`)
- Tools must implement the `execute()` method
- Tools are manually registered in `src/main.py` (not dynamically loaded despite README)
- Each tool is exposed as POST `/tools/{tool_name}`

### Project Structure
```
/src
  /tools/          # Individual tool implementations
  /tests/          # pytest test files
  base_tool.py     # Base class for all tools
  main.py          # FastAPI server and tool registration
```

### Adding New Tools
1. Create a new file in `src/tools/` (e.g., `my_new_tool.py`)
2. Define a class inheriting from `BaseTool`
3. Implement the `execute()` method
4. Import and register the tool in `src/main.py`:
   - Add import: `from src.tools import my_new_tool`
   - Add to tools list: `my_new_tool.MyNewTool("mynew")`

### Testing Guidelines
- Write tests in `src/tests/` with filename pattern `test_*.py`
- Maintain minimum 80% code coverage
- Mock external dependencies (especially Kubernetes API calls)
- Test both success and error cases

## Available Kubernetes Tools
- `KubernetesPodsTool`: Lists pods with namespace filtering
- `KubernetesEventsTool`: Lists cluster events
- `KubernetesDeploymentsTool`: Lists deployments
- `KubernetesServicesTool`: Lists services
- `KubernetesIngressesTool`: Lists ingresses
- `KubernetesSecretsTool`: Lists secrets (metadata only)
- `KubernetesPersistentVolumesTool`: Lists persistent volumes
- `KubernetesJobsTool`: Lists jobs
- `KubernetesCronJobsTool`: Lists cron jobs
- `KubernetesRoutesTool`: Placeholder for OpenShift routes
- `KubernetesPortForwardingTool`: Placeholder for port forwarding

## Dependencies
- FastAPI for web framework
- kubernetes Python client for K8s API
- pytest for testing
- httpx/requests for HTTP operations
- uvicorn as ASGI server

## Troubleshooting

### If `devenv up` doesn't start the server:
1. Check the process is defined: `devenv info | grep server`
2. The server uses a Python wrapper script (`run_server.py`) to ensure proper imports
3. Try running directly from the shell:
   ```bash
   devenv shell
   start  # This runs the server using the wrapper script
   ```
4. Or manually:
   ```bash
   devenv shell
   python run_server.py
   ```

### If commands fail in the shell:
The scripts use full paths to Python binaries to ensure the correct environment is used. If a command fails, check:
1. You're in the devenv shell
2. The Python path: `which python`
3. Import test: `python -c "import fastapi; print('FastAPI imported successfully')"`