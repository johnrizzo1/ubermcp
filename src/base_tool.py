class BaseTool:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def execute(self, **kwargs):
        """Execute the tool with optional keyword arguments.

        Subclasses should override this method to provide their functionality.
        The **kwargs parameter allows for flexible parameter passing while
        maintaining signature consistency across all tools.
        """
        raise NotImplementedError
