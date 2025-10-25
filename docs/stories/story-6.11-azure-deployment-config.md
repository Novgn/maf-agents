# Story 6.11: Azure Deployment Configuration

**Epic**: Epic 6: Production-Ready Next.js Frontend Integration

## User Story

As a **DevOps engineer**,
I want **the frontend configured for Azure deployment with proper environment settings**,
so that **the application can be deployed to production and connect to the backend**.

## Acceptance Criteria

1. **AC1**: `next.config.ts` is configured for Azure Static Web Apps or App Service deployment
2. **AC2**: Environment variables are documented in README with examples
3. **AC3**: Production build (`npm run build`) completes successfully with zero errors
4. **AC4**: Azure deployment configuration files are created (if needed for Static Web Apps)
5. **AC5**: CORS configuration in backend allows production frontend domain
6. **AC6**: Application Insights integration is configured for production monitoring
7. **AC7**: Deployment documentation includes step-by-step Azure deployment guide
8. **AC8**: Health check on app startup verifies backend connectivity and displays status

## Integration Verification

- **IV1**: Run production build locally with `npm run build && npm start`
- **IV2**: Deploy to Azure Static Web Apps staging environment and verify functionality
- **IV3**: Verify environment variables are correctly loaded from Azure App Settings
- **IV4**: Check Application Insights for successful telemetry data in production

## Technical Notes

### Next.js Configuration for Azure

```typescript
// client/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // For Azure App Service
  // OR
  // output: "export", // For Azure Static Web Apps (if static)

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
    NEXT_PUBLIC_APP_INSIGHTS_KEY: process.env.NEXT_PUBLIC_APP_INSIGHTS_KEY,
  },

  // Asset optimization
  compress: true,
  poweredByHeader: false,
};

export default nextConfig;
```

### Environment Variables

Create `.env.example`:

```bash
# Backend API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Azure Application Insights (optional)
NEXT_PUBLIC_APP_INSIGHTS_KEY=

# Production values (set in Azure App Settings)
# NEXT_PUBLIC_API_URL=https://maf-agents-api.azurewebsites.net
# NEXT_PUBLIC_WS_URL=wss://maf-agents-api.azurewebsites.net
```

### Azure Static Web Apps Configuration

Create `staticwebapp.config.json`:

```json
{
  "routes": [
    {
      "route": "/api/*",
      "allowedRoles": ["anonymous"]
    },
    {
      "route": "/*",
      "serve": "/index.html",
      "statusCode": 200
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/images/*.{png,jpg,gif}", "/css/*"]
  },
  "platform": {
    "apiRuntime": "node:18"
  }
}
```

### Application Insights Integration

```typescript
// client/src/lib/app-insights.ts
import { ApplicationInsights } from "@microsoft/applicationinsights-web";

let appInsights: ApplicationInsights | null = null;

export function initializeAppInsights() {
  const instrumentationKey = process.env.NEXT_PUBLIC_APP_INSIGHTS_KEY;

  if (!instrumentationKey || process.env.NODE_ENV !== "production") {
    console.log("Application Insights not initialized (dev mode or no key)");
    return;
  }

  appInsights = new ApplicationInsights({
    config: {
      instrumentationKey,
      enableAutoRouteTracking: true,
    },
  });

  appInsights.loadAppInsights();
  appInsights.trackPageView();
}

export function logErrorToAppInsights(error: Error, context?: any) {
  if (appInsights) {
    appInsights.trackException({ exception: error, properties: context });
  }
}
```

### Backend CORS Configuration

Update `server/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Dev
        "https://maf-agents.azurestaticapps.net",  # Production
        "https://your-custom-domain.com",  # Custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Deployment Documentation

Create `client/DEPLOYMENT.md` with:
1. Prerequisites (Azure subscription, Azure CLI)
2. Build and test locally
3. Deploy to Azure Static Web Apps via GitHub Actions
4. Configure environment variables in Azure Portal
5. Update backend CORS configuration
6. Test production deployment
7. Monitor with Application Insights

## Dependencies

- **Depends on**: All previous stories (6.1-6.10)

## Related Documents

- PRD: docs/prd.md (Story 1.11)
- Next.js Config: client/next.config.ts
- Deployment Guide: client/DEPLOYMENT.md (to be created)
- Azure Docs: https://learn.microsoft.com/azure/static-web-apps/
