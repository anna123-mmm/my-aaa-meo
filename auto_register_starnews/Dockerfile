FROM python:3.10-slim

# 1. Cài đặt Chromium, ChromeDriver và các thư viện hệ thống
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Tạo và phân quyền cho thư mục Socket màn hình ảo X11
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# 3. Lệnh khởi chạy Xvfb kèm cờ vô hiệu hóa truy cập (-ac) giúp Xvfb khởi tạo ổn định
CMD ["sh", "-c", "xvfb-run --auto-servernum --server-args='-ac -screen 0 1920x1080x24' streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]