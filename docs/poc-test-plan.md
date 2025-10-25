# POC Test Plan: maf-agents Detector Development Workflow

**Document Version**: 1.0
**Date**: 2025-10-25
**Purpose**: Validate maf-agents POC with 10+ detector scenarios covering various ETW providers and schema types

---

## Test Objectives

This test plan validates the maf-agents system meets the following success criteria:

1. **Cycle Time Reduction**: Complete detector workflow in <2 hours (70% reduction from 6-hour baseline)
2. **Pattern Matching Accuracy**: Generated code matches historical patterns with >80% accuracy
3. **Checkpoint Recovery**: Workflows can reliably resume from checkpoints after interruptions
4. **Workflow Completion**: All 8 executors execute successfully for multiple detector types
5. **User Satisfaction**: Interface rated as "easy to use" (4/5 or higher)

---

## Test Scenarios

### Scenario 1: Standard Security Alert Detector

**Provider**: Microsoft-Windows-Security-Auditing
**Rule ID**: `security_logon_failure_detector`
**Description**: Detect repeated failed logon attempts indicating potential brute force attack
**Schema Complexity**: Medium (5-8 fields)
**Expected Duration**: 45-60 minutes

**Test Steps**:
1. Start workflow with provider GUID and rule ID
2. Validate schema discovery from Kusto
3. Review generated detector code for pattern consistency
4. Approve PR and wait for merge
5. Verify deployment detection
6. Analyze results from Kusto queries
7. Confirm results and create production promotion PR

**Success Criteria**:
- Schema correctly identified
- Code follows security detector patterns
- PR created with appropriate title/description
- Deployment detected within 5 minutes of merge
- Results analysis shows event counts and error rates
- Promotion PR created with feature flag configuration

---

### Scenario 2: High-Volume Network Traffic Detector

**Provider**: Microsoft-Windows-NDIS-PacketCapture
**Rule ID**: `network_anomaly_detector`
**Description**: Detect unusual network traffic patterns
**Schema Complexity**: High (10+ fields)
**Expected Duration**: 60-90 minutes

**Test Steps**:
1. Execute workflow with network provider GUID
2. Validate complex schema discovery (multiple event types)
3. Review code generation for high-cardinality field handling
4. Approve PR with multi-file changes
5. Verify deployment and wait for stabilization
6. Analyze high-volume results data
7. Confirm and promote to production

**Success Criteria**:
- Complex schema correctly parsed
- Code handles high-cardinality fields appropriately
- Generated queries include performance optimizations
- Results analysis shows aggregated metrics
- Promotion includes appropriate rollout configuration

---

### Scenario 3: Simple Process Creation Detector

**Provider**: Microsoft-Windows-Kernel-Process
**Rule ID**: `suspicious_process_detector`
**Description**: Detect suspicious process creation events
**Schema Complexity**: Low (3-5 fields)
**Expected Duration**: 30-45 minutes

**Test Steps**:
1. Start workflow with process provider
2. Validate simple schema discovery
3. Review minimal code generation
4. Quick PR approval
5. Fast deployment verification
6. Simple results analysis
7. Quick production promotion

**Success Criteria**:
- Simple schema handled efficiently
- Minimal boilerplate code generated
- Fast PR creation (<5 minutes)
- Quick deployment detection
- Straightforward results presentation
- Fast promotion workflow

---

### Scenario 4: File System Activity Detector

**Provider**: Microsoft-Windows-Kernel-File
**Rule ID**: `file_access_anomaly_detector`
**Description**: Detect unusual file system access patterns
**Schema Complexity**: Medium (6-8 fields)
**Expected Duration**: 45-60 minutes

**Test Steps**:
1. Execute workflow with file system provider
2. Discover file operation schema
3. Generate detector for file access patterns
4. Review and approve PR
5. Verify deployment
6. Analyze file activity results
7. Promote to production

**Success Criteria**:
- File operation schema correctly identified
- Code includes file path normalization
- PR includes appropriate documentation
- Results show file access patterns
- Promotion follows file detector conventions

---

### Scenario 5: Registry Modification Detector

**Provider**: Microsoft-Windows-Kernel-Registry
**Rule ID**: `registry_persistence_detector`
**Description**: Detect registry modifications indicating persistence mechanisms
**Schema Complexity**: Medium (5-7 fields)
**Expected Duration**: 45-60 minutes

