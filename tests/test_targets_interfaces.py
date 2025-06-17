"""Tests for target interfaces."""

import pytest
from mcp import Tool
from mcp.types import Content, TextContent
from omegaconf import DictConfig, OmegaConf

from mcp_kit.targets.interfaces import Target


class TestTargetInterface:
    """Test cases for Target interface."""

    def test_target_is_abstract(self):
        """Test that Target cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Target()

    def test_target_inheritance_requirements(self):
        """Test that concrete Target implementations must implement all abstract methods."""

        # Incomplete implementation should fail
        class IncompleteTarget(Target):
            def __init__(self):
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteTarget()

    def test_concrete_target_implementation(self):
        """Test a complete Target implementation."""

        class ConcreteTarget(Target):
            def __init__(self, name: str):
                self._name = name

            @property
            def name(self) -> str:
                return self._name

            async def initialize(self) -> None:
                pass

            async def list_tools(self) -> list[Tool]:
                return []

            async def call_tool(
                self, name: str, arguments: dict | None = None
            ) -> list[Content]:
                return [TextContent(type="text", text="test")]

            async def close(self) -> None:
                pass

            @classmethod
            def from_config(cls, config: DictConfig):
                return cls("test")

        # Should be able to create instance
        target = ConcreteTarget("test-target")
        assert isinstance(target, Target)
        assert target.name == "test-target"

    @pytest.mark.asyncio
    async def test_target_interface_methods(self):
        """Test that all interface methods work correctly."""

        class TestTarget(Target):
            def __init__(self, name: str):
                self._name = name
                self.initialized = False
                self.closed = False

            @property
            def name(self) -> str:
                return self._name

            async def initialize(self) -> None:
                self.initialized = True

            async def list_tools(self) -> list[Tool]:
                return [Tool(name="test_tool", description="Test tool", inputSchema={})]

            async def call_tool(
                self, name: str, arguments: dict | None = None
            ) -> list[Content]:
                return [
                    TextContent(type="text", text=f"Called {name} with {arguments}")
                ]

            async def close(self) -> None:
                self.closed = True

            @classmethod
            def from_config(cls, config: DictConfig):
                return cls(config.name)

        target = TestTarget("interface-test")

        # Test name property
        assert target.name == "interface-test"

        # Test initialize
        await target.initialize()
        assert target.initialized is True

        # Test list_tools
        tools = await target.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "test_tool"

        # Test call_tool
        result = await target.call_tool("test_tool", {"param": "value"})
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "test_tool" in result[0].text

        # Test call_tool with None arguments
        result = await target.call_tool("test_tool", None)
        assert len(result) == 1
        assert "None" in result[0].text

        # Test close
        await target.close()
        assert target.closed is True

    def test_from_config_interface(self):
        """Test from_config class method interface."""

        class ConfigurableTarget(Target):
            def __init__(self, name: str, url: str | None = None):
                self._name = name
                self.url = url

            @property
            def name(self) -> str:
                return self._name

            async def initialize(self) -> None:
                pass

            async def list_tools(self) -> list[Tool]:
                return []

            async def call_tool(
                self, name: str, arguments: dict | None = None
            ) -> list[Content]:
                return []

            async def close(self) -> None:
                pass

            @classmethod
            def from_config(cls, config: DictConfig):
                name = config.name
                url = config.get("url", None)
                return cls(name, url)

        # Test with minimal config
        config = OmegaConf.create({"name": "config-target"})
        target = ConfigurableTarget.from_config(config)
        assert target.name == "config-target"
        assert target.url is None

        # Test with full config
        config = OmegaConf.create(
            {"name": "full-config-target", "url": "http://example.com"}
        )
        target = ConfigurableTarget.from_config(config)
        assert target.name == "full-config-target"
        assert target.url == "http://example.com"

    def test_target_with_configurable_mixin_inheritance(self):
        """Test Target works correctly with ConfigurableMixin inheritance."""
        from mcp_kit.mixins import ConfigurableMixin

        # Target already inherits from ConfigurableMixin, so this should work seamlessly
        class MixedTarget(Target):
            def __init__(self, name: str):
                self._name = name

            @property
            def name(self) -> str:
                return self._name

            async def initialize(self) -> None:
                pass

            async def list_tools(self) -> list[Tool]:
                return []

            async def call_tool(
                self, name: str, arguments: dict | None = None
            ) -> list[Content]:
                return []

            async def close(self) -> None:
                pass

            @classmethod
            def from_config(cls, config: DictConfig):
                return cls(config.name)

        target = MixedTarget("mixed-target")
        assert isinstance(target, Target)
        assert isinstance(target, ConfigurableMixin)
        assert target.name == "mixed-target"

    @pytest.mark.asyncio
    async def test_target_lifecycle_pattern(self):
        """Test common target lifecycle pattern."""

        class LifecycleTarget(Target):
            def __init__(self, name: str):
                self._name = name
                self.state = "created"

            @property
            def name(self) -> str:
                return self._name

            async def initialize(self) -> None:
                if self.state != "created":
                    raise RuntimeError("Already initialized")
                self.state = "initialized"

            async def list_tools(self) -> list[Tool]:
                if self.state != "initialized":
                    raise RuntimeError("Not initialized")
                return [
                    Tool(
                        name="lifecycle_tool",
                        description="Lifecycle tool",
                        inputSchema={},
                    )
                ]

            async def call_tool(
                self, name: str, arguments: dict | None = None
            ) -> list[Content]:
                if self.state != "initialized":
                    raise RuntimeError("Not initialized")
                return [TextContent(type="text", text="Lifecycle response")]

            async def close(self) -> None:
                self.state = "closed"

            @classmethod
            def from_config(cls, config: DictConfig):
                return cls(config.name)

        target = LifecycleTarget("lifecycle-test")

        # Should start in created state
        assert target.state == "created"

        # Operations should fail before initialization
        with pytest.raises(RuntimeError, match="Not initialized"):
            await target.list_tools()

        with pytest.raises(RuntimeError, match="Not initialized"):
            await target.call_tool("test", {})

        # Initialize
        await target.initialize()
        assert target.state == "initialized"

        # Operations should work after initialization
        tools = await target.list_tools()
        assert len(tools) == 1

        result = await target.call_tool("lifecycle_tool", {})
        assert len(result) == 1

        # Close
        await target.close()
        assert target.state == "closed"

        # Double initialization should fail
        with pytest.raises(RuntimeError, match="Already initialized"):
            await target.initialize()

    def test_target_method_signatures(self):
        """Test that Target method signatures are correctly defined."""
        import inspect

        # Check that abstract methods have the expected signatures
        initialize_sig = inspect.signature(Target.initialize)
        assert len(initialize_sig.parameters) == 1  # self

        list_tools_sig = inspect.signature(Target.list_tools)
        assert len(list_tools_sig.parameters) == 1  # self

        call_tool_sig = inspect.signature(Target.call_tool)
        assert len(call_tool_sig.parameters) == 3  # self, name, arguments

        close_sig = inspect.signature(Target.close)
        assert len(close_sig.parameters) == 1  # self

        from_config_sig = inspect.signature(Target.from_config)
        assert (
            len(from_config_sig.parameters) == 1
        )  # config (cls is implicit in classmethod)

    @pytest.mark.asyncio
    async def test_target_error_handling_patterns(self):
        """Test common error handling patterns in targets."""

        class ErrorTarget(Target):
            def __init__(self, name: str):
                self._name = name

            @property
            def name(self) -> str:
                return self._name

            async def initialize(self) -> None:
                # Simulate initialization error
                raise ConnectionError("Failed to connect")

            async def list_tools(self) -> list[Tool]:
                raise RuntimeError("Service unavailable")

            async def call_tool(
                self, name: str, arguments: dict | None = None
            ) -> list[Content]:
                if name == "error_tool":
                    raise ValueError("Invalid tool parameter")
                return [TextContent(type="text", text="Success")]

            async def close(self) -> None:
                # Close should typically not raise errors
                pass

            @classmethod
            def from_config(cls, config: DictConfig):
                return cls(config.name)

        target = ErrorTarget("error-test")

        # Test initialization error
        with pytest.raises(ConnectionError, match="Failed to connect"):
            await target.initialize()

        # Test list_tools error
        with pytest.raises(RuntimeError, match="Service unavailable"):
            await target.list_tools()

        # Test call_tool error
        with pytest.raises(ValueError, match="Invalid tool parameter"):
            await target.call_tool("error_tool", {})

        # Test successful call_tool
        result = await target.call_tool("good_tool", {})
        assert len(result) == 1

        # Close should not raise
        await target.close()
