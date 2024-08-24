FROM python:3.9-slim

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 패키지 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 서버 시작 스크립트 작성
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:8000 app:app & celery -A tasks worker --loglevel=info"]