**Test Steps**:
1. Start workflow with registry provider
2. Discover registry operation schema
3. Generate detector for registry keys
4. Approve PR with registry-specific patterns
5. Verify deployment
6. Analyze registry modification events
7. Promote with security considerations

**Success Criteria**:
- Registry schema parsed correctly
- Code includes registry path handling
- Generated queries filter for persistence indicators
- Results show registry modification patterns
- Promotion includes security documentation

---

### Scenario 6: DNS Query Detector

**Provider**: Microsoft-Windows-DNS-Client
**Rule ID**: `dns_tunneling_detector`
**Description**: Detect potential DNS tunneling activity
**Schema Complexity**: Medium (5-8 fields)
**Expected Duration**: 50-65 minutes

**Test Steps**:
1. Execute workflow with DNS provider
2. Discover DNS query schema
3. Generate detector for DNS patterns
4. Review DNS-specific code patterns
5. Approve and verify deployment
6. Analyze DNS query results
7. Promote with DNS documentation

**Success Criteria**:
- DNS schema correctly identified
- Code includes domain name parsing
- Queries identify tunneling indicators
- Results show DNS query patterns
- Promotion follows network detector patterns

---

### Scenario 7: PowerShell Execution Detector

**Provider**: Microsoft-Windows-PowerShell
**Rule ID**: `powershell_obfuscation_detector`
**Description**: Detect obfuscated PowerShell command execution
**Schema Complexity**: High (8-12 fields)
**Expected Duration**: 60-90 minutes

**Test Steps**:
1. Start workflow with PowerShell provider
2. Discover complex PowerShell event schema
3. Generate detector for script block analysis
4. Review complex pattern matching code
5. Approve multi-file PR
6. Verify deployment and wait for data
7. Analyze PowerShell execution results
8. Promote with extensive testing notes

**Success Criteria**:
- Complex PowerShell schema parsed
- Code includes script analysis logic
- Pattern matching for obfuscation techniques
- Results show command execution patterns
- Promotion includes comprehensive documentation

---

### Scenario 8: Scheduled Task Detector

**Provider**: Microsoft-Windows-TaskScheduler
**Rule ID**: `malicious_task_detector`
**Description**: Detect suspicious scheduled task creation
**Schema Complexity**: Medium (6-9 fields)
**Expected Duration**: 45-60 minutes

**Test Steps**:
1. Execute workflow with task scheduler provider
2. Discover scheduled task schema
3. Generate detector for task patterns
4. Review task-specific code
5. Approve and deploy
6. Analyze scheduled task events
7. Promote to production

**Success Criteria**:
- Task scheduler schema identified
- Code includes task attribute parsing
- Queries filter for suspicious patterns
- Results show task creation events
- Promotion includes persistence documentation

---

### Scenario 9: WMI Activity Detector

**Provider**: Microsoft-Windows-WMI-Activity
**Rule ID**: `wmi_persistence_detector`
**Description**: Detect WMI-based persistence mechanisms
**Schema Complexity**: High (9-11 fields)
**Expected Duration**: 60-80 minutes

**Test Steps**:
1. Start workflow with WMI provider
2. Discover WMI event schema
3. Generate detector for WMI operations
4. Review complex WMI code patterns
5. Approve sophisticated PR
6. Verify deployment
7. Analyze WMI activity results
8. Promote with security considerations

**Success Criteria**:
- WMI schema correctly parsed
- Code handles WMI query language
- Pattern matching for persistence indicators
- Results show WMI operations
- Promotion includes threat documentation

---

### Scenario 10: Network Connection Detector

**Provider**: Microsoft-Windows-Kernel-Network
**Rule ID**: `c2_connection_detector`
**Description**: Detect potential command-and-control network connections
**Schema Complexity**: Medium (7-9 fields)
**Expected Duration**: 50-70 minutes

**Test Steps**:
1. Execute workflow with network kernel provider
2. Discover network connection schema
3. Generate detector for connection patterns
4. Review network-specific code
5. Approve and deploy
6. Analyze connection events
7. Promote with threat intelligence

**Success Criteria**:
- Network schema identified
- Code includes IP/port analysis
- Queries identify suspicious connections
- Results show connection patterns
- Promotion includes IOC documentation

---

### Scenario 11: Checkpoint Recovery Test

