FROM python:3.10-slim

# Cài đặt các thư viện hệ thống và Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/googlechrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/googlechrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy toàn bộ source code vào container
COPY . /app

# Cài đặt các package Python
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

# Chạy ứng dụng Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]