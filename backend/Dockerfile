# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies for AWS CLI and unzip tools
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    groff \
    less \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && ln -sf /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws \
    && rm -rf aws awscliv2.zip

# Ensure AWS CLI is in PATH
ENV PATH="/usr/local/bin:/usr/local/aws-cli/v2/current/bin:${PATH}"

# Copy app files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start app
CMD ["python", "app.py"]
