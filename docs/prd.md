# maf-agents Brownfield Enhancement PRD
# Production-Ready Next.js Frontend Integration

## Intro Project Analysis and Context

### Analysis Source
**Source**: IDE-based fresh analysis of existing codebase
- Architecture documentation: `docs/architecture.md`
- Existing PRD: `docs/prd.md`
- Backend API server: `server/api/main.py`
- Frontend client: `client/` (Next.js 16)

---

### Existing Project Overview

#### Current Project State

**maf-agents** is a **stateless workflow orchestration engine** built on Microsoft Agent Framework (Python) that automates the end-to-end Azure detector development lifecycle. The system achieves a 70% cycle time reduction (6hrs → <2hrs) by orchestrating 8 specialized executors through a conversational workflow with human-in-the-loop approval gates.

**Core Backend Architecture**:
- Microsoft Agent Framework (Python 3.10+) with sequential executor pattern
- FastAPI server with REST + WebSocket APIs (`server/api/main.py`)
- Checkpoint-based state persistence (FileCheckpointStorage)
- Azure-native integrations (Azure Repos, Azure Kusto)
- 9-step workflow: Triage → ETW Input → Schema Discovery → Code Gen → PR Creation → Approval → Deployment → Results Analysis → Production Promotion
- **Status**: Production-ready

**Existing Frontend** (`client/`):
- Next.js 16 with React 19 and TypeScript
- Tailwind CSS v4 + shadcn/ui components
- API client with WebSocket support (`lib/api-client.ts`)
- Basic workflow page with chat interface
- Components: `ChatInterface`, `ETWInputForm`, `ApprovalDialog`, `WorkflowStepper`
- **Status**: Prototype with incomplete backend integration; requires refactoring

---

### Available Documentation Analysis

✅ **Available Documentation**:
- ✓ Tech Stack Documentation (`docs/architecture.md`)
- ✓ Source Tree/Architecture (Monorepo structure defined)
- ✓ Coding Standards (Documented in architecture)
- ✓ API Documentation (FastAPI endpoints in `server/api/main.py`)
- ✓ External API Documentation (Azure SDKs documented)
- ✗ UX/UI Guidelines (To be created)
- ✓ Technical Debt Documentation (`docs/poc-issues-log.md`)

**Assessment**: Strong technical documentation exists. This PRD adds comprehensive UI/UX requirements for production frontend.

---

### Enhancement Scope Definition

#### Enhancement Type
- ☑ **New Feature Addition** (Production-ready web UI)
- ☑ **Integration with Existing Systems** (Backend workflow integration)
- ☑ **UI/UX Overhaul** (Transform prototype to production)

#### Enhancement Description
Transform the existing Next.js 16 prototype (`client/`) into a **production-ready web application** with two primary capabilities: (1) a **conversational chat interface** that integrates with the Microsoft Agent Framework workflow backend for guided detector development, and (2) an **informational dashboard** displaying active detectors, provider information, workflow history, and system health metrics.

#### Impact Assessment
- ☑ **Moderate Impact**: Existing frontend structure remains; requires refactoring and replacing mocks with real integrations
- Backend API already supports required operations; minimal backend changes needed
- New dashboard components will be added as separate routes
- Existing workflow components will be enhanced with production-grade features

---

### Goals and Background Context

#### Goals
1. Refactor existing Next.js frontend into production-grade code structure
2. Replace mock/simulated frontend data with full backend API integration
3. Implement production-ready conversational chat interface with real-time workflow updates
4. Build informational dashboard showing active detectors, provider data, and workflow metrics
5. Achieve production-grade reliability, error handling, and user experience
6. Support concurrent workflow sessions with proper state management
7. Enable deployment to Azure App Service with proper configuration

#### Background Context
The maf-agents backend has been successfully implemented with Microsoft Agent Framework and validated through CLI interactions. The system is production-ready and capable of automating detector development workflows. However, the existing Next.js frontend prototype (`client/`) requires significant refactoring and complete backend integration to provide a production-quality user experience. This enhancement bridges the gap between the proven backend and a production-ready web interface that makes the system accessible to a broader range of users.

