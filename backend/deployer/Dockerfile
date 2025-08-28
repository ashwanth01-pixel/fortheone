# Use Python slim base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy deployer code and requirements
COPY . .

# Install Python dependencies in a single RUN
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend if your context allows it (see note)
# COPY ../deployer_frontend ./deployer_frontend

# Expose Flask port
EXPOSE 5001

# Run the Flask deployer
ENTRYPOINT ["python", "backend.py"]

