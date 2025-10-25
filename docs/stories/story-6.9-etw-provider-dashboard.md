# Story 6.9: ETW Provider Information Dashboard

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **user**,
I want **to view ETW provider information and active detectors in the dashboard**,
so that **I can understand what providers are being monitored and their current state**.

## Acceptance Criteria

1. **AC1**: Dashboard displays section for "Active Detectors" with provider GUID and rule ID
2. **AC2**: Active detectors are fetched from backend API endpoint
3. **AC3**: Each detector card shows: provider name, GUID, rule ID, deployment status, last updated
4. **AC4**: Detector cards are searchable/filterable by provider GUID or name
5. **AC5**: Clicking detector card shows detector details (source code link, results link)
6. **AC6**: Empty state is shown when no active detectors exist
7. **AC7**: Provider information is cached and refreshed every 30 seconds
8. **AC8**: Loading skeleton is displayed while fetching provider data

## Integration Verification

- **IV1**: Backend provides `/api/detectors` endpoint with mock data for at least 3 detectors
- **IV2**: Verify dashboard displays all active detectors from backend
- **IV3**: Search for specific provider GUID and verify filtering works
- **IV4**: Complete workflow creating new detector, verify it appears in active detectors list

## Technical Notes

### Backend Endpoint Required

**Note**: This story requires a new backend endpoint to be created:

```python
@app.get("/api/detectors")
async def list_detectors():
    """List all active detectors from Azure Repos/deployment."""
    # Implementation would query Azure DevOps for deployed detectors
    return {
        "detectors": [
            {
                "detector_id": "detector-123",
                "provider_guid": "{00000000-0000-0000-0000-000000000001}",
                "provider_name": "Microsoft-Windows-Security-Auditing",
                "rule_id": "SuspiciousProcessCreation_v1",
                "deployment_status": "deployed",
                "environment": "production",
                "created_at": "2025-10-20T10:30:00Z",
                "last_updated": "2025-10-24T15:45:00Z",
                "repo_url": "https://dev.azure.com/...",
            }
        ],
        "total": 1
    }
```

### Detector Card Component

```typescript
interface DetectorCardProps {
  detectorId: string;
  providerGuid: string;
  providerName: string;
  ruleId: string;
  deploymentStatus: "deployed" | "pending" | "failed";
  lastUpdated: string;
  repoUrl?: string;
}
```

### Dashboard Section Layout

Add to existing dashboard page (`/dashboard`):

```
┌─────────────────────────────────────────────────────┐
│  Active Detectors                                   │
│  🔍 Search: [_________________]                     │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐   │
│  │ Microsoft-Windows-Security-Auditing          │   │
│  │ GUID: {00000...}                             │   │
│  │ Rule: SuspiciousProcessCreation_v1           │   │
│  │ Status: ● Deployed | Updated: 2h ago         │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │ Microsoft-Windows-DNS-Client                 │   │
│  │ ...                                          │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Dependencies

- **Depends on**: Story 6.1 (Core Frontend Refactoring)
- **Depends on**: Story 6.2 (Backend REST API Integration)
- **Depends on**: Story 6.7 (Dashboard Landing Page)
- **Backend work**: New `/api/detectors` endpoint required

## Related Documents

- PRD: docs/prd.md (Story 1.9)
- Dashboard Components: client/src/components/dashboard/