---

### Change Log

| Change | Date | Version | Description | Author |
|--------|------|---------|-------------|---------|
| Initial Draft | 2025-10-25 | 1.0 | Brownfield PRD for Next.js production frontend | PM Agent (John) |

---

## Requirements

### Functional Requirements

1. **FR1**: The frontend shall establish WebSocket connection to backend for real-time workflow status updates
2. **FR2**: The frontend shall display conversational chat interface that sends user messages to the workflow triage agent
3. **FR3**: The frontend shall receive and display agent responses in real-time through WebSocket events
4. **FR4**: The frontend shall support all 9 workflow steps with appropriate UI components (chat, forms, approval dialogs)
5. **FR5**: The frontend shall display workflow progress using a visual stepper component showing current step status
6. **FR6**: The dashboard shall display list of active detector workflows with their current status
7. **FR7**: The dashboard shall display ETW provider information retrieved from backend
8. **FR8**: The dashboard shall show workflow history with completion status and timestamps
9. **FR9**: The frontend shall handle workflow approval gates with approve/reject actions
10. **FR10**: The frontend shall support submitting ETW input data (providerGuid, ruleId) to the workflow
11. **FR11**: The frontend shall display generated PR information during approval steps
12. **FR12**: The frontend shall show deployment verification status and results analysis data
13. **FR13**: The dashboard shall display system health metrics (active workflows, connection status, backend health)
14. **FR14**: The frontend shall support concurrent workflow sessions with proper state isolation
15. **FR15**: The frontend shall persist workflow state in browser for session recovery on page refresh
16. **FR16**: The frontend shall implement error boundaries to catch and display React component errors gracefully
17. **FR17**: The frontend shall provide user feedback for all async operations (loading spinners, progress bars)
18. **FR18**: The chat interface shall support markdown rendering for formatted agent responses
19. **FR19**: The frontend shall allow users to navigate between active workflow sessions
20. **FR20**: The dashboard shall provide export functionality for workflow history (CSV/JSON)

### Non-Functional Requirements

1. **NFR1**: The frontend shall maintain existing Next.js 16 and React 19 tech stack
2. **NFR2**: The frontend shall use existing Tailwind CSS v4 and shadcn/ui component library
3. **NFR3**: WebSocket reconnection shall implement exponential backoff with maximum 30-second retry interval
4. **NFR4**: UI shall remain responsive during workflow execution with loading states and progress indicators
5. **NFR5**: Error messages shall be user-friendly and actionable (no raw stack traces displayed)
6. **NFR6**: The frontend shall implement TypeScript strict mode with no `any` types in production code
7. **NFR7**: The frontend shall be deployable to Azure Static Web Apps or Azure App Service
8. **NFR8**: Environment configuration shall use `.env.local` for development and Azure App Settings for production
9. **NFR9**: API client shall implement retry logic for failed HTTP requests (3 retries with exponential backoff)
10. **NFR10**: The frontend shall support browser back/forward navigation without breaking workflow state
11. **NFR11**: The application shall be responsive and functional on desktop browsers (Chrome, Edge, Firefox, Safari)
12. **NFR12**: Page load time shall be under 3 seconds on standard broadband connection
13. **NFR13**: The frontend shall implement proper React hooks patterns (no class components)
14. **NFR14**: All API calls shall include proper error handling and timeout configuration (30 second timeout)
15. **NFR15**: The frontend shall log errors to browser console in development and to Azure Application Insights in production

### Compatibility Requirements

1. **CR1: Backend API Compatibility**: All frontend API calls must use existing FastAPI endpoints (`/api/workflows`, WebSocket `/ws/workflows/{id}`) without requiring backend changes
2. **CR2: Existing Component Compatibility**: Refactored code must maintain existing shadcn/ui component patterns and Tailwind styling approach
3. **CR3: Monorepo Compatibility**: Frontend deployment configuration must work within existing monorepo structure (`client/` directory)
4. **CR4: Azure Integration Compatibility**: Frontend must integrate with Azure App Service deployment pipeline and support Azure AD authentication (if implemented)

