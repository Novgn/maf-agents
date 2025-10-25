# Story 3.1: Azure Repos Client Wrapper Implementation

**Epic**: Epic 3: Detector Code Generation & PR Management

---

## ⚠️ BEFORE IMPLEMENTING: Read Documentation First

**REQUIRED READING:**
1. **[docs/IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md)** - MAF patterns and anti-patterns
2. **[MAF Executors Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/executors)**

**⚠️ IMPORTANT - This Story Needs Reinterpretation:**

The acceptance criteria below ask for an `AzureReposClientWrapper` class. **This is an anti-pattern** according to MAF best practices.

**Correct Approach:**
- ❌ DO NOT create `AzureReposClientWrapper` class
- ✅ Use Azure DevOps SDK directly in executors (`pr_creation_executor`, etc.)
- ✅ Create simple utility functions if needed (e.g., `create_branch_helper()`)
- ✅ Keep Azure SDK calls inline in executors

**Why:** Wrapper classes add unnecessary abstraction. Azure DevOps SDK is well-designed - use it directly.

See [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md#-correct-pattern-azure-sdk-integration) for examples.

---

## User Story

As a **developer**,
I want **a reusable Azure Repos client wrapper for repository operations**,
so that **agents can create branches, commit code, and manage PRs consistently**.

## Acceptance Criteria

1. `/shared/repos_client.py` implements `AzureReposClientWrapper` class
2. Wrapper initializes Azure DevOps client with organization, project, and repository from config
3. Wrapper implements `create_branch(branch_name, source_branch)` method
4. Wrapper implements `commit_files(branch_name, file_changes, commit_message)` method where file_changes is dict of {file_path: content}
5. Wrapper implements `create_pull_request(source_branch, target_branch, title, description)` method
6. Wrapper implements `get_pull_request_status(pr_id)` method to check merge status
7. Wrapper handles Azure DevOps API errors and implements retry logic for transient failures
8. Wrapper logs all operations for debugging
9. Unit tests validate operation logic with mocks
10. Integration test validates branch creation, commit, and PR creation against real Azure Repos (test repository)

## Notes

This wrapper abstracts all Azure Repos operations, making it easy for agents to interact with version control without dealing with Azure DevOps API complexity.

## Related Documents

- PRD: docs/prd.md (Epic 3, Story 3.1)
- Architecture: docs/architecture.md
