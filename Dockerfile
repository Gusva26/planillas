# Stage 1: Compilación de Frontend Moderno (React + Vite)
FROM node:22-slim AS frontend-builder
WORKDIR /build
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Servidor de Producción Backend (FastAPI + cafae)
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock && useradd --create-home cafae
COPY cafae ./cafae
COPY app.py .
COPY assets ./assets
# Frontend compilado listo para servir
COPY --from=frontend-builder /build/dist ./static
USER cafae
EXPOSE 8501
CMD ["uvicorn", "cafae.api.main:app", "--host", "0.0.0.0", "--port", "8501"]


