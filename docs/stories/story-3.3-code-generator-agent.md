# Story 3.3: Detector Code Generator Agent Implementation

**Epic**: Epic 3: Detector Code Generation & PR Management

---

## ⚠️ BEFORE IMPLEMENTING: Read Documentation First

**REQUIRED READING:**
1. **[docs/IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md)** - MAF patterns and anti-patterns
2. **[MAF ChatAgent Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/)** - Essential for this story
3. **[Using Agents in Workflows](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/using-agents)** - How to integrate LLMs

**⚠️ IMPORTANT - Use ChatAgent for Code Generation:**

The acceptance criteria below mention creating a `code_generator_agent.py` file with a custom class. **This should be reconsidered** according to MAF best practices.

**Correct Approach:**
- ✅ Use `ChatAgent` with LLM for intelligent code generation
- ✅ Integrate ChatAgent directly into workflow via `WorkflowBuilder`
- ✅ Provide pattern data and schema in agent instructions or context
- ❌ DO NOT create custom `CodeGeneratorAgent` class
- ❌ DO NOT implement as standalone sub-workflow

**Why:** Code generation requires LLM intelligence to analyze patterns and generate code. MAF's `ChatAgent` is designed for this.

**Example Pattern:**
```python
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

code_gen_agent = chat_client.create_agent(
    instructions="You are an expert at generating Python detector code...",
    name="code_generator",
)

# Add directly to workflow
workflow = (
    WorkflowBuilder()
    .add_edge(pattern_analysis_executor, code_gen_agent)
    .add_edge(code_gen_agent, pr_creation_executor)
    .build()
)
```

See [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md#-correct-pattern-chatagent-for-llm-tasks) for complete guidance.

---

## User Story

As a **detector engineer**,
I want **an agent that generates detector code files following learned patterns and conventions**,
so that **my detector code is consistent with team standards without manual effort**.

## Acceptance Criteria

1. `/agents/code_generator_agent.py` implements the Code Generator agent as Microsoft Agent Framework sub-workflow
2. Agent retrieves ETW inputs (providerGuid, ruleId) and schema definition from workflow state
3. Agent invokes `PRPatternAnalyzer` to extract naming and code patterns from historical PRs
4. Agent generates detector file name following naming patterns
5. Agent generates detector code (Python class) following code patterns, incorporating ETW schema fields
6. Agent includes necessary imports, class definition, initialization, and ETW event handling logic
7. Agent generates test file (basic unit test skeleton) following test patterns
8. Agent validates generated code syntax (Python AST parsing)
9. Agent stores generated files in workflow state for commit
10. Agent presents generated code preview to user conversationally
11. Unit tests validate code generation with mock patterns and ETW schema
12. Integration test validates complete code generation with real pattern analysis

## Notes

This is the core automation value of the entire system - automatically generating consistent, pattern-based detector code. The code preview gives users confidence before committing.

## Related Documents

- PRD: docs/prd.md (Epic 3, Story 3.3)
- Architecture: docs/architecture.md