**Provider**: Microsoft-Windows-Security-Auditing
**Rule ID**: `checkpoint_recovery_test_detector`
**Description**: Validate checkpoint recovery by intentionally interrupting workflow
**Schema Complexity**: Medium (5-7 fields)
**Expected Duration**: 60-75 minutes (including interruption)

**Test Steps**:
1. Start workflow normally
2. Allow schema discovery to complete
3. **Interrupt workflow after code generation (before PR creation)**
4. List saved checkpoints
5. Resume workflow from latest checkpoint
6. Verify workflow continues from interruption point
7. Complete remaining steps (PR, deployment, results, promotion)

**Success Criteria**:
- Checkpoint saved after code generation
- Workflow successfully resumes from checkpoint
- No data loss from interruption
- Remaining steps complete normally
- Final output matches expected state

---

### Scenario 12: Multi-Event Type Detector

**Provider**: Microsoft-Windows-Sysmon (multiple event IDs)
**Rule ID**: `multi_event_correlation_detector`
**Description**: Detect attack patterns requiring correlation across multiple event types
**Schema Complexity**: Very High (15+ fields across multiple event types)
**Expected Duration**: 90-120 minutes

**Test Steps**:
1. Execute workflow with Sysmon provider
2. Discover schemas for multiple event types
3. Generate detector with event correlation logic
4. Review complex multi-event code
5. Approve comprehensive PR
6. Verify deployment
7. Analyze correlated results
8. Promote with correlation documentation

**Success Criteria**:
- Multiple event schemas discovered
- Code includes correlation logic
- Queries join multiple event types
- Results show correlated patterns
- Promotion includes advanced documentation

---

## Metrics Collection

For each scenario, collect the following metrics:

### Timing Metrics

- **Total Workflow Duration**: Start to production promotion PR creation
- **Schema Discovery Time**: ETW input to schema identified
- **Code Generation Time**: Schema discovery to PR created
- **PR Approval Time**: PR created to user approval
- **Deployment Detection Time**: PR merged to deployment detected
- **Results Analysis Time**: Deployment detected to results presented
- **Promotion Time**: Results confirmed to promotion PR created

### Quality Metrics

- **Pattern Matching Accuracy**: % of generated code following historical patterns
  - Code structure matches examples: Yes/No
  - Naming conventions followed: Yes/No
  - File organization correct: Yes/No
  - Documentation style matches: Yes/No
  - Overall accuracy: (sum / 4) * 100%

- **Code Quality Score**: Review of generated code
  - Syntax errors: Count
  - Logic errors: Count
  - Missing required fields: Count
  - Unnecessary boilerplate: Count
  - Overall quality: (10 - errors) / 10 * 100%

### Reliability Metrics

- **Workflow Completion Rate**: % of scenarios completed successfully
- **Error Recovery Rate**: % of errors recovered automatically
- **Checkpoint Recovery Success**: Did resume work? Yes/No
- **False Positive Rate**: Incorrect deployment detections
- **Results Accuracy**: % of Kusto results correctly interpreted

### User Experience Metrics

- **Ease of Use Rating**: 1-5 scale (target: 4+)
  - Input collection clear: 1-5
  - Progress visibility good: 1-5
  - Error messages helpful: 1-5
  - Overall experience: 1-5

- **Cognitive Load**: How much manual effort required?
  - Schema understanding needed: Low/Medium/High
  - Code review complexity: Low/Medium/High
  - Decision points clear: Yes/No
  - Overall cognitive load: Low/Medium/High

---

## Test Environment

### Configuration

- **Azure DevOps Organization**: [Configure with actual org]
- **Azure DevOps Project**: [Configure with actual project]
- **Azure Repos Repository**: [Configure with test repository]
- **Azure Kusto Cluster**: [Configure with actual cluster]
- **Azure Kusto Database**: [Configure with test database]

### Test Data Requirements

- Historical PRs with detector patterns (minimum 20 PRs)
- ETW schema data in Kusto cluster
- Test event data for results analysis
- Deployment pipeline configured

### Environment Variables

```bash
AZURE_DEVOPS_ORG="[org-name]"
AZURE_DEVOPS_PROJECT="[project-name]"
AZURE_DEVOPS_REPO="[repo-name]"
KUSTO_CLUSTER_URL="https://[cluster].kusto.windows.net"
KUSTO_DATABASE_NAME="[database-name]"
MAF_AUTO_CONFIRM_RESULTS="false"  # Manual confirmation for testing
```

