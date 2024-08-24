from flask import Flask, request, render_template, redirect, url_for, flash
from celery import Celery
import logging
import redis
import os
from tasks import download_video

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Redis URL 설정
redis_host = os.getenv('REDIS_HOST', 'svc.sel4.cloudtype.app')
redis_port = os.getenv('REDIS_PORT', 30309)
app.config['CELERY_BROKER_URL'] = f'redis://{redis_host}:{redis_port}/0'
app.config['CELERY_RESULT_BACKEND'] = f'redis://{redis_host}:{redis_port}/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis 연결 테스트
try:
    r = redis.StrictRedis(host=redis_host, port=int(redis_port), db=0)
    r.ping()
    logger.info("Redis 연결 성공")
except redis.ConnectionError as e:
    logger.error("Redis 연결 실패: %s", e)
except Exception as e:
    logger.error("Redis 연결 중 알 수 없는 오류 발생: %s", e)

@app.route('/')
def index():
    logger.info("Index 페이지 접근")
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format = request.form['format']
    
    logger.info("다운로드 요청 수신됨. URL: %s, Format: %s", url, format)
    
    try:
        task = download_video.apply_async(args=[url, format])
        logger.info("비디오 다운로드 작업이 Celery에 제출됨. Task ID: %s", task.id)
        return redirect(url_for('status', task_id=task.id))
    except Exception as e:
        logger.error("작업 시작 실패: %s", e)
        flash('다운로드 작업을 시작하는 데 실패했습니다.', 'danger')
        return redirect(url_for('index'))

@app.route('/status/<task_id>')
def status(task_id):
    logger.info("상태 확인 요청 수신됨. Task ID: %s", task_id)
    task = download_video.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
        logger.info("Task 상태: PENDING")
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
            'result': task.info.get('result', '')
        }
        logger.info("Task 상태: %s, 상태 메시지: %s", task.state, task.info.get('status', ''))
        if task.state == 'SUCCESS':
            flash('다운로드가 완료되었습니다!', 'success')
            logger.info("다운로드 완료됨. Task ID: %s", task_id)
    else:
        response = {
            'state': task.state,
            'status': str(task.info),
        }
        logger.error("Task 실패. Task ID: %s, 오류: %s", task_id, str(task.info))
        flash('다운로드에 실패했습니다.', 'danger')
    return render_template('status.html', response=response)

if __name__ == '__main__':
    app.run(debug=True)
