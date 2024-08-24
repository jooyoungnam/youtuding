from flask import Flask, request, render_template, redirect, url_for, flash
from celery import Celery
import logging
import redis
from tasks import download_video

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 플래시 메시지에 필요

# Celery 설정
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Redis 연결 확인 및 로그 출력
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    logging.info("Redis 연결 성공")
except redis.ConnectionError as e:
    logging.error(f"Redis 연결 실패: {e}")

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format = request.form['format']
    
    logger.info("다운로드 작업이 시작되었습니다. URL: %s, Format: %s", url, format)
    
    try:
        task = download_video.apply_async(args=[url, format])
        return redirect(url_for('status', task_id=task.id))
    except Exception as e:
        logger.error(f"작업 시작 실패: {e}")
        flash('다운로드 작업을 시작하는데 실패했습니다.', 'danger')
        return redirect(url_for('index'))

@app.route('/status/<task_id>')
def status(task_id):
    task = download_video.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
            'result': task.info.get('result', '')
        }
        if task.state == 'SUCCESS':
            flash('다운로드가 완료되었습니다!', 'success')
    else:
        response = {
            'state': task.state,
            'status': str(task.info),
        }
        flash('다운로드에 실패했습니다.', 'danger')
    return render_template('status.html', response=response)

if __name__ == '__main__':
    app.run(debug=True)
