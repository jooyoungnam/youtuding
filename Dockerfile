FROM python:3.9-slim

# 시스템 패키지 업데이트 및 ffmpeg 설치
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 종속성 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade yt-dlp  # 최신 yt-dlp 설치

# 애플리케이션 코드 복사
COPY . .

# downloads 폴더에 쓰기 권한 부여
RUN mkdir -p downloads && chmod -R 777 downloads

# 포트 설정
EXPOSE 8000

# 애플리케이션 실행
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
