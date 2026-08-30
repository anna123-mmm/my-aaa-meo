FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8501
EXPOSE 8501

# Lấy cổng $PORT tự động của Railway và chạy app.py
CMD ["sh", "-c", "xvfb-run --auto-servernum streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]