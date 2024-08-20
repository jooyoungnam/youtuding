from flask import Flask, request, render_template, send_file, redirect, url_for, abort
import yt_dlp as youtube_dl
import os
import shutil
from werkzeug.utils import secure_filename
import glob

app = Flask(__name__)

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
        
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best' if format == 'mp4' else 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if format == 'mp3' else [],
            'ffmpeg_location': '/usr/bin/ffmpeg',
            'cachedir': False
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
        
        return redirect(url_for('download_file', filename=os.path.basename(final_path)))
    
    except PermissionError:
        # 권한 문제가 발생할 경우 /tmp 디렉토리를 기본 경로로 사용
        abort(500, description="디렉토리 권한 문제로 다운로드가 실패했습니다.")
    
    except Exception as e:
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
        print(f"서버 시작 중 오류가 발생했습니다: {str(e)}")
