.PHONY: help dev dev-server dev-client install clean build

help:
	@echo "MAF Agents - Available Commands"
	@echo "================================"
	@echo "make dev          - Run both server and client in development mode"
	@echo "make dev-server   - Run only the API server"
	@echo "make dev-client   - Run only the frontend"
	@echo "make install      - Install all dependencies"
	@echo "make build        - Build the client for production"
	@echo "make clean        - Clean all build artifacts"
	@echo "make test         - Run all tests"

dev:
	@echo "🚀 Starting MAF Agents in development mode..."
	@npm run dev

dev-server:
	@echo "🐍 Starting API server..."
	@cd server && uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-client:
	@echo "⚛️  Starting Next.js client..."
	@cd client && npm run dev

install:
	@echo "📦 Installing all dependencies..."
	@npm install
	@cd client && npm install
	@cd server && uv sync --all-extras
	@echo "✅ All dependencies installed!"

build:
	@echo "🏗️  Building client for production..."
	@cd client && npm run build

clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf client/node_modules client/.next client/out
	@rm -rf server/.venv server/__pycache__ server/**/__pycache__
	@rm -rf node_modules
	@echo "✅ Cleaned!"

test:
	@echo "🧪 Running tests..."
	@cd server && uv run poe test
