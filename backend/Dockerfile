# Use a specific minimal Python image
FROM python:3.9.18-slim

# Set working directory
WORKDIR /app

# Install only necessary dependencies for AWS CLI
RUN useradd --system --no-create-home --shell /usr/sbin/nologin appuser \
        && apt-get update && apt-get install -y --no-install-recommends \
        curl \
        unzip \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/* \
        && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" \
        && unzip /tmp/awscliv2.zip -d /tmp \
        && /tmp/aws/install \
        && rm -rf /tmp/aws /tmp/awscliv2.zip

# Add AWS CLI to PATH
ENV PATH="/usr/local/bin:/usr/local/aws-cli/v2/current/bin:$PATH"

# Copy only necessary files
COPY --chown=appuser:appuser requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose Flask port
EXPOSE 5000

# Switch to the minimal user
USER appuser

# Run the app
ENTRYPOINT ["python", "app.py"]

