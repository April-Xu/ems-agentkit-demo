FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    EMS_FIXTURE_DIR=/app/data/feishu \
    EMS_DEMO_STATE_DB=/tmp/ems-agentkit-demo.sqlite3

WORKDIR /app
COPY services/ems-governance/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY services/ems-governance/server.py /app/server.py
COPY data/feishu /app/data/feishu
EXPOSE 8000
CMD ["python", "/app/server.py"]
