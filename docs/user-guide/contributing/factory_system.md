---
sidebar_position: 3
# This file was auto-generated and should not be edited manually
---

# Factory System

The factory system provides a centralized, reflection-based approach to creating instances of both `Target` and `ResponseGenerator` from configuration.

## Overview

The new factory system is located in `src/mcp_kit/factory.py` and replaces the previous manual factory methods with a more generic, reflection-based approach.

## Core Components

### `create_object_from_config()`

The generic factory function that can create any object type from configuration using reflection.

**Parameters:**
- `config`: Configuration object with a 'type' field
- `get_class_name`: Function that converts type string to class name
- `get_module_name`: Function that converts type string to module name
- `object_type_name`: Name of object type for error messages

### `create_target_from_config()`

Factory function specifically for creating `Target` instances.

**Example:**
```python
from src.mcp_kit.factory import create_target_from_config

config = {
    "type": "mcp",
    "name": "example-server",
    "url": "http://localhost:8080/mcp"
}
target = create_target_from_config(config)
```

### `create_response_generator_from_config()`

Factory function specifically for creating `ResponseGenerator` instances.

**Example:**
```python
from src.mcp_kit.factory import create_response_generator_from_config

config = {
    "type": "llm",
    "model": "gpt-4"
}
generator = create_response_generator_from_config(config)
```

## Naming Conventions

### Targets
- Configuration type: `"mcp"` → Class: `McpTarget` → Module: `src.mcp_kit.targets.mcp_target`
- Configuration type: `"oas"` → Class: `OasTarget` → Module: `src.mcp_kit.targets.oas_target`
- Configuration type: `"mocked"` → Class: `MockedTarget` → Module: `src.mcp_kit.targets.mocked_target`

### Response Generators
- Configuration type: `"random"` → Class: `RandomResponseGenerator` → Module: `src.mcp_kit.generators`
- Configuration type: `"llm"` → Class: `LLMResponseGenerator` → Module: `src.mcp_kit.generators`

## Benefits

1. **Eliminates Manual Factories**: No need to manually update factory methods when adding new types
2. **Consistent Error Messages**: Standardized error handling across all object types
3. **Type Safety**: Proper type hints and runtime checking
4. **Extensibility**: Easy to add new object types without modifying existing factory code
5. **Reduced Circular Imports**: Centralized factory prevents circular import issues

## Migration

The refactoring maintains backward compatibility:
- All existing `from_config()` methods continue to work
- Import paths have been updated from `src.mcp_kit.targets.factory` to `src.mcp_kit.factory`
- Error messages have been standardized but tests have been updated accordingly

## Adding New Types

To add a new target type:
1. Create the class following the naming convention (e.g., `NewTarget`)
2. Implement the `from_config()` class method
3. Place it in the appropriate module (e.g., `src.mcp_kit.targets.new_target`)
4. The factory will automatically discover and instantiate it

To add a new generator type:
1. Create the class following the naming convention (e.g., `NewResponseGenerator`)
2. Implement the `from_config()` class method
3. Place it in `src.mcp_kit.generators`
4. The factory will automatically discover and instantiate it
