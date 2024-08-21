from flask import Flask, request, render_template, send_file, redirect, url_for, abort
import yt_dlp as youtube_dl
import os
import shutil
from werkzeug.utils import secure_filename
import glob
import logging

app = Flask(__name__)

# 로그를 콘솔에 출력
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    temp_dir = '/tmp/temp_downloads'
    final_dir = 'downloads'
    
    url = request.form['url']
    format = request.form['format']
    
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
            'retries': 5,  # 5번까지 자동 재시도
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
                'Origin': 'https://www.youtube.com',
            },
            'proxy': os.getenv('PROXY', None),  # 필요 시 환경 변수에서 프록시 설정
            'cookiefile': os.getenv('COOKIEFILE', None),  # 필요 시 환경 변수에서 쿠키 파일 설정
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
        
        logging.info(f"다운로드 완료: {final_path}")
        return redirect(url_for('download_file', filename=os.path.basename(final_path)))
    
    except Exception as e:
        logging.error(f"다운로드 오류: {str(e)}")
        return f"오류가 발생했습니다: {str(e)}", 500
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route('/download-file/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join('downloads', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            raise FileNotFoundError("파일을 찾을 수 없습니다.")
    
    except Exception as e:
        logging.error(f"파일 다운로드 오류: {str(e)}")
        return f"오류가 발생했습니다: {str(e)}", 500

@app.route('/back')
def back():
    return redirect(url_for('index'))

if __name__ == '__main__':
    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads', exist_ok=True)
        os.chmod('downloads', 0o777)
        app.run(debug=True)
    except Exception as e:
        logging.error(f"서버 시작 중 오류가 발생했습니다: {str(e)}")
        print(f"서버 시작 중 오류가 발생했습니다: {str(e)}")
