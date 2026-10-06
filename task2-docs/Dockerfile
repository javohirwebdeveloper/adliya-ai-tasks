FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# Tesseract OCR va o'zbek (lotin, kirill), rus til modellari: hammasi konteyner ichida, internetsiz ishlaydi
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-uzb tesseract-ocr-uzb-cyrl tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
COPY eval ./eval
COPY samples ./samples
# root emas: yuklangan PDF ni tahlil qiluvchi jarayon cheklangan huquqda ishlaydi
RUN useradd -m -u 10001 app
USER app
EXPOSE 8000
CMD ["uvicorn", "app.web:app", "--host", "0.0.0.0", "--port", "8000"]