---

## Test Execution Plan

### Phase 1: Simple Scenarios (Scenarios 1, 3)

**Goal**: Validate basic workflow functionality
**Duration**: 1.5-2 hours
**Success Threshold**: 100% completion, <60 minutes per scenario

### Phase 2: Medium Complexity (Scenarios 4, 5, 6, 8, 10)

**Goal**: Validate pattern matching and code quality
**Duration**: 4-5 hours
**Success Threshold**: 100% completion, >80% pattern accuracy

### Phase 3: High Complexity (Scenarios 2, 7, 9, 12)

**Goal**: Validate system handles complex schemas
**Duration**: 5-6 hours
**Success Threshold**: 90%+ completion, graceful error handling

### Phase 4: Checkpoint Recovery (Scenario 11)

**Goal**: Validate checkpoint persistence and resume
**Duration**: 1.5 hours
**Success Threshold**: 100% successful resume, no data loss

### Phase 5: User Experience Validation

**Goal**: Collect user satisfaction feedback
**Duration**: 30 minutes (survey after scenarios)
**Success Threshold**: 4/5 or higher on ease of use

---

## Success Criteria Summary

The POC is considered successful if:

| Criterion | Target | Measurement Method |
|-----------|--------|-------------------|
| Cycle Time Reduction | <2 hours per detector | Average total duration across scenarios 1-10 |
| Pattern Matching Accuracy | >80% | Average pattern accuracy across all scenarios |
| Checkpoint Recovery | 100% success | Scenario 11 successful resume |
| Workflow Completion Rate | >90% | Scenarios completed / total scenarios |
| User Satisfaction | 4/5 or higher | Average ease of use rating |
| Code Quality | <2 errors per scenario | Average syntax/logic errors |
| Deployment Detection | >95% accuracy | Correct detections / total deployments |

---

## Risk Mitigation

### Risk: Azure Services Unavailable

- **Mitigation**: Test during off-peak hours
- **Contingency**: Reschedule test execution

### Risk: Historical Patterns Insufficient

- **Mitigation**: Ensure 20+ example PRs available
- **Contingency**: Lower pattern accuracy threshold to 70%

### Risk: Long Deployment Times

- **Mitigation**: Use test repository with fast pipelines
- **Contingency**: Increase deployment detection timeout

### Risk: Kusto Query Timeouts

- **Mitigation**: Optimize queries upfront
- **Contingency**: Implement query result caching

---

## Test Report Template

After executing all scenarios, compile results into POC Validation Report:

1. **Executive Summary**: Overall success/failure, key findings
2. **Metrics Dashboard**: All collected metrics vs. targets
3. **Issues Log**: All errors, failures, edge cases encountered
4. **Pattern Accuracy Analysis**: Detailed review of code quality
5. **User Feedback**: Survey results and qualitative feedback
6. **Recommendations**: Suggestions for production implementation
7. **Lessons Learned**: What worked well, what needs improvement

---

## Appendix A: Metric Collection Templates

### Timing Metrics Spreadsheet

| Scenario | Total Duration | Schema Time | Code Gen Time | PR Approval Time | Deploy Time | Results Time | Promotion Time |
|----------|---------------|-------------|---------------|------------------|-------------|--------------|----------------|
| 1        |               |             |               |                  |             |              |                |
| 2        |               |             |               |                  |             |              |                |
| ...      |               |             |               |                  |             |              |                |

### Pattern Accuracy Scorecard

| Scenario | Code Structure | Naming | File Org | Documentation | Overall |
|----------|---------------|--------|----------|---------------|---------|
| 1        | Y/N           | Y/N    | Y/N      | Y/N           | %       |
| 2        | Y/N           | Y/N    | Y/N      | Y/N           | %       |
| ...      | Y/N           | Y/N    | Y/N      | Y/N           | %       |

### User Experience Survey

1. How easy was it to provide ETW input? (1-5)
2. How clear was the workflow progress? (1-5)
3. How useful were error messages? (1-5)
4. How confident are you in generated code? (1-5)
5. Overall satisfaction with the system? (1-5)
6. Would you use this for production work? (Yes/No)
7. What worked well?
8. What needs improvement?

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-25 | Dev Agent | Initial test plan created |

