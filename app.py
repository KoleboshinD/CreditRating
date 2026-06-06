from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///credit_rating.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey12345'

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, default=550)


with app.app_context():
    db.drop_all()  # Временно! Удаляет старые таблицы
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(fullname='Администратор', username='admin', password='admin123', rating=800)
        db.session.add(admin)

    if not User.query.filter_by(username='user').first():
        user = User(fullname='Обычный Пользователь', username='user', password='user123', rating=550)
        db.session.add(user)


@app.route('/')
def home():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        return render_template('index.html', rating=user.rating)
    return redirect(url_for('entry'))


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

        return "<h1>Регистрация успешна!</h1><a href='/entry'>Войти</a>"

    return render_template('authorization.html')


@app.route('/save_rating', methods=['POST'])
def save_rating():
    data = request.get_json()
    rating = data.get('rating')

    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        user.rating = rating
        db.session.commit()
        return jsonify({'success': True, 'message': f'Рейтинг сохранён: {rating}'})

    return jsonify({'success': False, 'message': 'Ошибка: не авторизован'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('entry'))


if __name__ == '__main__':
    app.run(debug=True)