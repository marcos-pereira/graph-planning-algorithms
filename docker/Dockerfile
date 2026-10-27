FROM python:3.12-slim

LABEL maintainer="marcos-pereira"
LABEL description="Graph planning algorithms (BFS on grid maps)"

# Shared library required by the OpenCV wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install Python dependencies (baked into the image; code is mounted at runtime)
COPY scripts/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py", "maps/simplemaze.png", "418", "0", "610", "861"]
