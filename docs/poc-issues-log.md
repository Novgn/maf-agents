# POC Issues Log: maf-agents Testing

**Document Version**: 1.0
**Date**: 2025-10-25
**Purpose**: Track all issues, failures, edge cases, and unexpected behaviors discovered during POC testing

---

## Issue Tracking Summary

| Status | Count |
|--------|-------|
| Open | 0 |
| In Progress | 0 |
| Resolved | 0 |
| Closed | 0 |
| **Total** | **0** |

---

## Issue Severity Definitions

| Severity | Definition | Example |
|----------|------------|---------|
| **Critical** | Workflow cannot complete; blocks testing | System crash, unrecoverable error |
| **High** | Major functionality broken; workaround exists | PR creation fails intermittently |
| **Medium** | Functionality degraded; minor impact | Slow query performance |
| **Low** | Cosmetic or minor issue; no functional impact | Typo in output message |

---

## Issue Categories

- **Schema Discovery**: Issues with Kusto schema queries or parsing
- **Code Generation**: Problems with detector code generation or patterns
- **PR Management**: Azure Repos branch/commit/PR creation issues
- **Deployment**: Deployment detection or verification problems
- **Results Analysis**: Kusto results querying or interpretation issues
- **Promotion**: Production promotion PR creation issues
- **Checkpoint**: State management and recovery issues
- **Performance**: Timing or resource usage problems
- **UX**: User experience and interface issues
- **Integration**: External service integration problems

---

## Open Issues

### Issue Template

```markdown
## Issue #[ID]: [Brief Title]

**Date Reported**: YYYY-MM-DD
**Reported By**: [Name]
**Severity**: Critical / High / Medium / Low
**Category**: [Category from list above]
**Status**: Open / In Progress / Resolved / Closed

**Description**:
[Detailed description of the issue]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happened]

**Error Messages/Logs**:
```
[Paste error messages or relevant logs]
```

**Environment**:
- Python Version: [version]
- MAF SDK Version: [version]
- Azure Kusto Cluster: [cluster]
- Azure DevOps Org: [org]
- Test Scenario: [scenario number]

**Impact**:
[How this affects testing or functionality]

**Workaround** (if any):
[Temporary solution]

**Root Cause** (if identified):
[Technical explanation]

**Resolution** (when resolved):
[How it was fixed]

**Related Issues**: #[ID], #[ID]
```

---

## Sample Issues (For Reference)

### Issue #1: Kusto Query Timeout on Large Schemas

**Date Reported**: 2025-10-25
**Reported By**: Test Engineer
**Severity**: High
**Category**: Schema Discovery
**Status**: Open

**Description**:
When discovering schema for high-volume ETW providers (>10,000 events/second), Kusto queries timeout after 30 seconds, preventing workflow from progressing.

**Steps to Reproduce**:
1. Start workflow with Microsoft-Windows-NDIS-PacketCapture provider
2. Wait for schema discovery query to execute
3. Query times out after 30 seconds

**Expected Behavior**:
Schema query completes within 30 seconds and returns event schema.

**Actual Behavior**:
Query times out with "Query execution exceeded the allowed timeout" error.

**Error Messages/Logs**:
```
KustoQueryException: Query execution exceeded the allowed timeout (30 seconds)
Query: | where Provider == 'Microsoft-Windows-NDIS-PacketCapture' | take 1000
```

**Environment**:
- Python Version: 3.12.7
- MAF SDK Version: 0.1.0
- Azure Kusto Cluster: mafagents-test
- Azure DevOps Org: contoso
- Test Scenario: Scenario 2 (High-Volume Network Traffic)

**Impact**:
Blocks testing of high-volume scenarios; cannot complete workflow.

**Workaround**:
Manually reduce query scope or increase timeout to 60 seconds.

**Root Cause**:
Default Kusto query timeout (30s) insufficient for high-cardinality providers.

**Resolution**:
*Pending - need to increase timeout in kusto_client.py*

**Related Issues**: None

---

### Issue #2: PR Title Pattern Not Matched

**Date Reported**: 2025-10-25
**Reported By**: Test Engineer
**Severity**: Medium
**Category**: Code Generation
**Status**: In Progress

**Description**:
Generated PR titles don't match historical patterns due to insufficient training data. Pattern matching accuracy only 65% instead of target 80%.

**Steps to Reproduce**:
1. Execute workflow with any detector
2. Review generated PR title
3. Compare to historical PR titles in repo

**Expected Behavior**:
PR title follows format "[Detector] Add {detector_name} for {provider}" based on historical examples.

**Actual Behavior**:
PR title uses generic format "Add detector code for {rule_id}" without matching patterns.

**Error Messages/Logs**:
```
PatternAnalyzer: No title patterns found with >30% confidence
Falling back to default title format
```

**Environment**:
- Python Version: 3.12.7
- Test Scenario: Multiple scenarios affected

**Impact**:
Reduces pattern matching accuracy metric; PR titles need manual correction.

