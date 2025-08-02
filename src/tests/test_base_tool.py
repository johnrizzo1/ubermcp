"""Tests for the BaseTool base class functionality."""

import pytest

from src.base_tool import BaseTool


class TestBaseTool:
    """Test cases for BaseTool base class."""

    def test_base_tool_initialization(self):
        """Test that BaseTool can be initialized with a name."""
        tool = BaseTool("test_tool")
        assert tool.name == "test_tool"

    def test_base_tool_execute_not_impl(self):
        """Test that BaseTool.execute() raises NotImplementedError."""
        tool = BaseTool("test_tool")
        with pytest.raises(NotImplementedError):
            tool.execute()

    def test_base_tool_name_property(self):
        """Test that name property returns the correct value."""
        tool = BaseTool("my_tool")
        assert tool.name == "my_tool"

    def test_base_tool_with_kwargs(self):
        """Test that tools can properly inherit from BaseTool with **kwargs."""

        class TestTool(BaseTool):
            def execute(self, **kwargs):
                return {"message": "test", "args": kwargs}

        tool = TestTool("test")
        result = tool.execute()
        assert result["message"] == "test"
        assert not result["args"]

        # Test with arguments
        result = tool.execute(param1="value1", param2="value2")
        assert result["args"]["param1"] == "value1"
        assert result["args"]["param2"] == "value2"

    def test_signature_consistency(self):
        """Test that tools can accept **kwargs for signature consistency."""

        class SimpleTool(BaseTool):
            def execute(self, **kwargs):
                return {"status": "ok"}

        class ParameterizedTool(BaseTool):
            def execute(self, required_param=None, **kwargs):
                return {"param": required_param, "extra": kwargs}

        simple = SimpleTool("simple")
        param = ParameterizedTool("param")

        # Both should work with no arguments
        assert simple.execute()["status"] == "ok"
        assert param.execute()["param"] is None

        # Both should work with keyword arguments
        assert simple.execute(extra="value")["status"] == "ok"
        result = param.execute(required_param="test", extra="value")
        assert result["param"] == "test"
        assert result["extra"]["extra"] == "value"

    def test_tool_name_immutability(self):
        """Test that tool name cannot be changed after initialization."""
        tool = BaseTool("original_name")
        assert tool.name == "original_name"

        # The name property should be read-only (no setter)
        with pytest.raises(AttributeError):
            tool.name = "new_name"

    def test_kwargs_param_forwarding(self):
        """Test **kwargs forwards parameters to subclass implementations."""

        class KwargsTestTool(BaseTool):
            def execute(self, **kwargs):
                return {
                    "received_keys": sorted(kwargs.keys()),
                    "param_count": len(kwargs),
                    "has_special": "special_param" in kwargs,
                }

        tool = KwargsTestTool("kwargs_test")

        # Test with no parameters
        result = tool.execute()
        assert result["param_count"] == 0
        assert result["received_keys"] == []
        assert not result["has_special"]

        # Test with multiple parameters
        result = tool.execute(
            special_param="special_value", other_param="other_value", numeric_param=42
        )
        assert result["param_count"] == 3
        assert "special_param" in result["received_keys"]
        assert result["has_special"]
