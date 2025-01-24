import os
import sqlite3
import hashlib
from flask import Flask, request, render_template, redirect, url_for, flash, session

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')
ADMIN_HASH = os.getenv('ADMIN_HASH', "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4")
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
DB_NAME = "bots.db"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def init_db():
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                pfp TEXT NOT NULL,
                screenshots TEXT NOT NULL
            )
        """)

def valid_file(name):
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXT

@app.route('/')
def home():
    with sqlite3.connect(DB_NAME) as db:
        bots = db.execute("SELECT name, username, pfp FROM bots").fetchall()
    return render_template('index.html', bots=bots)

@app.route('/bot/<username>')
def bot(username):
    with sqlite3.connect(DB_NAME) as db:
        bot = db.execute("SELECT name, description, username, screenshots FROM bots WHERE username = ?", (username,)).fetchone()
    if bot:
        screenshots = bot[3].split(',')
        return render_template('bot.html', bot=bot, screenshots=screenshots)
    return "Бот не найден", 404

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('auth'):
        if request.method == 'POST':
            name, desc, user = request.form.get('name'), request.form.get('description'), request.form.get('username')
            pfp, screenshots = request.files.get('pfp'), request.files.getlist('screenshots')

            if not all([name, desc, user, pfp, screenshots]) or not valid_file(pfp.filename) or not all(valid_file(s.filename) for s in screenshots):
                flash('Некорректные данные!', 'error')
                return redirect(url_for('admin'))

            bot_dir = os.path.join(app.config['UPLOAD_FOLDER'], user)
            os.makedirs(bot_dir, exist_ok=True)
            pfp_path = os.path.join(bot_dir, "pfp.jpg")
            pfp.save(pfp_path)

            shot_paths = [os.path.join(bot_dir, f"screenshot_{i}.jpg") for i, shot in enumerate(screenshots, 1)]
            for path, shot in zip(shot_paths, screenshots):
                shot.save(path)

            try:
                with sqlite3.connect(DB_NAME) as db:
                    db.execute("""
                        INSERT INTO bots (name, description, username, pfp, screenshots)
                        VALUES (?, ?, ?, ?, ?)
                    """, (name, desc, user, pfp_path, ",".join(shot_paths)))
                    flash('Бот добавлен!', 'success')
            except sqlite3.IntegrityError:
                flash('Юзернейм уже занят!', 'error')

        return render_template('admin.html')

    if request.method == 'POST':
        if hashlib.sha256(request.form.get('code', '').encode()).hexdigest() == ADMIN_HASH:
            session['auth'] = True
            return redirect(url_for('admin'))
        flash('Неверный код!', 'error')
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.pop('auth', None)
    flash('Вы вышли.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)