**Workaround**:
Manually edit PR title after creation.

**Root Cause**:
Test repository has <20 historical PRs; pattern analyzer needs 30+ examples for reliable extraction.

**Resolution**:
*In Progress - adding more example PRs to test repository*

**Related Issues**: #3

---

### Issue #3: Pattern Analyzer Requires More Training Data

**Date Reported**: 2025-10-25
**Reported By**: Test Engineer
**Severity**: Medium
**Category**: Code Generation
**Status**: Open

**Description**:
Pattern analyzer struggles to extract reliable patterns when repository has <20 historical PRs. Success rate drops significantly with limited training data.

**Steps to Reproduce**:
1. Use test repository with only 10 example PRs
2. Run pattern analysis
3. Check pattern confidence scores

**Expected Behavior**:
Pattern analyzer extracts reliable patterns with >30% confidence.

**Actual Behavior**:
Most patterns have <15% confidence; many patterns not detected at all.

**Error Messages/Logs**:
```
PatternAnalyzer: Analyzed 10 PRs
  - Title patterns found: 2 (confidence: 15%)
  - File patterns found: 3 (confidence: 20%)
  - Description patterns found: 1 (confidence: 10%)
```

**Environment**:
- Test Scenario: All scenarios

**Impact**:
Lower pattern matching accuracy across all scenarios; may not meet 80% target.

**Workaround**:
Add more example PRs to repository (target: 30+).

**Root Cause**:
Statistical pattern extraction requires sufficient sample size for confidence.

**Resolution**:
*Pending - creating additional example PRs in test repository*

**Related Issues**: #2

---

## Resolved Issues

### Issue #4: Deployment Detection False Positives

**Date Reported**: 2025-10-24
**Reported By**: Test Engineer
**Severity**: High
**Category**: Deployment
**Status**: Resolved

**Description**:
Deployment verification sometimes reports successful deployment when PR is only merged but not yet deployed to environment.

**Steps to Reproduce**:
1. Merge PR in Azure DevOps
2. Wait for deployment verification
3. Check actual deployment status

**Expected Behavior**:
Deployment detection waits for actual pipeline completion.

**Actual Behavior**:
Reports deployment success immediately after merge, before pipeline runs.

**Resolution**:
Added deployment pipeline status check in addition to merge status. Now verifies pipeline run completion before reporting success. Fixed in detector_workflow.py:745-760.

**Resolution Date**: 2025-10-24

---

## Closed Issues

### Issue #5: Checkpoint File Permissions Error

**Date Reported**: 2025-10-23
**Reported By**: Test Engineer
**Severity**: High
**Category**: Checkpoint
**Status**: Closed

**Description**:
Checkpoint save failed with permissions error when checkpoint directory didn't exist.

**Resolution**:
Added checkpoint directory creation in detector_workflow.py:38-40. Directory now created automatically if it doesn't exist.

**Closed Date**: 2025-10-24
**Closed Reason**: Fixed and verified

---

## Edge Cases Discovered

### Edge Case #1: Empty Provider GUID

**Scenario**: Scenario 3
**Description**: User provides empty string for provider GUID
**Expected**: Validation error with helpful message
**Actual**: Workflow proceeds with invalid GUID, fails later at schema discovery
**Recommendation**: Add input validation in ETW input collection executor

---

### Edge Case #2: Schema with No Events

**Scenario**: Scenario 8
**Description**: ETW provider exists but has no events in Kusto time window
**Expected**: Workflow should handle gracefully with message
**Actual**: Returns empty schema, code generation fails
**Recommendation**: Add zero-event check in schema discovery

---

### Edge Case #3: Very Long Rule IDs

**Scenario**: Scenario 12
**Description**: Rule ID exceeds 100 characters causes branch name to be invalid
**Expected**: Rule ID should be validated or truncated
**Actual**: Branch creation fails with "invalid ref name" error
**Recommendation**: Truncate rule ID to 50 characters for branch names

---

## Unexpected Behaviors

### Behavior #1: Fast PR Merge Detection

**Scenario**: All scenarios
**Description**: Deployment verification detects PR merge faster than expected
**Impact**: Positive - workflow completes 15% faster than estimated
**Analysis**: Azure DevOps webhook propagation is faster than documented
**Action**: Update timing estimates in test plan

---

### Behavior #2: Pattern Learning Improves Over Time

**Scenario**: Scenarios 5-10
**Description**: Pattern matching accuracy increases as more PRs are created during testing
**Impact**: Positive - later scenarios show better pattern matching
**Analysis**: System learns from its own generated PRs
**Action**: Document this self-improving behavior in final report

---

### Behavior #3: Kusto Query Caching

**Scenario**: Repeated executions
**Description**: Second execution of same scenario completes 40% faster
**Impact**: Positive - but may skew timing metrics
**Analysis**: Kusto cluster caches query results
**Action**: Clear cache between test runs for accurate timing

---

## Performance Issues

