import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from scraper.scraper import WebScraper
from database.db import Database
import tempfile

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
    
    try:
        scraper = WebScraper(url, max_pages=10, ignore_robots=True, max_workers=max_workers, auth=auth, preprocessing_options=preprocessing_options)
        content = scraper.scrape()
        data = json.loads(content)
        
        job_id = db.create_job(url)
        db.update_job_status(job_id, 'completed')
        db.save_content(job_id, content)
        
        formatted_content = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
        
        return jsonify({
            'status': 'completed',
            'job_id': job_id,
            'total_pages_attempted': data['total_pages_attempted'],
            'total_pages_scraped': data['total_pages_scraped'],
            'url_tree': data['url_tree'],
            'content': data['content'],
            'errors': data['errors'],
            'formatted_content': formatted_content
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/download/<int:job_id>')
def download(job_id):
    content = db.get_content(job_id)
    if content:
        if isinstance(content, str):
            data = json.loads(content)
        else:
            data = content
        
        formatted_content = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write(formatted_content)
        
        return send_file(temp_file.name, as_attachment=True, download_name=f'scraped_content_{job_id}.json')
    else:
        return jsonify({'status': 'error', 'message': 'Content not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
