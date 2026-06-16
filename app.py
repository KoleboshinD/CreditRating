from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey12345')

API_URL = "http://localhost:8000"


def convert_dates(history):
    for item in history:
        if item.get('request_date') and isinstance(item['request_date'], str):
            try:
                item['request_date'] = datetime.fromisoformat(item['request_date'].replace('Z', '+00:00'))
            except:
                item['request_date'] = None
        if item.get('response_date') and isinstance(item['response_date'], str):
            try:
                item['response_date'] = datetime.fromisoformat(item['response_date'].replace('Z', '+00:00'))
            except:
                item['response_date'] = None
    return history


@app.route('/')
def home():
    if 'username' in session:
        try:
            resp = requests.get(f"{API_URL}/api/get_user_by_username/{session['username']}")
            if resp.status_code == 200:
                user = resp.json()
                return render_template('index.html', rating=user['rating'])
        except:
            pass
        return render_template('index.html', rating=550)
    return redirect(url_for('entry'))


@app.route('/entry', methods=['GET', 'POST'])
def entry():
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            resp = requests.get(f"{API_URL}/api/get_user_by_username/{username}")
            if resp.status_code == 200:
                user = resp.json()
                if user and check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['fullname'] = user['fullname']
                    return redirect(url_for('home'))
        except:
            pass
        return "<h1>Неверный логин или пароль</h1><a href='/entry'>Попробовать снова</a>"
    return render_template('entry.html')


@app.route('/authorization', methods=['GET', 'POST'])
def authorization():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            resp = requests.get(f"{API_URL}/api/get_user_by_username/{username}")
            if resp.status_code == 200 and resp.json():
                return "<h1>Пользователь уже существует!</h1><a href='/authorization'>Назад</a>"
        except:
            pass

        password_hash = generate_password_hash(password)
        try:
            requests.post(f"{API_URL}/api/create_user", json={
                "username": username,
                "fullname": fullname,
                "password": password_hash,
                "rating": 800
            })
        except:
            pass
        return render_template('index.html', rating=800)
    return render_template('authorization.html')


@app.route('/save_rating', methods=['POST'])
def save_rating():
    data = request.get_json()
    if 'user_id' in session:
        try:
            resp = requests.put(f"{API_URL}/api/update_user_rating", json={
                "id": session['user_id'],
                "rating": data['rating']
            })
            if resp.status_code == 200:
                return jsonify({'success': True, 'message': f'Рейтинг сохранён: {data["rating"]}'})
        except:
            pass
        return jsonify({'success': False, 'message': 'Ошибка сохранения'})
    return jsonify({'success': False, 'message': 'Не авторизован'})


@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('entry'))

    try:
        resp = requests.get(f"{API_URL}/api/get_user_by_username/{session['username']}")
        if resp.status_code != 200:
            return redirect(url_for('entry'))
        user = resp.json()

        resp = requests.get(f"{API_URL}/api/get_banks_by_rating/{user['rating']}")
        banks = resp.json() if resp.status_code == 200 else []

        resp = requests.get(f"{API_URL}/api/get_user_credit_history/{user['id']}")
        history = resp.json() if resp.status_code == 200 else []

        history = convert_dates(history)

        return render_template('profile.html', user=user, banks=banks, history=history)
    except Exception as e:
        print(f"Ошибка: {e}")
        return redirect(url_for('entry'))


@app.route('/admin')
def admin():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('entry'))

    try:
        resp = requests.get(f"{API_URL}/api/get_all_users")
        users = resp.json() if resp.status_code == 200 else []

        for user in users:
            if user.get('created_at') and isinstance(user['created_at'], str):
                try:
                    user['created_at'] = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
                except:
                    pass

        return render_template('admin.html', users=users)
    except Exception as e:
        print(f"Ошибка: {e}")
        return render_template('admin.html', users=[])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('entry'))


@app.route('/credit_request', methods=['POST'])
def credit_request():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Не авторизован'})

    data = request.get_json()
    try:
        resp = requests.post(f"{API_URL}/api/credit_request", json={
            "user_id": session['user_id'],
            "bank_id": data['bank_id'],
            "amount": data['amount']
        })
        if resp.status_code == 200:
            return jsonify(resp.json())
        return jsonify({'success': False, 'message': 'Ошибка сервера'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)