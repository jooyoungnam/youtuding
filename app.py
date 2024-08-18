from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import yt_dlp as youtube_dl
import os

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
        'ffmpeg_location': '/usr/bin/ffmpeg',  # 서버에서 ffmpeg 경로
        'cookiefile': '/path/to/cookies.txt',  # 쿠키 파일 경로
        'no-cache-dir': True,  # 캐시 비활성화
        'restrictfilenames': True  # 파일 이름에서 특수 문자 제거
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        file_name = ydl.prepare_filename(info_dict).replace('.webm', f'.{format}').replace('.m4a', f'.{format}')
    
    return redirect(url_for('ad', file=os.path.basename(file_name)))

@app.route('/ad')
def ad():
    file_name = request.args.get('file')
    return render_template('ad.html', file=file_name)

@app.route('/download-file/<filename>')
def download_file(filename):
    return send_from_directory('downloads', filename, as_attachment=True)

@app.route('/back')
def back():
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(debug=True)
