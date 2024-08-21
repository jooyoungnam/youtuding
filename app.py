from flask import Flask, request, render_template, send_file, redirect, url_for, abort
import yt_dlp as youtube_dl
import os
import shutil
from werkzeug.utils import secure_filename
import glob
import logging

app = Flask(__name__)

# 로그 파일 설정
logging.basicConfig(filename='download.log', level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    # /tmp 디렉토리 사용 (서버에 따라 경로를 설정할 수 있음)
    temp_dir = '/tmp/temp_downloads'
    final_dir = 'downloads'
    
    # 'url'과 'format' 변수를 폼에서 가져옴
    url = request.form['url']
    format = request.form['format']
    
    try:
        # 임시 디렉토리 생성 (필요 시)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
        
        # yt-dlp 옵션 설정
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
            'retries': 5,  # 다운로드 실패 시 5번까지 자동 재시도
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
                'Origin': 'https://www.youtube.com',
            },
            # 'proxy': 'http://your_proxy_here',  # 필요 시 프록시 설정
            # 'cookiefile': '/path/to/your/cookies.txt'  # 필요 시 쿠키 파일 설정
        }
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            original_filename_pattern = os.path.join(temp_dir, f"{info_dict['title']}*")
            
            # 파일 패턴으로 파일 찾기
            downloaded_files = glob.glob(original_filename_pattern)
            
            if not downloaded_files:
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {original_filename_pattern}")
            
            original_filename = downloaded_files[0]
            base_filename = os.path.splitext(original_filename)[0]
            final_name = secure_filename(f"{base_filename}.{format}")
            final_path = os.path.join(final_dir, final_name)
            
            # 최종 경로로 파일 이동
            if not os.path.exists(final_dir):
                os.makedirs(final_dir, exist_ok=True)
            shutil.move(original_filename, final_path)
        
        logging.info(f"다운로드 완료: {final_path}")
        return redirect(url_for('download_file', filename=os.path.basename(final_path)))
    
    except Exception as e:
        logging.error(f"다운로드 오류: {str(e)}")
        return f"오류가 발생했습니다: {str(e)}", 500
    
    finally:
        # 임시 디렉토리 정리
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
