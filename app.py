from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey12345')

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, default=550)


def get_banks_by_rating(rating):
    if rating >= 750:
        return [
            {"name": "Сбербанк", "rate": "9.5%", "max_amount": "5 000 000 ₽", "term": "до 5 лет"},
            {"name": "Тинькофф", "rate": "9.9%", "max_amount": "3 000 000 ₽", "term": "до 3 лет"},
            {"name": "Альфа-Банк", "rate": "10.0%", "max_amount": "4 000 000 ₽", "term": "до 4 лет"},
            {"name": "ВТБ", "rate": "10.5%", "max_amount": "6 000 000 ₽", "term": "до 7 лет"},
        ]
    elif rating >= 650:
        return [
            {"name": "Тинькофф", "rate": "12.5%", "max_amount": "2 000 000 ₽", "term": "до 3 лет"},
            {"name": "Альфа-Банк", "rate": "13.0%", "max_amount": "2 500 000 ₽", "term": "до 3 лет"},
            {"name": "Открытие", "rate": "13.5%", "max_amount": "1 500 000 ₽", "term": "до 3 лет"},
            {"name": "Райффайзенбанк", "rate": "12.9%", "max_amount": "2 000 000 ₽", "term": "до 3 лет"},
        ]
    elif rating >= 550:
        return [
            {"name": "Почта Банк", "rate": "15.5%", "max_amount": "1 000 000 ₽", "term": "до 2 лет"},
            {"name": "МТС Банк", "rate": "16.0%", "max_amount": "1 200 000 ₽", "term": "до 2 лет"},
            {"name": "Русский Стандарт", "rate": "16.5%", "max_amount": "800 000 ₽", "term": "до 2 лет"},
            {"name": "Хоум Кредит", "rate": "15.9%", "max_amount": "900 000 ₽", "term": "до 2 лет"},
        ]
    elif rating >= 450:
        return [
            {"name": "МигКредит", "rate": "25.0%", "max_amount": "500 000 ₽", "term": "до 1 года"},
            {"name": "Займер", "rate": "28.0%", "max_amount": "300 000 ₽", "term": "до 6 мес"},
            {"name": "Ezaem", "rate": "26.5%", "max_amount": "400 000 ₽", "term": "до 1 года"},
        ]
    else:
        return [
            {"name": "Нет предложений", "rate": "-", "max_amount": "Улучшите рейтинг", "term": "-"},
        ]

with app.app_context():
    db.create_all()


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

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['fullname'] = user.fullname
            return redirect(url_for('home'))
        else:
            return "<h1>Неверный логин или пароль</h1><a href='/entry'>Попробовать снова</a>"

    return render_template('entry.html')


@app.route('/authorization', methods=['GET', 'POST'])
def authorization():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "<h1>Пользователь уже существует!</h1><a href='/authorization'>Назад</a>"

        new_user = User(fullname=fullname, username=username,
                       password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        return render_template('index.html')

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


@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('entry'))

    user = User.query.filter_by(username=session['username']).first()
    banks = get_banks_by_rating(user.rating)

    return render_template('profile.html', user=user, banks=banks)


@app.route('/admin')
def admin():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('entry'))

    users = User.query.all()
    df = pd.DataFrame([(u.id, u.fullname, u.username, u.rating) for u in users],
                      columns=['ID', 'ФИО', 'Логин', 'Рейтинг'])

    total_users = len(df)
    avg_rating = df['Рейтинг'].mean()

    df['Диапазон'] = pd.cut(df['Рейтинг'],
                            bins=[300, 450, 550, 650, 750, 800],
                            labels=['300-450', '451-550', '551-650', '651-750', '751-800'])
    chart_data = df['Диапазон'].value_counts().sort_index().to_dict()

    def get_category(r):
        if r >= 700: return 'Отличный (700+)'
        if r >= 600: return 'Хороший (600-699)'
        if r >= 500: return 'Средний (500-599)'
        return 'Низкий (<500)'

    df['Категория'] = df['Рейтинг'].apply(get_category)
    pie_data = df['Категория'].value_counts().to_dict()

    percent = ((avg_rating - 300) / 500) * 100
    percent = max(0, min(100, percent))

    if avg_rating >= 700:
        indicator_color = '#44cc44'
        status_text = 'Отличный'
    elif avg_rating >= 600:
        indicator_color = '#88cc44'
        status_text = 'Хороший'
    elif avg_rating >= 500:
        indicator_color = '#ffaa00'
        status_text = 'Средний'
    else:
        indicator_color = '#ff4444'
        status_text = 'Низкий'

    return render_template('admin.html',
                           total_users=total_users,
                           avg_rating=round(avg_rating, 1),
                           chart_data=chart_data,
                           pie_data=pie_data,
                           percent=round(percent),
                           indicator_color=indicator_color,
                           status_text=status_text)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('entry'))


if __name__ == '__main__':
    app.run(debug=True)