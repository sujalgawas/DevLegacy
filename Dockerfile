FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    cloc git \
    build-essential \
    cmake \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

COPY backend/requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

#RUN pip install -r requirements.txt

COPY backend/ .

EXPOSE 8082

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]