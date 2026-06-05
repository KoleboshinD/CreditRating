import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')

    # База данных (SQLite для простоты)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///credit_rating.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки PostgreSQL
    # DB_HOST = os.getenv('DB_HOST', 'localhost')
    # DB_PORT = os.getenv('DB_PORT', '5432')
    # DB_NAME = os.getenv('DB_NAME', 'credit_rating')
    # DB_USER = os.getenv('DB_USER', 'postgres')
    # DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    # SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"