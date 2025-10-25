# Implementation Guide for maf-agents

## ⚠️ CRITICAL: Read This Before Implementing ANY Story

### Documentation-First Development

**ALWAYS review official Microsoft Agent Framework documentation BEFORE writing code.**

This project uses the **Microsoft Agent Framework (MAF) SDK** exclusively. MAF provides built-in patterns for:
- Workflow orchestration
- Agent/executor implementation
- Checkpoint management
- Event streaming
- Message passing

**DO NOT create custom implementations of these patterns.**

---

## Pre-Implementation Checklist

Before starting ANY story:

- [ ] Read the relevant MAF documentation section (links below)
- [ ] Review official MAF code samples for the pattern you need
- [ ] Check: "Does MAF already provide this functionality?"
- [ ] Verify you understand the MAF pattern before coding

---

## Required MAF Documentation

### Core Concepts (Read First)

1. **Executors** (the building block of workflows)
   - https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/executors
   - Executors are workflow steps defined with `@executor` decorator
   - NOT custom classes - just decorated async functions

2. **Workflows** (how to build workflow graphs)
   - https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/workflows
   - Use `WorkflowBuilder()` to construct workflows
   - NOT custom orchestration logic

3. **Sequential Orchestration** (our primary pattern)
   - https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/sequential
   - Step-by-step workflow execution
   - This is what we're building for detector development

4. **Checkpoints** (state persistence)
   - https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints
   - MAF provides `FileCheckpointStorage` and `InMemoryCheckpointStorage`
   - Automatic checkpoint creation after each superstep

5. **Using Agents in Workflows** (for LLM-powered tasks)
   - https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/using-agents
   - When to use `ChatAgent` vs `@executor` functions

### Code Samples (Essential Reference)

- Sequential Workflow Tutorial: https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/simple-sequential-workflow
- Executors Tutorial: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/executors#overview
- GitHub Samples: https://github.com/microsoft/agent-framework/tree/main/python/samples

---

## MAF Patterns You MUST Follow

### ✅ Correct Pattern: Executors

**Use `@executor` decorator for workflow steps:**

```python
from agent_framework import executor, WorkflowContext

@executor(id="schema_discovery")
async def schema_discovery_executor(
    input_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    """Queries Kusto for ETW schema."""

    # 1. Get configuration
    config = get_config()

    # 2. Call Azure services directly (no wrappers)
    kusto_client = create_kusto_client(...)
    results = kusto_client.execute_query(query)

    # 3. Send results to next executor
    await ctx.send_message({"schema": results})
```

**Key Points:**
- Functions, not classes
- Use `@executor(id="...")` decorator
- Parameter: `ctx: WorkflowContext[...]` for message passing
- Use `await ctx.send_message(data)` to pass data to next executor
- Use `await ctx.yield_output(data)` for final workflow output

### ✅ Correct Pattern: WorkflowBuilder

**Use `WorkflowBuilder` to construct workflows:**

```python
from agent_framework import WorkflowBuilder, FileCheckpointStorage

workflow = (
    WorkflowBuilder()
    .set_start_executor(etw_input_executor)
    .add_edge(etw_input_executor, schema_discovery_executor)
    .add_edge(schema_discovery_executor, code_gen_executor)
    .with_checkpointing(FileCheckpointStorage(checkpoint_dir))
    .build()
)
```

**Key Points:**
- Fluent API for building workflow graph
- Use `.add_edge(from, to)` to define flow
- Use `.with_checkpointing(storage)` for state persistence
- Call `.build()` to create executable workflow

### ✅ Correct Pattern: Azure SDK Integration

**Use Azure SDKs directly in executors (no wrapper classes):**

```python
@executor(id="schema_discovery")
async def schema_discovery_executor(
    etw_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    # Initialize Azure SDK client directly
    from azure.kusto.data import KustoClient

    auth_mgr = get_auth_manager()
    kusto_client = auth_mgr.get_kusto_client(cluster_url, database)

    # Use SDK directly
    results = kusto_client.execute(database, query)

    await ctx.send_message({"results": results})
```

**Key Points:**
- Import Azure SDKs directly
- No custom wrapper classes
- Shared utilities (like `get_auth_manager()`) are OK
- Keep it simple - use SDKs as designed

### ✅ Correct Pattern: ChatAgent (for LLM tasks)

**Only use ChatAgent when you need LLM intelligence:**

```python
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

# Create LLM-powered agent
code_gen_agent = chat_client.create_agent(
    instructions="You generate detector code based on patterns...",
    name="code_generator",
)

# Add to workflow
workflow = (
    WorkflowBuilder()
    .set_start_executor(input_executor)
    .add_edge(input_executor, code_gen_agent)  # Agent as executor
    .build()
)
```

**When to use ChatAgent:**
- Code generation (analyzing patterns, writing code)
- Natural language understanding
- Complex decision-making

**When NOT to use ChatAgent:**
- Simple data transformation
- API calls to Azure services
- Validation logic
- Any deterministic operation

---

## ❌ Anti-Patterns: DO NOT DO THESE

### ❌ DO NOT Create Custom Agent Classes

**Wrong:**
```python
# ❌ WRONG - Don't do this
class SchemaDiscoveryAgent(WorkflowAgent):
    def __init__(self, kusto_client):
        self.kusto_client = kusto_client

    async def execute(self, checkpoint):
        # Custom logic...
        pass
```

**Why Wrong:** MAF uses `@executor` functions, not custom classes.

**Correct:** Use `@executor` decorator (see above).

### ❌ DO NOT Build Custom Orchestration

**Wrong:**
```python
# ❌ WRONG - Don't do this
class WorkflowOrchestrator:
    def __init__(self):
        self.agents = [agent1, agent2, agent3]

    async def run(self):
        for agent in self.agents:
            result = await agent.execute()
            # Manual checkpoint saving...
```

