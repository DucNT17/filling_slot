from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
load_dotenv()

# URL của bạn
DB_POSTGRES_URL = os.getenv("DB_POSTGRES_URL")

# Tạo engine
engine = create_engine(DB_POSTGRES_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base cho ORM models
Base = declarative_base()