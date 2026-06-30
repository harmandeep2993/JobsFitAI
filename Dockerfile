FROM python:3.12-slim

RUN pip install uv --no-cache-dir

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen --no-dev

COPY backend/ ./backend/
COPY templates/ ./templates/
COPY assets/ ./assets/

RUN mkdir -p backend/data backend/resumes backend/logs

EXPOSE 8080

WORKDIR /app/backend
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
