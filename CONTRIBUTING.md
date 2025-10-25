# Contributing to maf-agents

## Development Philosophy: Documentation-First

### The Golden Rule

> **📚 Read the docs FIRST, implement SECOND.**

Before writing any code, thoroughly review the official documentation for the technology you're using:

1. **Microsoft Agent Framework**: https://learn.microsoft.com/en-us/agent-framework/
2. **Azure SDKs**: https://learn.microsoft.com/en-us/azure/
3. **Related technologies**: Check official docs for any library you're using

### Why This Matters

**Real Example from This Project:**

We initially implemented:
```python
# ❌ WRONG - Custom wrapper (not MAF pattern)
class SchemaDiscoveryAgent(WorkflowAgent):
    def __init__(self, kusto_client):
        self.kusto_client = kusto_client

    async def execute(self, checkpoint: WorkflowCheckpoint):
        # Custom execution logic
        pass
```

This seemed logical but **violated MAF patterns**. We had to rewrite it as:

```python
# ✅ CORRECT - MAF executor pattern
@executor(id="schema_discovery")
async def schema_discovery_executor(
    etw_data: dict[str, Any],
    ctx: WorkflowContext[dict[str, Any]]
) -> None:
    # Direct Azure SDK integration
    kusto_client = create_kusto_client(...)
    results = kusto_client.execute_query(query)
    await ctx.send_message(results)
```

**Time wasted**: Several hours of implementation + refactoring
**Lesson**: Read MAF executor documentation first, implement second

## Pre-Implementation Checklist

Before starting ANY story or task:

- [ ] Read relevant MAF documentation sections
- [ ] Review official code samples for the pattern
- [ ] Search MAF docs for "Does this already exist?"
- [ ] Check MAF_BEST_PRACTICES.md in this repo
- [ ] Ask: "Am I following MAF patterns or creating custom code?"

## Story Implementation Workflow

### Step 1: Documentation Review (30-60 minutes)

**For each story, review:**

1. **MAF Documentation**
   - Executors: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/executors
   - Workflows: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/workflows
   - Agents: https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/
   - Checkpoints: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints

2. **Code Samples**
   - Sequential workflow: https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/simple-sequential-workflow
   - Using agents: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/using-agents
   - Executors: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/executors

3. **Azure SDK Documentation**
   - Only for Azure service integration (Kusto, DevOps, etc.)
   - Use SDKs directly, don't wrap them

### Step 2: Pattern Identification (15 minutes)

**Ask yourself:**

1. Is this a workflow orchestration task?
   - ✅ Use `WorkflowBuilder`
   - ❌ Don't build custom orchestrator

2. Is this a workflow step/agent?
   - ✅ Use `@executor` decorator
   - ❌ Don't create custom Agent class

3. Does this need LLM intelligence?
   - ✅ Use `ChatAgent` from MAF
   - ❌ Don't integrate OpenAI directly

4. Do I need to call an Azure service?
   - ✅ Use Azure SDK directly in executor
   - ❌ Don't create wrapper classes

5. Do I need to persist state?
   - ✅ Use MAF's `FileCheckpointStorage` or `InMemoryCheckpointStorage`
   - ❌ Don't build custom checkpoint manager (unless Azure Table Storage is required)

### Step 3: Implementation (follow the docs)

**Write code that:**

- ✅ Mirrors official MAF code samples
- ✅ Uses MAF built-in classes and decorators
- ✅ Follows type hints from MAF (e.g., `WorkflowContext[TMessage, TOutput]`)
- ✅ Integrates services directly (no unnecessary abstractions)

### Step 4: Review Against Docs

Before submitting code:

- [ ] Compare your code to official MAF samples
- [ ] Check MAF_BEST_PRACTICES.md anti-patterns
- [ ] Verify you're not reimplementing MAF functionality
- [ ] Confirm you followed type signatures from docs

## Red Flags: Stop and Review Docs

🚨 **If you find yourself doing any of these, STOP and review documentation:**

1. Creating a class that extends something like `WorkflowAgent` or `BaseAgent`
   - → MAF uses `@executor` functions, not custom classes

2. Building any orchestration logic (loops, sequential calls, etc.)
   - → MAF's `WorkflowBuilder` handles orchestration

3. Creating wrapper classes for Azure SDKs
   - → Use Azure SDKs directly in executors

4. Implementing checkpoint save/load logic
   - → MAF provides `FileCheckpointStorage`

5. Creating custom event systems
   - → MAF provides `WorkflowOutputEvent`, `WorkflowFailedEvent`, etc.

6. Building message passing between agents
   - → MAF provides `ctx.send_message()` and `ctx.yield_output()`

## Code Review Guidelines

### For Reviewers

When reviewing code, check:

1. **Is this following MAF patterns?**
   - Compare to code samples in MAF docs
   - Check for custom implementations of MAF features

2. **Could this use MAF built-ins instead?**
   - Look for reinvented wheels
   - Suggest MAF alternatives

3. **Are we wrapping what doesn't need wrapping?**
   - Unnecessary abstraction layers
   - Wrapper classes around SDKs

### For Authors

Before requesting review:

1. Link to relevant MAF documentation in PR description
2. Explain which MAF pattern you're following
3. Justify any code that seems custom/non-standard

## Learning Resources

### Must-Read MAF Documentation

1. **Getting Started**: https://learn.microsoft.com/en-us/agent-framework/tutorials/overview
2. **Executors**: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/executors
3. **WorkflowBuilder**: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/workflows
4. **Sequential Orchestration**: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/sequential
5. **Working with Agents**: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/using-agents

### Project Documentation

1. **MAF_BEST_PRACTICES.md** - Correct patterns vs anti-patterns
2. **MAF_IMPLEMENTATION_SUMMARY.md** - How we implemented MAF
3. **CLEANUP_SUMMARY.md** - Mistakes we made and how we fixed them

### Code Samples Repository

Official MAF samples: https://github.com/microsoft/agent-framework/tree/main/python/samples

## Development Standards

### Code Quality

1. **Linting**: `uv run ruff check .`
2. **Formatting**: `uv run ruff format .`
3. **Type Checking**: `uv run pyright`
4. **Testing**: `uv run pytest --cov`

### Test Coverage

- Maintain 80%+ test coverage
- Write tests for all executors
- Test Azure SDK integration with mocks

### Documentation

- Update README.md for user-facing changes
- Update MAF_BEST_PRACTICES.md for new patterns learned
- Comment code that deviates from obvious MAF patterns (with justification)

## Getting Help

### Before Asking

1. Search MAF documentation
2. Review code samples in MAF repo
3. Check MAF_BEST_PRACTICES.md in this repo

### When Asking

Provide:
1. Link to MAF docs you've reviewed
2. What MAF pattern you think applies
3. Specific question about how to apply it

## Summary

> **The best code is code that follows established patterns.**

MAF provides well-designed patterns for workflow orchestration. Our job is to:
1. **Learn** those patterns thoroughly
2. **Apply** them consistently
3. **Avoid** reinventing them

**Time spent reading documentation upfront saves hours of refactoring later.**
