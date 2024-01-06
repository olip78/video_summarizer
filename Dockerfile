FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl && \
    apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/src/app/
RUN mkdir -p /usr/src/app/runtimes

COPY ./requirements.txt /usr/src/app/
WORKDIR /usr/src/app/
RUN pip install --no-cache-dir -v -r requirements.txt

COPY ./src/ /usr/src/app/src
COPY ./app.py/ /usr/src/app/app.py

EXPOSE 8501

HEALTHCHECK --interval=15s --retries=2 \
  CMD curl -f http://0.0.0.0:8501/healthz

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]