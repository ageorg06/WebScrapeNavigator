import os
import json
from flask import Flask, render_template, request, jsonify
from scraper.scraper import WebScraper
from database.db import Database

app = Flask(__name__)

# Initialize database connection
db = Database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json['url']
    scraper = WebScraper(url, max_pages=10, ignore_robots=True)
    job_id = db.create_job(url)
    
    try:
        content = scraper.scrape()
        data = json.loads(content)
        db.update_job_status(job_id, 'completed')
        db.save_content(job_id, content)
        return jsonify({
            'status': 'success',
            'job_id': job_id,
            'start_url': data['start_url'],
            'total_pages_attempted': data['total_pages_attempted'],
            'total_pages_scraped': data['total_pages_scraped'],
            'content': data['content'][:1],  # Return only the first page for display
            'errors': data['errors'],
            'skipped_urls': data['skipped_urls']
        })
    except Exception as e:
        db.update_job_status(job_id, 'failed')
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
        data = json.loads(content)
        response = jsonify(data)
        response.headers.set('Content-Disposition', f'attachment; filename=scraped_content_{job_id}.json')
        return response
    else:
        return jsonify({'status': 'error', 'message': 'Content not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
