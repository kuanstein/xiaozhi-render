FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git libopus0 ffmpeg build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN git clone --depth 1 https://github.com/xinnan-tech/xiaozhi-esp32-server.git .
ENV PYTHONUNBUFFERED=1
RUN cd main/xiaozhi-server && grep -vE '^(vosk|torch|torchaudio|funasr|transformers|silero_vad|#)' requirements.txt | grep -v '^$' > /tmp/req.txt \
 && pip install --no-cache-dir -r /tmp/req.txt onnxruntime \
 && pip install --no-cache-dir --no-deps silero_vad==6.2.3
COPY proxy.py start.sh /app/
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
