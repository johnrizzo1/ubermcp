{
  description = "FastAPI-based MCP Server providing Kubernetes management tools";

  inputs = {
    nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.1";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        
        # Project metadata
        projectName = "uber-mcp-server";
        projectVersion = "0.1.0";
        
        # Python version configuration
        python = pkgs.python313;
        
        # Python dependencies for development
        pythonDeps = with python.pkgs; [
          fastapi
          uvicorn
          requests
          httpx
          kubernetes
          
          # Testing dependencies
          pytest
          pytest-cov
          pytest-asyncio
          pytest-mock
          pytest-watch
          
          # Development tools
          black
          isort
          pylint
          mypy
          ruff
          
          # Type stubs
          types-requests
          types-pyyaml
          
          # Build tools
          build
          wheel
          setuptools
          
          # SSL/TLS support
          pyopenssl
          cryptography
        ];
        
        # Development Python environment
        pythonEnv = python.withPackages (ps: pythonDeps);
        
        # Build the Python package
        ubermcp = python.pkgs.buildPythonPackage {
          pname = projectName;
          version = projectVersion;
          
          src = ./.;
          format = "pyproject";
          
          nativeBuildInputs = with python.pkgs; [
            setuptools
            wheel
            build
          ];
          
          propagatedBuildInputs = with python.pkgs; [
            fastapi
            uvicorn
            requests
            httpx
            kubernetes
          ];
          
          checkInputs = with python.pkgs; [
            pytest
            pytest-cov
            pytest-asyncio
            pytest-mock
          ];
          
          # Skip tests during build (we'll run them separately)
          doCheck = false;
          
          meta = with pkgs.lib; {
            description = "FastAPI-based MCP Server providing Kubernetes management tools";
            license = licenses.mit;
            maintainers = [ ];
          };
        };
        
      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          name = "${projectName}-dev";
          
          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.curl
            pkgs.jq
          ];
          
          shellHook = ''
            echo "╔═══════════════════════════════════════════════════════════════╗"
            echo "║          ${projectName} Development Environment              ║"
            echo "║                    Version ${projectVersion}                           ║"
            echo "╠═══════════════════════════════════════════════════════════════╣"
            echo "║ Python: ${python.version}                                                ║"
            echo "║                                                               ║"
            echo "║ Available commands:                                           ║"
            echo "║   nix run .#test         - Run tests with coverage           ║"
            echo "║   nix run .#lint         - Run code quality checks           ║"
            echo "║   nix run .#format       - Format code                       ║"
            echo "║   nix run .#serve        - Start the FastAPI server          ║"
            echo "║   nix build              - Build the package                 ║"
            echo "║                                                               ║"
            echo "║ Direct commands:                                              ║"
            echo "║   pytest                 - Run tests                         ║"
            echo "║   black src/             - Format with black                 ║"
            echo "║   pylint src/            - Run pylint                        ║"
            echo "║   mypy src/              - Run type checking                 ║"
            echo "║                                                               ║"
            echo "║ Server: http://localhost:8080                                ║"
            echo "╚═══════════════════════════════════════════════════════════════╝"
            
            export PYTHONPATH="./src:$PYTHONPATH"
          '';
        };
        
        # Build outputs
        packages = {
          default = ubermcp;
          ${projectName} = ubermcp;
        };
        
        # Applications/scripts
        apps = {
          # Test runner
          test = {
            type = "app";
            program = toString (pkgs.writeShellScript "test" ''
              export PYTHONPATH="./src:$PYTHONPATH"
              ${pythonEnv}/bin/pytest \
                --cov=src \
                --cov-report=term-missing \
                --cov-fail-under=80 \
                src/tests \
                -v \
                "$@"
            '');
          };
          
          # Test watcher
          test-watch = {
            type = "app";
            program = toString (pkgs.writeShellScript "test-watch" ''
              export PYTHONPATH="./src:$PYTHONPATH"
              ${pythonEnv}/bin/pytest-watch \
                --config /dev/null \
                -- --cov=src \
                --cov-report=term-missing \
                --cov-fail-under=80 \
                src/tests \
                -v \
                "$@"
            '');
          };
          
          # Code formatting
          format = {
            type = "app";
            program = toString (pkgs.writeShellScript "format" ''
              echo "Formatting code with black and isort..."
              ${pythonEnv}/bin/black src/
              ${pythonEnv}/bin/isort src/
              echo "Code formatting complete!"
            '');
          };
          
          # Code linting
          lint = {
            type = "app";
            program = toString (pkgs.writeShellScript "lint" ''
              echo "Running code quality checks..."
              echo "1. Checking code formatting..."
              ${pythonEnv}/bin/black src/ --check
              ${pythonEnv}/bin/isort src/ --check-only
              echo "2. Running pylint..."
              export PYTHONPATH="./src:$PYTHONPATH"
              ${pythonEnv}/bin/pylint src/ --rcfile=.pylintrc
              echo "3. Running type checking..."
              ${pythonEnv}/bin/mypy src/ --ignore-missing-imports
              echo "All quality checks passed!"
            '');
          };
          
          # Combined quality checks
          check = {
            type = "app";
            program = toString (pkgs.writeShellScript "check" ''
              echo "Running all checks..."
              export PYTHONPATH="./src:$PYTHONPATH"
              
              echo "1. Formatting..."
              ${pythonEnv}/bin/black src/ --check && ${pythonEnv}/bin/isort src/ --check-only
              
              echo "2. Linting..."
              ${pythonEnv}/bin/pylint src/ --rcfile=.pylintrc
              
              echo "3. Type checking..."
              ${pythonEnv}/bin/mypy src/ --ignore-missing-imports
              
              echo "4. Testing..."
              ${pythonEnv}/bin/pytest \
                --cov=src \
                --cov-report=term-missing \
                --cov-fail-under=80 \
                src/tests \
                -v
              
              echo "All checks passed!"
            '');
          };
          
          # Start the FastAPI server
          serve = {
            type = "app";
            program = toString (pkgs.writeShellScript "serve" ''
              export PYTHONPATH="./src:$PYTHONPATH"
              echo "Starting FastAPI server..."
              echo "Server will be available at http://localhost:8080"
              echo "Press Ctrl+C to stop"
              ${pythonEnv}/bin/uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
            '');
          };
          
          # Start the FastAPI server with HTTPS
          serve-https = {
            type = "app";
            program = toString (pkgs.writeShellScript "serve-https" ''
              export PYTHONPATH="./src:$PYTHONPATH"
              
              # Check if certificates exist
              if [ ! -f "certs/server.crt" ] || [ ! -f "certs/server.key" ]; then
                echo "SSL certificates not found. Generating self-signed certificates..."
                ./generate_certs.sh
              fi
              
              echo "Starting FastAPI server with HTTPS..."
              echo "Server will be available at https://localhost:9543"
              echo "Press Ctrl+C to stop"
              ${pythonEnv}/bin/uvicorn src.main:app --host 0.0.0.0 --port 9543 --ssl-keyfile=certs/server.key --ssl-certfile=certs/server.crt --reload
            '');
          };
          
          # MCP stdio bridge for Claude Desktop
          mcp-bridge = {
            type = "app";
            program = toString (pkgs.writeShellScript "mcp-bridge" ''
              export PYTHONPATH="./src:$PYTHONPATH"
              # Don't print anything to stdout - it interferes with JSON-RPC
              ${pythonEnv}/bin/python src/mcp_stdio_bridge.py
            '');
          };
          
          # MCP stdio bridge for Claude Desktop with HTTPS
          mcp-bridge-https = {
            type = "app";
            program = toString (pkgs.writeShellScript "mcp-bridge-https" ''
              export PYTHONPATH="./src:$PYTHONPATH"
              # Don't print anything to stdout - it interferes with JSON-RPC
              ${pythonEnv}/bin/python src/mcp_stdio_bridge_https.py
            '');
          };
          
          # Default app points to serve
          default = self.apps.${system}.serve;
        };
        
        # Development checks
        checks = {
          # Format check
          format = pkgs.runCommand "check-format" {
            buildInputs = [ pythonEnv ];
          } ''
            export PYTHONPATH="${./.}/src:$PYTHONPATH"
            cd ${./.}
            ${pythonEnv}/bin/black src/ --check
            ${pythonEnv}/bin/isort src/ --check-only
            touch $out
          '';
          
          # Lint check
          lint = pkgs.runCommand "check-lint" {
            buildInputs = [ pythonEnv ];
          } ''
            export PYTHONPATH="${./.}/src:$PYTHONPATH"
            cd ${./.}
            ${pythonEnv}/bin/pylint src/ --rcfile=.pylintrc
            touch $out
          '';
          
          # Type check
          typecheck = pkgs.runCommand "check-types" {
            buildInputs = [ pythonEnv ];
          } ''
            export PYTHONPATH="${./.}/src:$PYTHONPATH"
            cd ${./.}
            ${pythonEnv}/bin/mypy src/ --ignore-missing-imports
            touch $out
          '';
          
          # Test check
          test = pkgs.runCommand "check-tests" {
            buildInputs = [ pythonEnv ];
          } ''
            export PYTHONPATH="${./.}/src:$PYTHONPATH"
            cd ${./.}
            ${pythonEnv}/bin/pytest \
              --cov=src \
              --cov-report=term-missing \
              --cov-fail-under=80 \
              src/tests \
              -v
            touch $out
          '';
        };
      });
}
