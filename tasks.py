from celery import Celery
import yt_dlp as youtube_dl
import logging
import os

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis 브로커 URL 설정
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', '6379')
celery = Celery('tasks', broker=f'redis://{redis_host}:{redis_port}/0', backend=f'redis://{redis_host}:{redis_port}/0')

@celery.task(bind=True)
def download_video(self, url, format):
    logger.info("비디오 다운로드 작업이 시작되었습니다. URL: %s, Format: %s", url, format)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if format == 'mp4' else 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format == 'mp3' else [],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logger.info("비디오 다운로드가 완료되었습니다. URL: %s", url)
        return "Download complete!"
    except Exception as e:
        logger.error("다운로드 오류: %s", str(e))
        self.update_state(state='FAILURE', meta={'exc_type': str(type(e)), 'exc_message': str(e)})
        raise e
