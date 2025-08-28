# Base image
FROM python:3.9.18-slim

# Set working directory
WORKDIR /app

# Install dependencies, AWS CLI, create user, clean up in one RUN
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip ca-certificates bash git && \
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && \
    unzip /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    rm -rf /tmp/aws /tmp/awscliv2.zip /var/lib/apt/lists/* && \
    useradd --system --create-home --shell /usr/sbin/nologin appuser

# Add AWS CLI to PATH
ENV PATH="/usr/local/bin:/usr/local/aws-cli/v2/current/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Expose port and switch to non-root user
EXPOSE 5000
USER appuser

# Run Flask app
ENTRYPOINT ["python", "app.py"]