---

## User Interface Enhancement Goals

### Integration with Existing UI

The frontend enhancement will build upon the existing Next.js 16 + React 19 + Tailwind CSS v4 foundation while upgrading from prototype to production quality. The enhancement maintains:

- **Component Library**: Continue using shadcn/ui components with Radix UI primitives
- **Design Language**: Maintain existing Tailwind utility-first approach with consistent spacing, typography, and color schemes
- **Layout Patterns**: Preserve existing container/card-based layouts for consistency

**Key Integration Points**:
- Existing `WorkflowStepper` component will be enhanced with real-time status updates
- Current `ChatInterface` will be refactored to support markdown rendering and WebSocket message streaming
- `ApprovalDialog` will be extended to handle different approval types (code review, results confirmation, production promotion)
- New dashboard components will follow existing card-based layout patterns

### Modified/New Screens and Views

#### Enhanced/Modified Screens

1. **Workflow Page** (`/workflow`) - ENHANCED
   - Replace mock data with real WebSocket integration
   - Add session persistence for page refresh recovery
   - Implement proper error boundaries and loading states
   - Add ability to switch between multiple concurrent workflows

2. **Landing Page** (`/`) - NEW
   - Welcome screen with system overview
   - Quick start guide for creating first detector
   - Link to workflow and dashboard pages

#### New Screens

3. **Dashboard Page** (`/dashboard`) - NEW
   - Active workflows list with status indicators
   - Workflow history table with filtering/search
   - ETW provider information cards
   - System health metrics panel
   - Export functionality for workflow data

4. **Workflow History Detail** (`/dashboard/workflow/[id]`) - NEW
   - Detailed view of completed workflow
   - Step-by-step execution timeline
   - Generated artifacts (PR links, code diffs, results)
   - Conversation history replay

5. **Error Page** (`/error`) - NEW
   - User-friendly error messages
   - Suggested troubleshooting steps
   - Link back to dashboard or create new workflow

### UI Consistency Requirements

1. **Visual Consistency**: All new components must use existing Tailwind color palette (blue-600 primary, gray scale, status colors)
2. **Interaction Patterns**: Maintain existing button styles, form inputs, and modal behaviors from shadcn/ui
3. **Responsive Design**: Desktop-first approach (1280px+ optimal), graceful degradation to 1024px minimum
4. **Loading States**: Consistent use of lucide-react icons (`Loader2`) with spin animation for async operations
5. **Status Indicators**: Standardize status badges (running=blue, completed=green, failed=red) across all views
6. **Typography**: Maintain existing font hierarchy (headings, body text, code/mono)
7. **Spacing**: Continue using Tailwind spacing scale for consistent padding/margins

---

## Technical Constraints and Integration Requirements

### Existing Technology Stack

**Languages**: TypeScript 5.x, JavaScript (ES2022)

**Frameworks**:
- Next.js 16.0.0 (App Router)
- React 19.2.0
- Tailwind CSS v4 (@tailwindcss/postcss)

**UI Libraries**:
- shadcn/ui components (Radix UI primitives)
- lucide-react (icons)
- class-variance-authority (component variants)

**Backend**:
- FastAPI (Python 3.10+)
- Microsoft Agent Framework
- WebSocket support

**Infrastructure**:
- Development: npm/Node.js 20+
- Target Deployment: Azure Static Web Apps or Azure App Service
- Backend: Already deployed/production-ready

**External Dependencies**:
- Backend REST API: `http://localhost:8000/api` (dev), Azure endpoint (prod)
- WebSocket API: `ws://localhost:8000/ws` (dev), Azure endpoint (prod)

### Integration Approach

