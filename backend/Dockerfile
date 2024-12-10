FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create a new user
RUN adduser --disabled-password celeryuser

# Switch to the non-root user
USER celeryuser

# Copy project files
COPY . /app/
