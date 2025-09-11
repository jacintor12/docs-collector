# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app
# Install system dependencies for SQLite
RUN apt-get update && apt-get install -y libsqlite3-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (adjust if your app uses a different port)
EXPOSE 5000

# Run the app
CMD ["python", "run.py"]
