from flask import Flask, request, jsonify
import psycopg2
import os
from urllib.parse import urlparse

app = Flask(__name__)


# ------------------------
#  Подключение к базе данных
# ------------------------
def get_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        return None

    url = urlparse(DATABASE_URL)

    try:
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            sslmode="require"
        )
        return conn

    except Exception as e:
        print("DB connection error:", e)
        return None


# Создаём таблицу при старте
conn = get_connection()
if conn:
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
    except Exception as e:
        print("Error creating table:", e)
    finally:
        conn.close()


# ------------------------
#  Маршруты
# ------------------------

@app.route('/')
def home():
    return jsonify({"service": "running"})


@app.route('/save', methods=['POST'])
def save_message():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    data = request.get_json() or {}
    message = data.get("message", "")

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"status": "saved", "message": message})


@app.route('/messages', methods=['GET'])
def get_messages():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, content, created_at
                FROM messages
                ORDER BY id DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    messages = [
        {"id": r[0], "text": r[1], "time": r[2].isoformat()}
        for r in rows
    ]

    return jsonify(messages)


# ------------------------
#  Запуск локально
# ------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
