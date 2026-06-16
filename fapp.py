from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from database import (
    init_db, get_user_by_id, get_user_by_username, create_user,
    update_user_rating, get_all_users, get_banks_by_rating,
    get_bank_by_id, save_credit_request, get_user_credit_history
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_amount(amount_str):
    import re
    numbers = re.findall(r'\d+', amount_str)
    return int(''.join(numbers)) if numbers else 0


@app.get("/api/get_user_by_id/{user_id}")
def api_get_user_by_id(user_id: int):
    return get_user_by_id(user_id)


@app.get("/api/get_user_by_username/{username}")
def api_get_user_by_username(username: str):
    return get_user_by_username(username)


@app.post("/api/create_user")
def api_create_user(data: dict):
    result, error = create_user(data['username'], data['fullname'], data['password'], data['rating'])
    return {"result": result, "error": error}


@app.put("/api/update_user_rating")
def api_update_user_rating(data: dict):
    success = update_user_rating(data['id'], data['rating'])
    return {"success": success}


@app.get("/api/get_all_users")
def api_get_all_users():
    return get_all_users()


@app.get("/api/get_banks_by_rating/{rating}")
def api_get_banks_by_rating(rating: int):
    return get_banks_by_rating(rating)


@app.get("/api/get_bank_by_id/{bank_id}")
def api_get_bank_by_id(bank_id: int):
    return get_bank_by_id(bank_id)


@app.post("/api/save_credit_request")
def api_save_credit_request(data: dict):
    success = save_credit_request(
        data['user_id'], data['bank_id'],
        data['amount'], data['approved_amount'], data['status']
    )
    return {"success": success}


@app.get("/api/get_user_credit_history/{user_id}")
def api_get_user_credit_history(user_id: int):
    return get_user_credit_history(user_id)


@app.post("/api/credit_request")
def api_credit_request(data: dict):
    user = get_user_by_id(data['user_id'])
    bank = get_bank_by_id(data['bank_id'])

    if not user or not bank:
        return {"success": False, "message": "Пользователь или банк не найден"}

    max_amount = parse_amount(bank['max_amount'])
    approved_amount = min(data['amount'], max_amount)
    status = 'approved' if approved_amount >= data['amount'] else 'partial'

    save_credit_request(data['user_id'], data['bank_id'], data['amount'], approved_amount, status)

    return {
        "success": True,
        "status": status,
        "approved_amount": approved_amount,
        "message": "Заявка одобрена"
    }


if __name__ == '__main__':
    import uvicorn

    init_db()
    uvicorn.run(app, host='0.0.0.0', port=8000)