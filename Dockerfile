FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps required by opencv, pillow, tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtiff5-dev libjpeg62-turbo-dev libpng-dev \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# copy project
COPY . /app

# install python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

# runtime env
ENV TESSERACT_CMD=tesseract

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]