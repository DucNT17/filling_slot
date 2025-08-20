from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
load_dotenv()

DB_POSTGRES_URL = os.getenv("DB_POSTGRES_URL")

engine = create_engine(
    DB_POSTGRES_URL,
    echo=True,
    future=True,
    pool_size=20,           # Tăng pool size từ 5 (mặc định) lên 20
    max_overflow=30,        # Tăng overflow từ 10 (mặc định) lên 30
    pool_timeout=60,        # Tăng timeout từ 30s lên 60s
    pool_recycle=3600,      # Recycle connection sau 1 giờ
    pool_pre_ping=True      # Kiểm tra connection trước khi sử dụng
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base cho ORM models
Base = declarative_base()