**Why Wrong:** MAF provides `WorkflowBuilder` for orchestration.

**Correct:** Use `WorkflowBuilder` (see above).

### ❌ DO NOT Wrap Azure SDKs

**Wrong:**
```python
# ❌ WRONG - Don't do this
class AzureReposClientWrapper:
    def __init__(self, connection):
        self.client = connection.get_git_client()

    def create_branch(self, name):
        # Wrapper around Azure SDK...
```

**Why Wrong:** Unnecessary abstraction. Use Azure SDKs directly.

**Correct:** Use Azure SDKs directly in executors (see above).

### ❌ DO NOT Implement Custom Checkpointing

**Wrong:**
```python
# ❌ WRONG - Don't do this
class CustomCheckpointManager:
    def save(self, checkpoint):
        # Custom save logic to Azure Table Storage...
```

**Why Wrong:** MAF provides `FileCheckpointStorage`.

**Correct:** Use `FileCheckpointStorage` or `InMemoryCheckpointStorage`.

**Note:** We DO have a custom checkpoint manager for Azure Table Storage (`shared/checkpoint.py`), but this is a legacy pattern. For new code, use MAF's built-in storage.

---

## Story-Specific Guidance

### Stories 1.1-1.5: Infrastructure (COMPLETED)

✅ These are implemented following MAF patterns.

**Reference implementation:** `workflows/detector_workflow.py`

### Stories 2.1-2.4: ETW & Schema Discovery

**Key Patterns:**
- Story 2.1 (ETW Input): Use `@executor` with input validation
- Story 2.2 (Kusto Client): Thin wrapper OK, but use directly in executors
- Story 2.3 (Schema Discovery): Integrate Kusto queries in executor
- Story 2.4 (Query Templates): YAML templates are fine (not MAF-specific)

**Reference:** See `schema_discovery_executor` in `workflows/detector_workflow.py`

### Stories 3.1-3.5: Code Generation & PR Creation

**Key Patterns:**
- Story 3.2, 3.3 (Pattern Analysis, Code Gen): Use `ChatAgent` with LLM
- Story 3.1, 3.4 (Azure Repos, PR Creation): Use Azure DevOps SDK directly in executor
- Story 3.5 (Approval Gate): Use MAF request/response pattern or human-in-loop

**Important:** Code generation SHOULD use ChatAgent (LLM intelligence needed).

### Stories 4.1-4.2: Deployment & Results

**Key Patterns:**
- Story 4.1 (Deployment Verification): Azure DevOps SDK in executor
- Story 4.2 (Results Analysis): Kusto queries in executor, possibly ChatAgent for analysis

### Stories 5.1-5.5: Production Promotion

**Key Patterns:**
- Story 5.2 (Production Promotion): ChatAgent for intelligent promotion decisions
- Story 5.1 (Pattern Analysis): ChatAgent for learning patterns
- Story 5.3-5.5 (Testing, Validation, Docs): Standard Python testing, no special MAF patterns

---

## Development Workflow

### 1. Read Documentation (30-60 min)

Before coding:
1. Read relevant MAF docs (links above)
2. Review MAF code samples
3. Identify which MAF pattern applies

### 2. Implement Following MAF Patterns

Write code that:
- Uses `@executor` for workflow steps
- Uses `WorkflowBuilder` for orchestration
- Uses Azure SDKs directly
- Uses `ChatAgent` only when LLM is needed

### 3. Verify Against Documentation

Before submitting:
- Compare your code to MAF samples
- Check: "Did I reinvent any MAF functionality?"
- Verify type hints match MAF patterns

---

## Type Hints Reference

### WorkflowContext Type Parameters

```python
# For executors that send messages to next executor
WorkflowContext[TMessage]

# For executors that yield final output
WorkflowContext[Never, TOutput]

# For executors that do both
WorkflowContext[TMessage, TOutput]

# For executors that do neither (just side effects)
WorkflowContext
```

### Common Type Signatures

```python
from typing import Any
from typing_extensions import Never
from agent_framework import WorkflowContext

# Regular executor (passes data forward)
async def my_executor(
    input_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    await ctx.send_message({"result": "..."})

# Final executor (yields output)
async def final_executor(
    input_data: dict[str, Any],
    ctx: WorkflowContext[Never, dict[str, Any]]
) -> None:
    await ctx.yield_output({"final": "result"})
```

---

## Event Handling

MAF workflows emit events during execution:

```python
from agent_framework import WorkflowOutputEvent, WorkflowFailedEvent

async for event in workflow.run_stream(input_data):
    if isinstance(event, WorkflowOutputEvent):
        final_result = event.data  # Workflow completed
    elif isinstance(event, WorkflowFailedEvent):
        error_details = event.details  # Workflow failed
```

**Note:** Use `event.details`, NOT `event.error` or `event.exception`.

---

## Resources

### In This Repository

- `workflows/detector_workflow.py` - Reference MAF implementation
- `../MAF_BEST_PRACTICES.md` - Patterns vs anti-patterns (not in docs/, but worth reading)
- `../MAF_IMPLEMENTATION_SUMMARY.md` - How we implemented MAF

### External Resources

- MAF Documentation: https://learn.microsoft.com/en-us/agent-framework/
- MAF GitHub Samples: https://github.com/microsoft/agent-framework/tree/main/python/samples
- Azure SDK Documentation: https://learn.microsoft.com/en-us/azure/

---

## Summary

> **📚 Read MAF docs first. Implement MAF patterns second. Avoid custom code.**

MAF provides excellent patterns for workflow orchestration. Use them.

**Time spent reading documentation upfront saves hours of refactoring later.**

We learned this the hard way - don't repeat our mistakes.
