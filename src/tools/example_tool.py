"""Example tool for demonstration purposes."""

from src.base_tool import BaseTool


class ExampleTool(BaseTool):
    """Example tool that returns a simple greeting message."""

    def execute(self, **kwargs):
        return {"message": "Hello from the example tool!"}
