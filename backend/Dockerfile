FROM python:3.9-slim

WORKDIR /app

# Install dependencies for AWS CLI
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
    && rm -rf aws awscliv2.zip

# Add AWS CLI to PATH for all environments
ENV PATH="/usr/local/bin:/usr/local/aws-cli/v2/current/bin:$PATH"

# Copy app files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "mainapp.py"]
