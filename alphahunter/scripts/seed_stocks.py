import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from models.db.stock import Stock
from models.db.base import Base

def seed_stocks():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    stocks = [
        {"symbol": "INFY", "name": "Infosys Ltd", "sector": "IT"},
        {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT"},
        {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "sector": "Energy"},
        {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "sector": "Banking"},
        {"symbol": "TATASTEEL", "name": "Tata Steel Ltd", "sector": "Metals"},
        {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "sector": "Banking"},
        {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking"},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "sector": "Telecom"},
        {"symbol": "ITC", "name": "ITC Ltd", "sector": "FMCG"},
        {"symbol": "WIPRO", "name": "Wipro Ltd", "sector": "IT"},
        {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "sector": "FMCG"},
        {"symbol": "LT", "name": "Larsen & Toubro Ltd", "sector": "Construction"},
        {"symbol": "AXISBANK", "name": "Axis Bank Ltd", "sector": "Banking"},
        {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd", "sector": "Automobile"}
    ]

    print("Seeding stocks...")
    added_count = 0
    for stock_data in stocks:
        existing = db.query(Stock).filter(Stock.symbol == stock_data["symbol"]).first()
        if not existing:
            new_stock = Stock(**stock_data)
            db.add(new_stock)
            added_count += 1

    db.commit()
    print(f"Done! {added_count} stocks seeded.")
    db.close()

if __name__ == "__main__":
    seed_stocks()
