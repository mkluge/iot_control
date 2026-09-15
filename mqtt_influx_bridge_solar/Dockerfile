FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bridge.py .

ENV PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/config/config.json

CMD ["python", "bridge.py"]
