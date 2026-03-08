FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        curl \
        wget \
        procps \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (avoids ~3GB CUDA packages)
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

WORKDIR /workspaces/ChessieBot