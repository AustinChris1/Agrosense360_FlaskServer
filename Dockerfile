# Use a Python base image. We use python:3.11-slim for a smaller image size.
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install necessary system dependencies
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
RUN if [ -f "requirements.txt" ]; then \
        echo "✅ requirements.txt found, installing dependencies..."; \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "❌ ERROR: requirements.txt not found. Build cannot continue."; \
        exit 1; \
    fi

# ✅ Download model directly from Google Drive
RUN echo "⬇️ Downloading model from Google Drive..." && \
    FILE_ID=1xkvaONSV_Y5i4uts6qWYxesaf5LAH7Ll && \
    FILE_NAME=best_agrosense_model.h5 && \
    wget --no-check-certificate "https://drive.google.com/uc?export=download&id=${FILE_ID}" -O ${FILE_NAME} && \
    if [ -s "${FILE_NAME}" ]; then \
        echo "✅ Model download complete: ${FILE_NAME}"; \
    else \
        echo "❌ ERROR: Model file failed to download or is empty!"; \
        exit 1; \
    fi

# Copy your other asset files with safety checks
COPY class_indices.json ./
RUN if [ -f "class_indices.json" ]; then \
        echo "✅ class_indices.json copied successfully."; \
    else \
        echo "⚠️ WARNING: class_indices.json missing in build context."; \
    fi

COPY recommendations.json ./
RUN if [ -f "recommendations.json" ]; then \
        echo "✅ recommendations.json copied successfully."; \
    else \
        echo "⚠️ WARNING: recommendations.json missing in build context."; \
    fi


# Recommended TensorFlow environment variables for stability on limited resources
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV OMP_NUM_THREADS=1
ENV KMP_BLOCKTIME=0
ENV KMP_SETTINGS=1

# Copy the main app code
COPY . .
RUN if [ -f "app.py" ]; then \
        echo "✅ app.py found and copied successfully."; \
    else \
        echo "❌ ERROR: app.py not found in build context. Build cannot continue."; \
        exit 1; \
    fi

# ✅ Set environment variable Cloud Run expects
ENV FLASK_APP=app.py
ENV PORT=8080

# Expose the port Cloud Run will use
EXPOSE 8080

# ✅ Use the dynamic Cloud Run port
CMD ["sh", "-c", "flask run --host=0.0.0.0 --port=$PORT"]