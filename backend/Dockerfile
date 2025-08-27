# Base image
FROM python:3.9.18-slim

# Set working directory
WORKDIR /app

# Install dependencies: curl, unzip, certificates, Docker dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        unzip \
        ca-certificates \
        bash \
        git \
        iptables \
        gnupg \
        lsb-release \
        sudo \
        apt-transport-https \
        software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Docker (latest stable)
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
       > /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli docker-ce \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/aws /tmp/awscliv2.zip

# Add AWS CLI to PATH
ENV PATH="/usr/local/bin:/usr/local/aws-cli/v2/current/bin:$PATH"

# Create minimal user with home directory for Docker credentials
RUN useradd --system --create-home --shell /usr/sbin/nologin appuser

# Set Docker config directory to writable path
ENV DOCKER_CONFIG=/app/.docker
RUN mkdir -p /app/.docker && chown appuser:appuser /app/.docker

# Copy requirements and install Python dependencies
COPY --chown=appuser:appuser requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose Flask port
EXPOSE 5000

# Switch to minimal user
USER appuser

# Run the Flask app
ENTRYPOINT ["python", "app.py"]

