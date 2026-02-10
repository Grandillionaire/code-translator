FROM python:3.11-slim

LABEL maintainer="Code Translator Team"
LABEL description="GitHub Action for Code Translation"

# Install dependencies
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY github-action/entrypoint.py ./entrypoint.py

# Set entrypoint
ENTRYPOINT ["python", "/app/entrypoint.py"]
