FROM python:3.9-slim

WORKDIR /app

# Copy only necessary files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY . .

# Expose the port
EXPOSE 5001

# Run in foreground
CMD ["python", "app.py"]

