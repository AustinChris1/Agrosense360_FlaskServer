# Use a Python base image. We use python:3.11-slim for a smaller image size.
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# The MODEL_DRIVE_ID ARG is removed. The model must be present locally.

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

# CRITICAL: COPY THE MODEL FILE (It must be in your Git repository and local directory)
COPY best_agrosense_model.h5 .
COPY class_indices.json .
COPY recommendations.json .
COPY firebase_service_account.json .

# Copy the rest of the application code
COPY . .

# to prevent OOM Kill during model loading.
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV OMP_NUM_THREADS=1
ENV KMP_BLOCKTIME=0
ENV KMP_SETTINGS=1

# Flask applications typically run on port 3000
EXPOSE 3000

# GUNICORN CONFIG: Workers=1, Timeout=300s. 
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "1", "--timeout", "300", "app:app"]
