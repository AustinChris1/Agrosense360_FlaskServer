FROM python:3.12-slim-trixie

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    libgl1 \
    libgomp1 \
    libsm6 \
    libxext6 \
    curl \
    libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

ADD . .
RUN uv sync --locked

# # to prevent OOM Kill during model loading.
# ENV TF_ENABLE_ONEDNN_OPTS=0
# ENV OMP_NUM_THREADS=1
# ENV KMP_BLOCKTIME=0
# ENV KMP_SETTINGS=1

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "1", "--timeout", "300", "wsgi:app"]
