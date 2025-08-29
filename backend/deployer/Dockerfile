FROM python:3.11-slim

WORKDIR /app

# Copy deployer folder as /app/deployer
COPY ./ /app/deployer

# Install dependencies if any
RUN pip install --no-cache-dir -r /app/deployer/requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 5001

# Run the app
CMD ["python", "/app/deployer/app.py"]

