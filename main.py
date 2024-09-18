import os
import json
from flask import Flask, render_template, request, jsonify, Response
from scraper.scraper import WebScraper
from database.db import Database
from tasks import scrape_website
from celery.result import AsyncResult

app = Flask(__name__)

# Initialize database connection
db = Database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json['url']
    max_workers = request.json.get('max_workers', 5)
    auth = request.json.get('auth')
    preprocessing_options = request.json.get('preprocessing_options', {})
    
    # Start the Celery task
    task = scrape_website.delay(url, max_pages=200, ignore_robots=True, max_workers=max_workers, auth=auth, preprocessing_options=preprocessing_options)
    
    return jsonify({'status': 'task_started', 'task_id': task.id})

@app.route('/task_status/<task_id>')
def task_status(task_id):
    task = AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    return jsonify(response)

@app.route('/scrape_updates/<task_id>')
def scrape_updates(task_id):
    def generate():
        task = AsyncResult(task_id)
        while not task.ready():
            yield f"data: {json.dumps(task.info)}\n\n"
            time.sleep(1)
        yield f"data: {json.dumps({'status': 'completed', 'result': task.result})}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/show_content/<int:job_id>')
def show_content(job_id):
    content = db.get_content(job_id)
    if content:
        data = json.loads(content)
        return jsonify(data)
    else:
        return jsonify({'status': 'error', 'message': 'Content not found'}), 404

@app.route('/download/<int:job_id>')
def download(job_id):
    content = db.get_content(job_id)
    if content:
        if isinstance(content, str):
            data = json.loads(content)
        else:
            data = content
        
        formatted_content = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
        
        response = app.response_class(
            formatted_content,
            mimetype='application/json',
            content_type='application/json; charset=utf-8'
        )
        response.headers.set('Content-Disposition', f'attachment; filename=scraped_content_{job_id}.json')
        return response
    else:
        return jsonify({'status': 'error', 'message': 'Content not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
