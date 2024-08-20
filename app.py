from flask import Flask, request, render_template, send_file, redirect, url_for
import yt_dlp as youtube_dl
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format = request.form['format']
    
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
        original_filename = ydl.prepare_filename(info_dict)  # 원본 파일명 (확장자가 포함됨)
        base_filename = os.path.splitext(original_filename)[0]  # 확장자를 제외한 파일명
        final_name = secure_filename(f"{base_filename}.{format}")  # 최종 파일명과 확장자
        
        # 파일이 실제로 존재하는지 확인
        if os.path.exists(original_filename):
            os.rename(original_filename, final_name)  # 다운로드된 파일을 확장자에 맞게 이름 변경
        else:
            return f"파일을 찾을 수 없습니다: {original_filename}", 404
    
    return redirect(url_for('download_file', filename=os.path.basename(final_name)))

@app.route('/download-file/<filename>')
def download_file(filename):
    file_path = os.path.join('downloads', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

@app.route('/back')
def back():
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(debug=True)
