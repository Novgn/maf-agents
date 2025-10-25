# Story 3.2: Historical PR Pattern Analysis Implementation

**Epic**: Epic 3: Detector Code Generation & PR Management

---

## ⚠️ BEFORE IMPLEMENTING: Read Documentation First

**REQUIRED READING:**
1. **[docs/IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md)** - MAF patterns and anti-patterns
2. **[MAF ChatAgent Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/)** - This story likely needs LLM intelligence

**Key Pattern for This Story:**
- ✅ Use `ChatAgent` for intelligent pattern extraction
- ✅ Use Azure DevOps SDK directly in executor (no wrapper class)
- ❌ DO NOT create custom `PRPatternAnalyzer` class
- ❌ DO NOT implement as standalone agent - integrate as executor in workflow

See [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md#stories-31-35-code-generation--pr-creation) for specific guidance.

---

## User Story

As a **developer**,
I want **logic to analyze historical PRs and extract naming conventions and code patterns**,
so that **generated detector code follows team conventions automatically**.

## Acceptance Criteria

1. `/agents/pattern_analyzer.py` implements `PRPatternAnalyzer` class
2. Analyzer implements `fetch_recent_prs(repository, limit=20)` to retrieve recent merged PRs related to detectors
3. Analyzer implements `extract_naming_patterns(prs)` to identify file naming conventions (regex-based pattern extraction)
4. Analyzer implements `extract_code_patterns(prs)` to identify common code structures (e.g., class names, function signatures, imports)
5. Analyzer stores extracted patterns in workflow state for Code Generator agent
6. Analyzer provides confidence score for each pattern (based on frequency in PRs)
7. Analyzer handles cases where insufficient PR history exists (falls back to default templates)
8. Unit tests validate pattern extraction with mock PR data
9. Integration test validates pattern analysis with real Azure Repos PR history

## Notes

This is one of the core differentiators of the system - learning from historical patterns ensures consistency. The confidence scoring helps identify which patterns are most reliable.

## Related Documents

- PRD: docs/prd.md (Epic 3, Story 3.2)
- Architecture: docs/architecture.md
