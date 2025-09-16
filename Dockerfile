# Use slim Python base image
FROM python:3.10-slim

# Install system dependencies for Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port (Render sets PORT env var, we use 8000 by default)
EXPOSE 8000

# Start the app with Gunicorn
# ⚠ Replace "medical_analyzer:app" with "<filename>:<app_variable>" if your entry is different
CMD ["gunicorn", "medical_analyzer:app", "--bind", "0.0.0.0:8000"]