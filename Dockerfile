# Basic Dockerfile for PetPlantr backend (development/quick build)
# Usage: docker build -t petplantr-basic .

FROM python:3.11-slim

# Set working dir
WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
