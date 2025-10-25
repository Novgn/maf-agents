# Quick Start Guide

## One-Line Start

```bash
npm run dev
```

That's it! Both servers will start:
- 🐍 Backend: http://localhost:8000
- ⚛️  Frontend: http://localhost:3000

---

## First Time Setup

### 1. Install Dependencies

```bash
npm run install:all
```

### 2. Configure Environment

```bash
# Server
cd server && cp .env.example .env
# Edit .env with your Azure credentials

# Client
cd ../client
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
```

### 3. Run

```bash
cd ..  # Back to root
npm run dev
```

---

## Common Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Run both servers |
| `npm run dev:server` | Run only backend |
| `npm run dev:client` | Run only frontend |
| `make dev` | Run both (alternative) |
| `make help` | Show all make commands |

---

## Troubleshooting

### Port Already in Use

**Backend (8000):**
```bash
lsof -ti:8000 | xargs kill -9
```

**Frontend (3000):**
```bash
lsof -ti:3000 | xargs kill -9
```

### Dependencies Not Installing

```bash
# Clean and reinstall
npm run clean
npm run install:all
```

### WebSocket Not Connecting

Check that both servers are running and `.env.local` has correct URLs.

---

## Next Steps

1. Visit http://localhost:3000/workflow
2. Click "Start New Workflow"
3. Follow the conversational prompts

## Documentation

- **Full Setup**: [README_MONOREPO.md](./README_MONOREPO.md)
- **Backend Docs**: [server/README.md](./server/README.md)
- **Frontend Docs**: [client/README.md](./client/README.md)
- **API Docs**: http://localhost:8000/docs (when running)
