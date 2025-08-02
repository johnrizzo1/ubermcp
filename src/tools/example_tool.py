from src.base_tool import BaseTool


class ExampleTool(BaseTool):
    def execute(self, **kwargs):
        return {"message": "Hello from the example tool!"}