#### Backend Integration Strategy
- **REST API**: Use existing `apiClient` in `lib/api-client.ts` for workflow CRUD operations
- **WebSocket**: Enhance existing `createWorkflowWebSocket` for real-time event streaming
- **State Management**: Implement React Context for global workflow state with local storage persistence
- **Error Handling**: Centralized error handling with typed error responses from backend

#### Frontend Integration Strategy
- **Component Refactoring**: Extract business logic from components into custom hooks
- **State Management**: Create `WorkflowContext` provider for global state; maintain local state for UI-only concerns
- **Routing**: Use Next.js App Router with proper loading/error boundaries
- **Data Fetching**: Server Components for dashboard data; Client Components for interactive workflow
- **Type Safety**: Generate TypeScript types from backend OpenAPI schema

#### Testing Integration Strategy
- **Unit Tests**: Jest + React Testing Library for component logic
- **Integration Tests**: Mock Service Worker (MSW) for API mocking
- **E2E Tests**: Playwright for critical user flows (deferred to post-MVP)
- **Type Checking**: `tsc --noEmit` in CI pipeline

### Code Organization and Standards

#### File Structure Approach
```
client/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # Landing page
│   │   ├── layout.tsx         # Root layout
│   │   ├── workflow/          # Workflow routes
│   │   └── dashboard/         # Dashboard routes
│   ├── components/
│   │   ├── ui/                # shadcn/ui primitives
│   │   ├── workflow/          # Workflow-specific components
│   │   ├── dashboard/         # Dashboard components
│   │   └── providers/         # React Context providers
│   ├── hooks/                 # Custom React hooks
│   ├── lib/
│   │   ├── api-client.ts      # API client (enhanced)
│   │   ├── utils.ts           # Utility functions
│   │   └── types.ts           # Shared TypeScript types
│   └── styles/                # Global styles
```

