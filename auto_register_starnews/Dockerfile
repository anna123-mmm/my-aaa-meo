FROM python:3.10-slim

# Cài đặt Chromium, ChromeDriver và các thư viện cần thiết (Đã loại bỏ libgconf-2-4)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Chạy Xvfb giả lập màn hình và khởi chạy ứng dụng Streamlit
CMD ["sh", "-c", "xvfb-run --server-args='-screen 0 1920x1080x24' streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]