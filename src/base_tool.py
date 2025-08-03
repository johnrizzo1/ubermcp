"""Base class for all tool implementations in the uber-mcp-server."""


class BaseTool:
    """Abstract base class that all MCP tools must inherit from."""

    def __init__(self, name: str):
        """Initialize the tool with a name.

        Args:
            name: The name of the tool.
        """
        self._name = name

    @property
    def name(self):
        """Get the name of the tool.

        Returns:
            The tool's name.
        """
        return self._name

    def execute(self, **kwargs):
        """Execute the tool with optional keyword arguments.

        Subclasses should override this method to provide their functionality.
        The **kwargs parameter allows for flexible parameter passing while
        maintaining signature consistency across all tools.
        """
        raise NotImplementedError
