import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# Connects to the database, creates session.

# explicitly point to root .env regardless of where this file is called from
load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env')

class Base(DeclarativeBase):
    pass

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL').strip()  # type: ignore
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

def get_session():
    with SessionLocal() as session:
        yield session

if __name__ == "__main__":
    conn = engine.connect()
    print("Connected to db")
    conn.close()