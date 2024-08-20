import os
import yt_dlp as youtube_dl
from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import glob

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format = request.form['format']
    
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best' if format == 'mp4' else 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if format == 'mp3' else [],
            'ffmpeg_location': '/usr/bin/ffmpeg',
            'cachedir': False  # 캐시를 비활성화하여 권한 문제를 피합니다
        }
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            original_filename_pattern = os.path.join('downloads', f"{info_dict['title']}*")
            
            # 파일 패턴으로 파일 찾기
            downloaded_files = glob.glob(original_filename_pattern)
            
            if not downloaded_files:
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {original_filename_pattern}")
            
            original_filename = downloaded_files[0]
            base_filename = os.path.splitext(original_filename)[0]  # 확장자를 제외한 파일명
            final_name = secure_filename(f"{base_filename}.{format}")  # 최종 파일명과 확장자
            
            # 파일 권한 설정
            os.chmod(original_filename, 0o666)  # 읽기 및 쓰기 권한 설정
            os.rename(original_filename, final_name)  # 다운로드된 파일을 확장자에 맞게 이름 변경
        
        return redirect(url_for('download_file', filename=os.path.basename(final_name)))
    
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}", 500

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

@app.route('/back')
def back():
    return redirect(url_for('index'))

if __name__ == '__main__':
    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads', exist_ok=True)
        os.chmod('downloads', 0o777)  # downloads 디렉토리에 모든 권한 부여
        app.run(debug=True)
    except Exception as e:
        print(f"서버 시작 중 오류가 발생했습니다: {str(e)}")