#### Naming Conventions
- **Components**: PascalCase (`WorkflowStepper.tsx`)
- **Hooks**: camelCase with `use` prefix (`useWorkflow.ts`)
- **Utilities**: camelCase (`formatTimestamp.ts`)
- **Types**: PascalCase interfaces/types (`WorkflowStatus`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`)

#### Coding Standards
- **TypeScript**: Strict mode enabled; no `any` types; explicit return types for functions
- **React**: Functional components only; hooks for state/effects; proper dependency arrays
- **Formatting**: Prettier with 2-space indent, single quotes, trailing commas
- **Linting**: ESLint with Next.js config + TypeScript rules
- **Comments**: JSDoc for exported functions; inline comments for complex logic only

#### Documentation Standards
- **Component Props**: Document with TypeScript interfaces and JSDoc
- **API Functions**: Document parameters, return types, and error cases
- **README**: Update client/README.md with setup, development, and deployment instructions

### Deployment and Operations

#### Build Process Integration
- **Development**: `npm run dev` (Next.js dev server on port 3000)
- **Build**: `npm run build` (Next.js production build)
- **Type Check**: `npm run type-check` (TypeScript validation)
- **Lint**: `npm run lint` (ESLint check)

#### Deployment Strategy
- **Development**: Local Next.js dev server connecting to local FastAPI backend
- **Staging**: Azure Static Web Apps with preview deployments for PRs
- **Production**: Azure Static Web Apps or Azure App Service with custom domain

#### Monitoring and Logging
- **Client-Side Logging**: Console in dev; Azure Application Insights in production
- **Error Tracking**: React Error Boundaries with error reporting to Application Insights
- **Performance Monitoring**: Next.js built-in analytics + Web Vitals reporting

#### Configuration Management
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: Backend REST API endpoint
  - `NEXT_PUBLIC_WS_URL`: Backend WebSocket endpoint
  - `NEXT_PUBLIC_APP_INSIGHTS_KEY`: Azure Application Insights key (optional)
- **Development**: `.env.local` file (gitignored)
- **Production**: Azure App Settings or Static Web Apps configuration

### Risk Assessment and Mitigation

#### Technical Risks
1. **WebSocket Connection Stability**: Network interruptions could break real-time updates
   - **Mitigation**: Implement automatic reconnection with exponential backoff; fallback to polling if WebSocket unavailable

2. **State Synchronization**: Frontend and backend state could become out of sync
   - **Mitigation**: Implement optimistic UI updates with rollback; periodic state reconciliation

3. **TypeScript Type Drift**: Backend API changes could break frontend types
   - **Mitigation**: Generate types from OpenAPI schema; implement contract testing

#### Integration Risks
1. **Backend API Changes**: Backend modifications could break frontend
   - **Mitigation**: Backend is production-ready; use API versioning if changes needed; comprehensive integration tests

2. **Browser Compatibility**: Modern features might not work in older browsers
   - **Mitigation**: Target modern browsers only (Chrome/Edge/Firefox/Safari latest versions); document requirements

#### Deployment Risks
1. **Azure Configuration**: Incorrect environment variables could cause runtime failures
   - **Mitigation**: Validate configuration on startup; provide clear error messages; comprehensive deployment documentation

2. **Build Failures**: TypeScript/lint errors could block deployment
   - **Mitigation**: Run type-check and lint in pre-commit hooks; CI/CD pipeline validation

#### Mitigation Strategies
- **Comprehensive Error Handling**: Try-catch blocks around all async operations; typed error responses
- **Progressive Enhancement**: Core functionality works without JavaScript; enhance with real-time features
- **Graceful Degradation**: System remains usable if WebSocket fails (fallback to HTTP polling)
- **Monitoring**: Application Insights for production error tracking and performance monitoring

---

## Epic and Story Structure

### Epic Approach

**Epic Structure Decision**: **Single Comprehensive Epic**

**Rationale**: This brownfield enhancement represents a cohesive body of work focused on transforming the existing Next.js prototype into a production-ready frontend. While the work includes multiple features (chat integration, dashboard, deployment), they are all tightly coupled to the same goal and share the same technical foundation. A single epic ensures:

1. **Unified Technical Approach**: All stories share the same refactoring patterns, state management strategy, and integration approach
2. **Sequential Dependencies**: Dashboard and deployment depend on core refactoring and backend integration being complete
3. **Consistent User Experience**: All features must work together seamlessly as a cohesive application
4. **Simplified Planning**: Single epic allows for better prioritization and risk management across related stories

Alternative considered: Multiple epics (Core Refactoring, Chat Integration, Dashboard, Deployment) - rejected due to tight coupling and increased coordination overhead.

---

## Epic 1: Production-Ready Next.js Frontend Integration

**Epic Goal**: Transform the existing Next.js 16 prototype into a production-ready web application with full backend integration, conversational chat interface, informational dashboard, and Azure deployment capability.

**Integration Requirements**:
- Maintain compatibility with production-ready FastAPI backend
- Preserve existing component library (shadcn/ui) and styling approach (Tailwind CSS v4)
- Work within monorepo structure without disrupting backend development
- Support Azure deployment pipeline and infrastructure

---

### Story 1.1: Core Frontend Refactoring and State Management

As a **developer**,
I want to refactor the existing Next.js codebase with production-grade architecture and state management,
so that the application has a solid foundation for backend integration and new features.

#### Acceptance Criteria

1. **AC1**: TypeScript strict mode is enabled with no `any` types in production code
2. **AC2**: Business logic is extracted from components into custom hooks following React best practices
3. **AC3**: Global state management is implemented using React Context (`WorkflowContext`)
4. **AC4**: Error boundaries are implemented at route and component levels to catch rendering errors
5. **AC5**: Consistent file structure is established following Next.js App Router conventions
6. **AC6**: All components use proper TypeScript interfaces for props with JSDoc documentation
7. **AC7**: ESLint and Prettier configurations are updated and passing
8. **AC8**: Existing functionality (workflow page, components) continues to work after refactoring

#### Integration Verification

- **IV1**: Run `npm run type-check` with zero TypeScript errors
- **IV2**: Run `npm run lint` with zero linting errors
- **IV3**: Verify existing workflow page renders without console errors
- **IV4**: Confirm all existing shadcn/ui components still function correctly

---

### Story 1.2: Backend REST API Integration

As a **user**,
I want the frontend to connect to the real backend API instead of using mock data,
so that workflow operations persist and reflect actual system state.

#### Acceptance Criteria

1. **AC1**: `apiClient` in `lib/api-client.ts` is enhanced with comprehensive error handling and retry logic
2. **AC2**: Environment variables (`NEXT_PUBLIC_API_URL`) are properly configured for dev and production
3. **AC3**: Workflow creation, retrieval, and deletion operations use real backend endpoints
4. **AC4**: Health check endpoint is called on app initialization to verify backend connectivity
5. **AC5**: Failed API requests display user-friendly error messages (not raw error objects)
6. **AC6**: API client implements 3-retry logic with exponential backoff for failed requests
7. **AC7**: All API responses are properly typed using TypeScript interfaces
8. **AC8**: Loading states are displayed during all async API operations

#### Integration Verification

- **IV1**: Start backend server and confirm frontend health check succeeds
- **IV2**: Create a new workflow via API and verify it appears in backend state
- **IV3**: Simulate backend downtime and verify error handling displays user-friendly message
- **IV4**: Verify API retry logic attempts 3 retries before failing

---

### Story 1.3: WebSocket Integration for Real-Time Updates

As a **user**,
I want to receive real-time workflow status updates without refreshing the page,
so that I can see workflow progress as it happens.

#### Acceptance Criteria

1. **AC1**: WebSocket connection is established when a workflow is created or loaded
2. **AC2**: Real-time workflow status updates (step changes, completions, failures) are received via WebSocket
3. **AC3**: WebSocket messages update the `WorkflowContext` state triggering UI re-renders
4. **AC4**: WebSocket connection implements automatic reconnection with exponential backoff (max 30 seconds)
5. **AC5**: Connection status indicator shows "Connected" (green) or "Disconnected" (gray) in UI
6. **AC6**: WebSocket cleanup occurs when component unmounts or workflow changes
7. **AC7**: Failed WebSocket connections fall back to periodic polling (every 5 seconds)
8. **AC8**: WebSocket message parsing errors are logged and don't crash the application

#### Integration Verification

- **IV1**: Connect to backend and verify WebSocket establishes connection (check browser DevTools)
- **IV2**: Trigger workflow step change from backend and verify UI updates in real-time
- **IV3**: Simulate network interruption and verify automatic reconnection occurs
- **IV4**: Close backend WebSocket server and verify fallback to polling activates

---

### Story 1.4: Enhanced Chat Interface with Backend Integration

As a **user**,
I want to interact with the detector triage agent through a production-quality chat interface,
so that I can naturally describe my detector requirements and receive guided assistance.

#### Acceptance Criteria

1. **AC1**: Chat messages are sent to backend triage agent via `submitInput` API call
2. **AC2**: Agent responses are received via WebSocket and displayed in chat interface
3. **AC3**: Chat interface supports markdown rendering for formatted agent responses
4. **AC4**: Message history is maintained in component state and persists during workflow session
5. **AC5**: Chat input is disabled with loading spinner while waiting for agent response
6. **AC6**: Long agent responses are properly formatted with scrollable message area
7. **AC7**: Timestamps are displayed for each message in human-readable format
8. **AC8**: Chat history scrolls to bottom automatically when new messages arrive

#### Integration Verification

- **IV1**: Send chat message and verify it appears in backend workflow logs
- **IV2**: Trigger agent response from backend and verify it renders in UI with markdown formatting
- **IV3**: Send multiple rapid messages and verify UI handles queueing gracefully
- **IV4**: Verify chat history persists when navigating away and returning to workflow page

---

### Story 1.5: Workflow Step Components Integration

As a **user**,
I want all 9 workflow steps to display appropriate UI components connected to the backend,
so that I can complete the entire detector development workflow through the web interface.

#### Acceptance Criteria

1. **AC1**: ETW Input Form (`step 2`) submits data to backend and advances workflow
2. **AC2**: Code Review Approval (`step 4`) displays generated PR details and submits approval/rejection
3. **AC3**: Results Confirmation (`step 6`) displays detector results from backend and accepts user confirmation
4. **AC4**: Production Promotion Approval (`step 8`) shows promotion details and handles approval
5. **AC5**: WorkflowStepper component shows real-time step progress based on backend state
6. **AC6**: Each step displays loading state while backend processes executor
7. **AC7**: Step-specific errors are displayed with actionable error messages
8. **AC8**: Completed steps show success indicators; failed steps show error states

#### Integration Verification

- **IV1**: Complete entire workflow from step 1-9 and verify each step advances correctly
- **IV2**: Reject approval at step 4 and verify workflow handles rejection gracefully
- **IV3**: Trigger failure at step 3 (schema discovery) and verify error is displayed to user
- **IV4**: Verify WorkflowStepper visual state matches backend workflow state at each step

---

### Story 1.6: Session Persistence and Recovery

As a **user**,
I want my workflow session to persist when I refresh the page or close the browser,
so that I don't lose progress if my browser crashes or I navigate away accidentally.

#### Acceptance Criteria

1. **AC1**: Active workflow ID is saved to browser localStorage on workflow creation
2. **AC2**: Workflow state is restored from localStorage on page load if workflow ID exists
3. **AC3**: Backend API is queried to fetch latest workflow status on page restore
4. **AC4**: Chat message history is restored from backend data or localStorage
5. **AC5**: WorkflowStepper displays correct step based on restored state
6. **AC6**: Completed workflows are removed from localStorage after 24 hours
7. **AC7**: Failed workflows display restoration option with ability to start fresh
8. **AC8**: Multiple concurrent workflows are supported with session isolation

#### Integration Verification

- **IV1**: Create workflow, advance to step 3, refresh page, verify state restores correctly
- **IV2**: Create workflow, close browser, reopen, verify workflow can be resumed
- **IV3**: Create 3 workflows, verify each maintains isolated state in localStorage
- **IV4**: Complete workflow, wait 24 hours (or manipulate timestamp), verify cleanup occurs

---

### Story 1.7: Dashboard Landing Page

As a **user**,
I want a dashboard that shows all active workflows, system health, and workflow history,
so that I can monitor detector development activity and access past workflows.

#### Acceptance Criteria

1. **AC1**: Dashboard page (`/dashboard`) displays list of all workflows from backend API
2. **AC2**: Each workflow card shows: ID (truncated), status badge, current step, last updated timestamp
3. **AC3**: Workflows are filterable by status (all, running, completed, failed)
4. **AC4**: Clicking workflow card navigates to workflow detail view
5. **AC5**: System health panel shows: backend connection status, total workflows, active workflows
6. **AC6**: Dashboard auto-refreshes every 10 seconds to show latest data
7. **AC7**: "Create New Workflow" button navigates to `/workflow` page
8. **AC8**: Empty state message is displayed when no workflows exist

#### Integration Verification

- **IV1**: Call `/api/workflows` endpoint and verify dashboard displays all workflows
- **IV2**: Create new workflow and verify it appears in dashboard within 10 seconds
- **IV3**: Filter workflows by "completed" status and verify only completed workflows show
- **IV4**: Verify system health panel shows accurate connection status and workflow counts

---

### Story 1.8: Workflow History Detail View

As a **user**,
I want to view detailed information about completed workflows,
so that I can review past detector development sessions and access generated artifacts.

#### Acceptance Criteria

1. **AC1**: Workflow detail page (`/dashboard/workflow/[id]`) fetches workflow data from backend
2. **AC2**: Step-by-step execution timeline is displayed showing completion time for each step
3. **AC3**: Chat conversation history is displayed in chronological order
4. **AC4**: Generated PR links are displayed with click-through to Azure DevOps
5. **AC5**: ETW input data (providerGuid, ruleId) is displayed in summary section
6. **AC6**: Results analysis data from step 7 is formatted and displayed
7. **AC7**: Workflow status (completed/failed) is prominently displayed with status badge
8. **AC8**: "Back to Dashboard" button returns to dashboard page

#### Integration Verification

- **IV1**: Complete full workflow, navigate to detail view, verify all steps are shown
- **IV2**: Verify chat history matches actual conversation from workflow execution
- **IV3**: Click PR link and verify it opens correct Azure DevOps pull request
- **IV4**: View failed workflow detail and verify error information is displayed

---

### Story 1.9: ETW Provider Information Dashboard

As a **user**,
I want to view ETW provider information and active detectors in the dashboard,
so that I can understand what providers are being monitored and their current state.

#### Acceptance Criteria

1. **AC1**: Dashboard displays section for "Active Detectors" with provider GUID and rule ID
2. **AC2**: Active detectors are fetched from backend API endpoint
3. **AC3**: Each detector card shows: provider name, GUID, rule ID, deployment status, last updated
4. **AC4**: Detector cards are searchable/filterable by provider GUID or name
5. **AC5**: Clicking detector card shows detector details (source code link, results link)
6. **AC6**: Empty state is shown when no active detectors exist
7. **AC7**: Provider information is cached and refreshed every 30 seconds
8. **AC8**: Loading skeleton is displayed while fetching provider data

#### Integration Verification

- **IV1**: Backend provides `/api/detectors` endpoint with mock data for at least 3 detectors
- **IV2**: Verify dashboard displays all active detectors from backend
- **IV3**: Search for specific provider GUID and verify filtering works
- **IV4**: Complete workflow creating new detector, verify it appears in active detectors list

---

### Story 1.10: Error Handling and User Feedback

As a **user**,
I want clear, actionable error messages and loading indicators throughout the application,
so that I understand what's happening and what to do when problems occur.

#### Acceptance Criteria

1. **AC1**: All API errors display user-friendly messages (no raw stack traces shown to user)
2. **AC2**: Network errors show "Connection failed - please check your network" message
3. **AC3**: Backend unavailable shows "Backend service unavailable - please try again later"
4. **AC4**: Workflow step failures display specific error with retry option
5. **AC5**: All async operations show loading spinners or progress indicators
6. **AC6**: Error boundary catches React errors and displays fallback UI with "Report Issue" button
7. **AC7**: Toast notifications are used for non-critical feedback (workflow created, action completed)
8. **AC8**: Critical errors are logged to browser console (dev) and Application Insights (prod)

#### Integration Verification

- **IV1**: Stop backend server and verify user-friendly "service unavailable" message appears
- **IV2**: Trigger React component error and verify error boundary catches it with fallback UI
- **IV3**: Submit invalid ETW input data and verify validation error message is clear
- **IV4**: Check Application Insights logs in production for error tracking

---

### Story 1.11: Azure Deployment Configuration

As a **DevOps engineer**,
I want the frontend configured for Azure deployment with proper environment settings,
so that the application can be deployed to production and connect to the backend.

#### Acceptance Criteria

1. **AC1**: `next.config.ts` is configured for Azure Static Web Apps or App Service deployment
2. **AC2**: Environment variables are documented in README with examples
3. **AC3**: Production build (`npm run build`) completes successfully with zero errors
4. **AC4**: Azure deployment configuration files are created (if needed for Static Web Apps)
5. **AC5**: CORS configuration in backend allows production frontend domain
6. **AC6**: Application Insights integration is configured for production monitoring
7. **AC7**: Deployment documentation includes step-by-step Azure deployment guide
8. **AC8**: Health check on app startup verifies backend connectivity and displays status

#### Integration Verification

- **IV1**: Run production build locally with `npm run build && npm start`
- **IV2**: Deploy to Azure Static Web Apps staging environment and verify functionality
- **IV3**: Verify environment variables are correctly loaded from Azure App Settings
- **IV4**: Check Application Insights for successful telemetry data in production

---

