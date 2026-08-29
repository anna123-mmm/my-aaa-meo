FROM python:3.10-slim

# Cài đặt Google Chrome và các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy toàn bộ file code vào container
COPY . /app

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Mở cổng cho Streamlit
EXPOSE 8501

# Lệnh chạy ứng dụng
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]