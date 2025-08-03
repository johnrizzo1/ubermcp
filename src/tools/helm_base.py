"""Base class for Helm-related tools with common functionality."""

import subprocess

from src.base_tool import BaseTool


class HelmBaseTool(BaseTool):
    """Base class for Helm tools with common functionality"""

    def execute(self, **kwargs):
        """Execute method to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement execute method")

    def _run_helm_command(self, command, capture_output=True, input_data=None):
        """Run a helm command and return the result"""
        try:
            # Ensure helm is available
            result = subprocess.run(
                ["helm", "version", "--short"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return {"error": "Helm is not installed or not in PATH"}

            # Run the actual command
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    input=input_data,
                    check=False,
                )

                if result.returncode == 0:
                    return {
                        "status": "success",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
                return {
                    "error": f"Command failed with exit code {result.returncode}",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            # For streaming commands
            with subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            ) as process:
                stdout, stderr = process.communicate(input=input_data)

                if process.returncode == 0:
                    return {"status": "success", "stdout": stdout, "stderr": stderr}
                return {
                    "error": f"Command failed with exit code {process.returncode}",
                    "stdout": stdout,
                    "stderr": stderr,
                }

        except FileNotFoundError:
            return {"error": "Helm command not found. Please ensure Helm is installed."}
        except subprocess.TimeoutExpired as e:
            return {"error": f"Helm command timed out: {str(e)}"}
        except subprocess.SubprocessError as e:
            return {"error": f"Subprocess error running helm command: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error running helm command: {str(e)}"}

    def _parse_helm_list_output(self, output):
        """Parse helm list output into structured data"""
        lines = output.strip().split("\n")
        if not lines or len(lines) < 2:
            return []

        # Skip header
        releases = []
        for line in lines[1:]:
            parts = line.split("\t")
            if len(parts) >= 9:  # Helm 3 format
                releases.append(
                    {
                        "name": parts[0].strip(),
                        "namespace": parts[1].strip(),
                        "revision": parts[2].strip(),
                        "updated": parts[3].strip(),
                        "status": parts[4].strip(),
                        "chart": parts[5].strip(),
                        "app_version": parts[6].strip() if len(parts) > 6 else "",
                    }
                )

        return releases

    def _get_kubeconfig_args(self, kubeconfig=None, context=None):
        """Get kubeconfig related arguments"""
        args = []
        if kubeconfig:
            args.extend(["--kubeconfig", kubeconfig])
        if context:
            args.extend(["--kube-context", context])
        return args
