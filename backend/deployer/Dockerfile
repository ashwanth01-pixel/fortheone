#!/opt/homebrew/bin/bash
FROM python:3.9-slim

WORKDIR /app

COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../deployer ./deployer
COPY ../deployer_frontend ./deployer_frontend

EXPOSE 5001

CMD ["python", "deployer/backend.py"]