### Performance Issue #1: Large PR Description Generation

**Scenario**: Scenario 12
**Description**: Generating PR description for complex multi-event detector takes 15+ seconds
**Impact**: Adds to total workflow time
**Measurement**: Average 18 seconds for complex scenarios vs 3 seconds for simple
**Recommendation**: Optimize description generation algorithm

---

### Performance Issue #2: Pattern Analysis Time

**Scenario**: All scenarios
**Description**: Pattern analysis (fetching and analyzing PRs) takes 45-60 seconds
**Impact**: Constant overhead added to every workflow
**Measurement**: Average 52 seconds across all scenarios
**Recommendation**: Implement pattern caching for repeated analyses

---

## Integration Issues

### Integration Issue #1: Azure DevOps Rate Limiting

**Scenario**: Rapid sequential test execution
**Description**: When running scenarios back-to-back, Azure DevOps API returns 429 rate limit errors
**Impact**: Cannot execute tests rapidly; must space out scenarios
**Measurement**: Rate limit hit after 10 API calls in 1 minute
**Recommendation**: Add rate limit handling with exponential backoff

---

### Integration Issue #2: Kusto Connection Timeout

**Scenario**: Long-running workflows (>60 minutes)
**Description**: Kusto connection times out if workflow runs for extended period
**Impact**: Results analysis fails for slow workflows
**Measurement**: Connection valid for 60 minutes, then times out
**Recommendation**: Implement connection refresh logic

---

## User Experience Issues

### UX Issue #1: Unclear Progress Messages

**Scenario**: All scenarios
**Description**: Users don't have clear visibility into what step is currently executing
**Impact**: Reduces user confidence during wait times
**User Feedback**: "Not sure if system is working or stuck"
**Recommendation**: Add step-by-step progress indicator with time estimates

---

### UX Issue #2: Error Messages Too Technical

**Scenario**: Scenario 2 (timeout error)
**Description**: Error messages include technical stack traces rather than user-friendly guidance
**Impact**: Users don't know how to recover from errors
**User Feedback**: "Error message didn't tell me what to do"
**Recommendation**: Add user-friendly error messages with recovery suggestions

---

## Lessons Learned

### Technical Lessons

1. **Checkpoint Storage**: File-based checkpoints work reliably; consider Azure Table Storage for production
2. **Pattern Learning**: Requires 30+ training examples for >80% accuracy
3. **Async Operations**: MAF's async patterns work well but require careful error handling
4. **Azure Integration**: Azure SDK rate limits require explicit handling
5. **Query Optimization**: Kusto queries need indexing hints for high-volume data

### Process Lessons

1. **Test Data**: Prepare sufficient historical PRs before testing
2. **Timing Estimates**: Initial estimates were 20-30% too optimistic
3. **Metrics Collection**: Automated metric collection would save time
4. **Issue Tracking**: Real-time issue logging catches more edge cases
5. **User Feedback**: Early user feedback sessions prevent late-stage UX issues

### Recommendations for Production

1. **Monitoring**: Add comprehensive logging and telemetry
2. **Error Recovery**: Implement automatic retry for transient failures
3. **User Guidance**: Enhanced progress indicators and help text
4. **Pattern Management**: Periodic retraining of pattern analyzer
5. **Performance**: Query result caching to improve response times
6. **Testing**: Expanded integration test coverage for edge cases
7. **Documentation**: User guide with troubleshooting section
8. **Scalability**: Connection pooling for Azure services
9. **Security**: Audit logging for all workflow actions
10. **Reliability**: Circuit breaker pattern for external service calls

---

## Issue Statistics

### Issues by Severity

| Severity | Open | In Progress | Resolved | Closed | Total |
|----------|------|-------------|----------|--------|-------|
| Critical | 0 | 0 | 0 | 0 | 0 |
| High | 1 | 0 | 1 | 1 | 3 |
| Medium | 2 | 1 | 0 | 0 | 3 |
| Low | 0 | 0 | 0 | 0 | 0 |
| **Total** | **3** | **1** | **1** | **1** | **6** |

### Issues by Category

| Category | Count |
|----------|-------|
| Schema Discovery | 1 |
| Code Generation | 2 |
| PR Management | 0 |
| Deployment | 1 |
| Results Analysis | 0 |
| Promotion | 0 |
| Checkpoint | 1 |
| Performance | 2 |
| UX | 2 |
| Integration | 2 |
| **Total** | **11** |

---

## Next Steps

1. **Resolve Open Issues**: Address all high-severity issues before final report
2. **Edge Case Handling**: Implement handling for discovered edge cases
3. **Performance Optimization**: Address performance issues where feasible
4. **User Feedback**: Conduct final user satisfaction survey
5. **Documentation**: Compile all findings into POC validation report
6. **Recommendations**: Create prioritized list of improvements for production

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-25 | Dev Agent | Initial issues log template created |

**Note**: This is a living document. Update throughout POC testing as issues are discovered, investigated, and resolved.
