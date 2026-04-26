FROM python:3.11-slim

# Create a non-root user
RUN useradd -m -r appuser

WORKDIR /app

# Copy requirements.txt first for Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Change ownership of the /app directory
RUN chown -R appuser:appuser /app

# Switch to the non-root user for security
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
