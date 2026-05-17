FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /models \
    && wget -q -O /models/en_US-ryan-high.onnx \
       "https://huggingface.co/rhasspy/piper-voices/resolve/main/rhasspy/en_US-ryan/2023-07-07/en_US-ryan-high.onnx" \
    && wget -q -O /models/en_US-ryan-high.onnx.json \
       "https://huggingface.co/rhasspy/piper-voices/resolve/main/rhasspy/en_US-ryan/2023-07-07/en_US-ryan-high.onnx.json"

RUN useradd -m -s /bin/bash piper
USER piper

HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
