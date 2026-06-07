import psycopg2
from psycopg2 import pool
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "CreditRating",
    "user": "postgres",
    "password": "rostik2007",
    "client_encoding": "UTF8"
}

_connection_pool = None


def init_db():
    global _connection_pool
    try:
        _connection_pool = pool.SimpleConnectionPool(
            5, 10, **DB_CONFIG
        )
        print("Пул соединений с БД создан")
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        raise


def _get_conn():
    if _connection_pool is None:
        raise Exception("БД не инициализирована. Вызовите init_db()")
    return _connection_pool.getconn()


def _return_conn(conn):
    if _connection_pool and conn:
        _connection_pool.putconn(conn)



def get_user_by_id(user_id):
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM users WHERE id = %s
            """, (user_id,))
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "fullname": row[2],
                    "rating": row[3],
                    "created_at": row[4]
                }
            return None
    except Exception as e:
        print(f"Ошибка в get_user_by_id: {e}")
        return None
    finally:
        _return_conn(conn)


def get_user_by_username(username):
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM users WHERE username = %s
            """, (username,))
            row = cur.fetchone()

            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "fullname": row[2],
                    "password": row[3],
                    "rating": row[4],
                    "created_at": row[5].strftime("%Y-%m-%d") if row[5] else None
                }
            return None
    except Exception as e:
        print(f"Ошибка в get_user_by_username: {e}")
        return None
    finally:
        _return_conn(conn)

def create_user(username, fullname, password, rating):
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, fullname, password, rating)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """, (username, fullname, password, rating))
            conn.commit()
            res = cur.fetchone()
            return res, None
    except Exception as e:
        print(f"Ошибка в create_user: {e}")
        return None, str(e)
    finally:
        _return_conn(conn)

def update_user_rating(id, rating):
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE users
                SET rating = %s
                WHERE id = %s;
            """, (rating, id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка в update_user_rating: {e}")
        return False
    finally:
        _return_conn(conn)

def get_all_users():
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM users ORDER BY id
            """)
            rows = cur.fetchall()
            users = []
            for row in rows:
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "fullname": row[2],
                    "password": row[3],
                    "rating": row[4],
                    "created_at": row[5].strftime("%Y-%m-%d")
                })
            return users
    except Exception as e:
        print(f"Ошибка в get_user_by_email: {e}")
        return None
    finally:
        _return_conn(conn)

def get_banks_by_rating(rating):
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM banks WHERE min_rating <= %s
            """, (rating,))
            rows = cur.fetchall()
            banks = []
            for row in rows:
                banks.append({
                    "id": row[0],
                    "name": row[1],
                    "min_rating": row[2],
                    "max_rating": row[3],
                    "interest_rate": row[4],
                    "max_amount": row[5],
                    "term": row[6]
                })
            return banks
    except Exception as e:
        print(f"Ошибка в get_user_by_rating: {e}")
        return None
    finally:
        _return_conn(conn)

def get_bank_by_id(bank_id):
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM banks WHERE id = %s", (bank_id,))
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "min_rating": row[2],
                    "max_rating": row[3],
                    "interest_rate": row[4],
                    "max_amount": row[5],
                    "term": row[6]
                }
            return None
    except Exception as e:
        print(f"Ошибка в get_bank_by_id: {e}")
        return None
    finally:
        _return_conn(conn)

def save_credit_request(user_id, bank_id, amount, approved_amount, status):
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO credit_history (user_id, bank_id, requested_amount, status, approved_amount)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, bank_id, amount, status, approved_amount))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка в save_credit_request: {e}")
        return False
    finally:
        _return_conn(conn)

def get_user_credit_history(user_id):
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ch.id, ch.user_id, ch.bank_id, ch.requested_amount, 
                       ch.status, ch.requested_date, ch.approved_amount, ch.response_date,
                       b.name as bank_name
                FROM credit_history ch
                JOIN banks b ON ch.bank_id = b.id
                WHERE user_id = %s
                ORDER BY requested_date DESC
            """, (user_id,))
            rows = cur.fetchall()
            history = []
            for row in rows:
                history.append({
                    "id": row[0],
                    "user_id": row[1],
                    "bank_id": row[2],
                    "requested_amount": row[3],
                    "status": row[4],
                    "request_date": row[5],
                    "approved_amount": row[6],
                    "response_date": row[7],
                    "bank_name": row[8]
                })
            return history
    except Exception as e:
        print(f"Ошибка в get_user_credit_history: {e}")
        return []
    finally:
        _return_conn(conn)