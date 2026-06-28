FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e . 2>/dev/null || pip install --no-cache-dir pytest
COPY src/ src/
COPY tests/ tests/
EXPOSE 8000
CMD ["python", "-m", "prometheus_ultra.services.server"]
