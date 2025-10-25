# Epic 6: Production-Ready Next.js Frontend Integration

## Epic Goal

Transform the existing Next.js 16 prototype into a production-ready web application with full backend integration, conversational chat interface, informational dashboard, and Azure deployment capability.

## Background

The maf-agents backend has been successfully implemented with Microsoft Agent Framework and is production-ready. However, the existing Next.js frontend prototype (`client/`) requires significant refactoring and complete backend integration to provide a production-quality user experience. This epic bridges the gap between the proven backend and a production-ready web interface.

## Integration Requirements

- Maintain compatibility with production-ready FastAPI backend
- Preserve existing component library (shadcn/ui) and styling approach (Tailwind CSS v4)
- Work within monorepo structure without disrupting backend development
- Support Azure deployment pipeline and infrastructure

## Stories

1. **Story 6.1**: Core Frontend Refactoring and State Management
2. **Story 6.2**: Backend REST API Integration
3. **Story 6.3**: WebSocket Integration for Real-Time Updates
4. **Story 6.4**: Enhanced Chat Interface with Backend Integration
5. **Story 6.5**: Workflow Step Components Integration
6. **Story 6.6**: Session Persistence and Recovery
7. **Story 6.7**: Dashboard Landing Page
8. **Story 6.8**: Workflow History Detail View
9. **Story 6.9**: ETW Provider Information Dashboard
10. **Story 6.10**: Error Handling and User Feedback
11. **Story 6.11**: Azure Deployment Configuration

## Success Criteria

- All 11 stories completed and tested
- Frontend successfully connects to production backend
- Dashboard displays real-time workflow and detector information
- Application deployed to Azure and accessible
- Production-grade error handling and user experience
- Complete integration verification passed

## Related Documents

- PRD: docs/prd.md (Epic 1: Production-Ready Next.js Frontend Integration)
- Architecture: docs/architecture.md
- Backend API: server/api/main.py
