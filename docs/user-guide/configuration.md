---
sidebar_position: 3
# This file was auto-generated and should not be edited manually
---

# Configuration

MCP Kit uses YAML or JSON configuration files to define proxy behavior, targets, and routing rules.

## Basic Configuration

### Minimal Configuration

```yaml
# proxy_config.yaml
target:
  type: mcp
  name: my-mcp-server
  url: http://localhost:8080/mcp
  headers:
    Authorization: Bearer your-token-here
    Content-Type: application/json
```

### Advanced Configuration

```yaml
# Example configuration for a multiplex target combining multiple servers
target:
  type: multiplex
  name: combined-servers
  targets:
    - type: mcp
      name: mcp-server-1
      url: http://localhost:8080/mcp
    - type: oas
      name: petstore-api
      spec_url: https://petstore3.swagger.io/api/v3/openapi.json
    - type: mocked
      response_generator:
        type: llm
        model: openai/gpt-4.1-nano
      base_target:
        type: mcp
        name: test-server
        tools:
          - name: get_user_info
            description: Retrieve user information by user ID
            inputSchema:
              type: object
              properties:
                user_id:
                  type: string
                  description: The unique identifier for the user
                include_details:
                  type: boolean
                  description: Whether to include detailed information
                  default: false
              required:
                - user_id
            annotations:
              title: User Information Retrieval
              readOnlyHint: true
              destructiveHint: false
              idempotentHint: true
              openWorldHint: false
          - name: send_notification
            description: Send a notification to a user
            inputSchema:
              type: object
              properties:
                user_id:
                  type: string
                  description: The unique identifier for the user
                message:
                  type: string
                  description: The notification message to send
                priority:
                  type: string
                  enum: ["low", "medium", "high"]
                  description: The priority level of the notification
                  default: medium
              required:
                - user_id
                - message
            annotations:
              title: User Notification Sender
              readOnlyHint: false
              destructiveHint: false
              idempotentHint: false
              openWorldHint: true

```

## Configuration Sections

### Targets

Define where requests should be routed:

#### MCP Target
```yaml
target:
  type: mcp
  name: my-mcp-server
  url: http://localhost:8080/mcp
  headers:
    Authorization: Bearer your-token-here
    Content-Type: application/json
```

#### OpenAPI Spec Target
```yaml
target:
  type: oas
  name: petstore-api
  spec_url: https://petstore3.swagger.io/api/v3/openapi.json
```

#### Mocked Target
```yaml
target:
  type: mocked
  base_target:
    type: oas
    name: base-oas-server
    spec_url: https://petstore3.swagger.io/api/v3/openapi.json
  response_generator:
    type: llm
    model: openai/gpt-4.1-nano

```

#### Multiplex Target
```yaml
target:
  type: multiplex
  name: combined-servers
  targets:
    - type: mcp
      name: mcp-server-1
      url: http://localhost:8080/mcp
    - type: oas
      name: petstore-api
      spec_url: https://petstore3.swagger.io/api/v3/openapi.json
```


### Generators

Configure response generation:

```yaml
response_generator:
  type: llm
  model: anthropic/claude-3-5-haiku-20241022
```

```yaml
response_generator:
  type: random
```

Set variables:
```bash
# .env
ANTHROPIC_API_KEY="your_api_key"
```

## Examples

See the [Examples section](../examples) for real-world configuration examples.

## Next Steps

- [Adapters Guide](./adapters.md) - Framework integrations
- [Examples](../examples) - Real-world usage examples
