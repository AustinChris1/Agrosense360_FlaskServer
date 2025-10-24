# Use a Python base image. We use python:3.11-slim for a smaller image size.
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# 1. DEFINE THE BUILD ARGUMENT for the Google Drive ID
ARG MODEL_DRIVE_ID="1xkvaONSV_Y5i4uts6qWYxesaf5LAH7Ll"

# Install necessary system dependencies (including wget for model download)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    libgl1 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies first.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. DOWNLOAD THE MODEL FILE
RUN echo "Downloading model..." && \
    wget --no-check-certificate \
    "https://docs.google.com/uc?export=download&id=${MODEL_DRIVE_ID}" \
    -O "best_agrosense_model.h5" && \
    echo "Model download complete."

# Copy the rest of the application code, excluding the model file (assuming you have a good .dockerignore)
COPY . .

# Flask applications typically run on port 3000
EXPOSE 3000

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "app:app"]
