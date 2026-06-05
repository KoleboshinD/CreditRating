from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from database import Config

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)

# Теперь secret_key берётся из Config
app.secret_key = Config.SECRET_KEY

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html')
    else:
        return render_template('entry.html')


@app.route('/entry', methods=['GET', 'POST'])
def entry():
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['fullname'] = user.fullname
            return redirect(url_for('home'))
        else:
            return "<h1>Ошибка! Неверный логин или пароль</h1><a href='/entry'>Попробовать снова</a>"

    return render_template('entry.html')


@app.route('/authorization', methods=['GET', 'POST'])
def authorization():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "<h1>Пользователь с таким именем уже существует!</h1><a href='/authorization'>Назад</a>"

        new_user = User(fullname=fullname, username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return render_template('entry.html')

    return render_template('authorization.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)