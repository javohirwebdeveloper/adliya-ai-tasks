FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
# ffmpeg: Telegram ovozli xabarini (ogg/opus) va brauzer yozuvini (webm) 16 kHz ga o'tkazish uchun
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
COPY eval ./eval
COPY data/synonyms.csv data/categories.csv ./data/
# root emas; modellar /models da (HF_HOME), internetsiz muhitda shu papka oldindan to'ldiriladi
RUN useradd -m -u 10001 app && mkdir -p /models && chown app /models
ENV HF_HOME=/models
USER app
EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
