FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
RUN pip install "fastapi>=0.115" "uvicorn>=0.30"
COPY shield ./shield
COPY app.py page.html namunalar.json rag_namunalar.json ./
COPY static ./static
RUN useradd -m -u 10001 app
USER app
EXPOSE 8000
# matn jurnalga yozilmasin: so'rov jurnali o'chiq
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
