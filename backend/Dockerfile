# Base image
FROM python:3.9.18-slim

# Set working directory
WORKDIR /app

# Install basic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        unzip \
        ca-certificates \
        bash \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/aws /tmp/awscliv2.zip

# Add AWS CLI to PATH
ENV PATH="/usr/local/bin:/usr/local/aws-cli/v2/current/bin:$PATH"

# Create non-root user
RUN useradd --system --create-home --shell /usr/sbin/nologin appuser

# Copy requirements and install Python deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . /app

# Env vars
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose Flask port
EXPOSE 5000

# Switch user
USER appuser

# Run Flask app
ENTRYPOINT ["python", "app.py"]

