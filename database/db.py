import os
import psycopg2
import json

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )
        self._create_tables()

    def _create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scrape_jobs (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scrape_content (
                    job_id INTEGER PRIMARY KEY REFERENCES scrape_jobs(id),
                    content JSONB NOT NULL
                )
            """)
        self.conn.commit()

    def reconnect(self):
        try:
            self.conn.close()
        except:
            pass
        self.conn = psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )

    def create_job(self, url):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.conn.cursor() as cur:
                    cur.execute("INSERT INTO scrape_jobs (url, status) VALUES (%s, %s) RETURNING id", (url, 'in_progress'))
                    job_id = cur.fetchone()[0]
                self.conn.commit()
                return job_id
            except psycopg2.OperationalError as e:
                if attempt < max_retries - 1:
                    print(f"Database connection failed. Attempting to reconnect... (Attempt {attempt + 1}/{max_retries})")
                    self.reconnect()
                else:
                    raise e

    def update_job_status(self, job_id, status):
        with self.conn.cursor() as cur:
            cur.execute("UPDATE scrape_jobs SET status = %s WHERE id = %s", (status, job_id))
        self.conn.commit()

    def get_job_status(self, job_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT status FROM scrape_jobs WHERE id = %s", (job_id,))
            result = cur.fetchone()
        return result[0] if result else None

    def save_content(self, job_id, content):
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO scrape_content (job_id, content) VALUES (%s, %s)", (job_id, content))
        self.conn.commit()

    def get_content(self, job_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT content FROM scrape_content WHERE job_id = %s", (job_id,))
            result = cur.fetchone()
        return result[0] if result else None
