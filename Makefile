.PHONY: dev-backend dev-frontend build install

# Run the FastAPI backend with hot-reload
dev-backend:
	cd backend && uv run uvicorn main:app --reload --port 8080

# Run the Vite dev server (proxies /api to localhost:8080)
dev-frontend:
	cd frontend && npm run dev

# Build the React app into frontend/dist/ (served by FastAPI in production)
build:
	cd frontend && npm run build

# Install all dependencies for both apps
install:
	cd backend && uv sync
	cd frontend && npm install
