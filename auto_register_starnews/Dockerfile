FROM python:3.10-slim

# Cài đặt đầy đủ các thư viện hệ thống Linux, Chromium và ChromeDriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Expose port mặc định của Streamlit
EXPOSE 8501

# Lệnh chạy ứng dụng
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]