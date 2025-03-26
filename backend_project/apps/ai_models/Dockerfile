# Use Python 3.11 as the base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    python3-distutils \
    python3-setuptools \
    libgl1 \
    libglib2.0-0 \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /app/

# Upgrade pip, setuptools, and wheel to the latest versions
RUN pip install --upgrade pip setuptools wheel

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the PYTHONPATH
ENV PYTHONPATH=/app

# Copy the rest of the application code
COPY . /app/

COPY best.pt /app/

# Expose the port for FastAPI
EXPOSE 8001

# Run the FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]