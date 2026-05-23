FROM python:3.13-slim

WORKDIR /app

RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python - <<'PY'
import urllib.request, sys
try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=5)
    sys.exit(0 if response.status == 200 else 1)
except Exception:
    sys.exit(1)
PY

CMD ["uvicorn", "task_api:app", "--host", "0.0.0.0", "--port", "8000"]
