# Microsoft Agent Framework Best Practices

## Summary

This document outlines the correct patterns for implementing workflows with the Microsoft Agent Framework (MAF) SDK, based on official documentation and our implementation learnings.

## ✅ DO: Follow MAF Patterns

### 1. Use `@executor` Decorator for Workflow Steps

**Correct Approach:**
```python
from agent_framework import executor, WorkflowContext

@executor(id="etw_input_collection")
async def etw_input_collection_executor(
    input_data: dict[str, Any] | None,
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """Collects and validates ETW input."""
    # Validate input
    provider_guid = input_data.get("provider_guid")

    # Process data
    result = {"provider_guid": provider_guid, "validated": True}

    # Send to next executor
    await ctx.send_message(result)
```

**Why:** Executors are the fundamental building blocks in MAF. The `@executor` decorator:
- Registers the function as a workflow node
- Provides automatic type handling
- Enables workflow graph construction
- Supports MAF's superstep execution model

### 2. Integrate Azure Services Directly in Executors

**Correct Approach:**
```python
@executor(id="schema_discovery")
async def schema_discovery_executor(
    etw_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """Queries Kusto for ETW schema."""
    # Get configuration
    config = get_config()

    # Initialize Azure SDK client directly
    auth_mgr = get_auth_manager(use_default_credential=True)
    kusto_client = create_kusto_client(
        cluster_url=config.azure.kusto_cluster_url,
        database=config.azure.kusto_database_name,
        auth_manager=auth_mgr,
    )

    # Execute Azure service call
    query = kusto_client.load_query_template("get_etw_schema", params)
    results = kusto_client.execute_query(query)

    # Pass results to next executor
    etw_data["schema_fields"] = results
    await ctx.send_message(etw_data)
```

**Why:** MAF executors can directly integrate with any service. No wrapper "agent" classes needed.

### 3. Use `WorkflowBuilder` for Workflow Construction

**Correct Approach:**
```python
from agent_framework import WorkflowBuilder, FileCheckpointStorage

# Build workflow with fluent API
workflow = (
    WorkflowBuilder()
    .set_start_executor(etw_input_collection_executor)
    .add_edge(etw_input_collection_executor, schema_discovery_executor)
    .add_edge(schema_discovery_executor, code_generator_executor)
    .with_checkpointing(FileCheckpointStorage(checkpoint_dir))
    .build()
)
```

**Why:** `WorkflowBuilder`:
- Provides fluent, readable API
- Validates workflow graph structure
- Enables checkpointing integration
- Supports type-safe edge definitions

### 4. Use MAF's Built-in Checkpoint System

**Correct Approach:**
```python
from agent_framework import FileCheckpointStorage
from pathlib import Path

checkpoint_dir = Path("./checkpoints")
checkpoint_dir.mkdir(exist_ok=True)
checkpoint_storage = FileCheckpointStorage(checkpoint_dir)

workflow = (
    WorkflowBuilder()
    # ... add executors ...
    .with_checkpointing(checkpoint_storage)
    .build()
)
```

**Why:** MAF's checkpoint system:
- Automatically saves state after each superstep
- Supports workflow resumption
- Handles serialization/deserialization
- Provides both file-based and in-memory options

### 5. Use AI Agents for Intelligent Tasks

**Correct Approach (when LLM intelligence is needed):**
```python
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity import AzureCliCredential

# Create AI agent
chat_client = AzureAIAgentClient(credential=AzureCliCredential())
code_gen_agent = chat_client.create_agent(
    instructions="You are an expert at generating detector code...",
    name="code_generator",
)

# Add agent directly to workflow
workflow = (
    WorkflowBuilder()
    .set_start_executor(input_executor)
    .add_edge(input_executor, code_gen_agent)  # Agent as executor
    .add_edge(code_gen_agent, pr_executor)
    .build()
)
```

**Why:** For LLM-powered tasks:
- ChatAgent integrates seamlessly into workflows
- MAF automatically wraps agents as executors
- No custom wrapper code needed
- Supports streaming, function calling, tools

## ❌ DON'T: Anti-Patterns to Avoid

### 1. ❌ Don't Create Custom "Agent" Wrapper Classes

**Wrong Approach:**
```python
# ❌ DON'T DO THIS
class SchemaDiscoveryAgent(WorkflowAgent):
    def __init__(self, kusto_client):
        self.kusto_client = kusto_client

    async def execute(self, checkpoint: WorkflowCheckpoint):
        # Custom execution logic
        pass
```

**Why Wrong:**
- Not the MAF pattern
- Adds unnecessary abstraction
- Breaks MAF's type system
- Can't leverage MAF features (checkpointing, events, etc.)

**Correct Alternative:**
Use `@executor` decorated functions directly.

### 2. ❌ Don't Build Custom Orchestration Logic

**Wrong Approach:**
```python
# ❌ DON'T DO THIS
class WorkflowOrchestrator:
    def __init__(self):
        self.agents = [agent1, agent2, agent3]

    async def execute_workflow(self):
        for agent in self.agents:
            result = await agent.execute()
            # Manual checkpoint saving
            checkpoint_manager.save(result)
```

**Why Wrong:**
- Reimplements MAF functionality
- No graph-based workflow
- Manual checkpoint management
- Doesn't support MAF events, resumption, etc.

**Correct Alternative:**
Use `WorkflowBuilder` with edges.

### 3. ❌ Don't Create Wrapper Classes for Azure SDKs

**Wrong Approach:**
```python
# ❌ DON'T DO THIS
class AzureReposClientWrapper:
    def __init__(self, connection):
        self.git_client = connection.clients.get_git_client()

    def create_branch(self, branch_name):
        # Wrapper around Azure DevOps SDK
        pass
```

**Why Wrong:**
- Unnecessary abstraction
- Doesn't integrate with MAF
- Adds maintenance burden
- Azure SDKs already provide excellent APIs

**Correct Alternative:**
Use Azure SDKs directly within executors. Create utility functions if needed, but not "agent" classes.

## MAF Architecture Summary

```
Workflow (Graph of Executors)
  ├── Executor 1 (simple @executor function)
  ├── Executor 2 (simple @executor function)
  ├── Executor 3 (ChatAgent - for LLM tasks)
  └── Executor 4 (simple @executor function)
```

**Key Principles:**
1. **Executors are the unit of work** - Use `@executor` decorator
2. **Workflows are graphs** - Use `WorkflowBuilder` to connect executors
3. **Agents are optional** - Only use ChatAgent when you need LLM intelligence
4. **Azure SDKs go inside executors** - No custom wrapper classes

## Implementation Checklist

- [x] Install MAF SDK: `uv sync --prerelease=allow` with `agent-framework>=0.1.0a0`
- [x] Use `@executor` decorator for all workflow steps
- [x] Use `WorkflowBuilder()` to construct workflows
- [x] Use `FileCheckpointStorage` for persistence
- [x] Integrate Azure SDKs directly in executors
- [x] Use `ChatAgent` only for LLM-powered tasks
- [x] Use `ctx.send_message()` for data passing
- [x] Use `ctx.yield_output()` for final results
- [x] Use `workflow.run_stream()` for event-based execution

## References

- [MAF Executors Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/executors)
- [MAF Sequential Orchestration](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/sequential)
- [MAF Checkpoints](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints)
- [MAF Working with Agents](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/using-agents)
