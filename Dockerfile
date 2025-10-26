# Use a Python base image. We use python:3.11-slim for a smaller image size.
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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

# CRITICAL: COPY THE MODEL AND ASSET FILES
COPY best_agrosense_model.h5 .
COPY class_indices.json .
COPY recommendations.json .

# Copy the rest of the application code
COPY . .

# to prevent OOM Kill during model loading.
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV OMP_NUM_THREADS=1
ENV KMP_BLOCKTIME=0
ENV KMP_SETTINGS=1

# Expose the default Cloud Run port, though the CMD uses $PORT
EXPOSE 8080 

# Cloud Run injects PORT=8080 (by default). The Gunicorn bind command needs this variable.
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "--workers", "1", "--threads", "1", "--timeout", "300", "app:app"]