from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'tvoy_sekretny_klyuch_12345'

ADMIN_PASSWORD_HASH = hashlib.sha256('admin123'.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        player TEXT,
        civilization TEXT,
        judge TEXT,
        answers TEXT,
        ip TEXT
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def exam():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('''INSERT INTO answers (timestamp, player, civilization, judge, answers, ip)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (datetime.now().isoformat(),
               data.get('player'),
               data.get('civilization'),
               data.get('judge'),
               json.dumps(data.get('answers'), ensure_ascii=False),
               request.remote_addr))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='Неверный пароль')
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('SELECT id, timestamp, player, civilization, judge, answers FROM answers ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            'id': row[0],
            'timestamp': row[1],
            'player': row[2],
            'civilization': row[3],
            'judge': row[4],
            'answers': json.loads(row[5])
        })
    
    return render_template('admin.html', results=results)

@app.route('/admin/delete/<int:answer_id>', methods=['POST'])
def delete_answer(answer_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'unauthorized'}), 401
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('DELETE FROM answers WHERE id = ?', (answer_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)