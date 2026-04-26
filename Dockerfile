# 直接使用微软官方打包好所有底层依赖的 Playwright 镜像
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# 安装中文字体，防止二维码出现方块乱码
RUN apt-get update && apt-get install -y fonts-wqy-zenhei && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 双重保险：强制下载并校验 Chromium 内核
RUN playwright install chromium

COPY . .

EXPOSE 3666
CMD ["python", "-u", "app.py"]
