from flask import Flask, request, render_template, send_file, redirect, url_for
import yt_dlp as youtube_dl
import os
import shutil
from werkzeug.utils import secure_filename
import glob
import logging
from celery import Celery

app = Flask(__name__)

# Celery 구성
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@app.route('/')
def index():
    return render_template('index.html')

@celery.task(bind=True)
def download_video(self, url, format):
    temp_dir = '/tmp/temp_downloads'
    final_dir = 'downloads'

    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best' if format == 'mp4' else 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if format == 'mp3' else [],
            'ffmpeg_location': '/usr/bin/ffmpeg',
            'cachedir': False,
            'retries': 10,
            'proxy': 'socks5://your_proxy_address:your_proxy_port',  # 필요한 경우 프록시 설정
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            original_filename_pattern = os.path.join(temp_dir, f"{info_dict['title']}*")

            downloaded_files = glob.glob(original_filename_pattern)

            if not downloaded_files:
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {original_filename_pattern}")

            original_filename = downloaded_files[0]
            base_filename = os.path.splitext(original_filename)[0]
            final_name = secure_filename(f"{base_filename}.{format}")
            final_path = os.path.join(final_dir, final_name)

            if not os.path.exists(final_dir):
                os.makedirs(final_dir, exist_ok=True)
            shutil.move(original_filename, final_path)
        
        return final_path
    
    except Exception as e:
        logging.error(f"다운로드 오류: {str(e)}")
        self.update_state(state='FAILURE', meta={'exc_type': str(type(e)), 'exc_message': str(e)})
        raise e
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format = request.form['format']
    task = download_video.apply_async(args=[url, format])
    return redirect(url_for('status', task_id=task.id))

@app.route('/status/<task_id>')
def status(task_id):
    task = download_video.AsyncResult(task_id)
    if task.state == 'PENDING':
        return render_template('status.html', state=task.state)
    elif task.state == 'FAILURE':
        return render_template('error.html', message="다운로드에 실패했습니다.")
    elif task.state == 'SUCCESS':
        return redirect(url_for('download_file', filename=os.path.basename(task.result)))

@app.route('/download-file/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join('downloads', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            raise FileNotFoundError("파일을 찾을 수 없습니다.")
    
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
