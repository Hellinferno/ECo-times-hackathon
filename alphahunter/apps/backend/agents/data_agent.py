import yfinance as yf
import pandas as pd
import datetime
from sqlalchemy.orm import Session
from loguru import logger
import json
from tenacity import retry, stop_after_attempt, wait_exponential

from models.db.market_data_cache import MarketDataCache

class DataAgent:
    def __init__(self, db: Session):
        self.db = db

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_market_data(self, symbol: str, lookback_days: int = 60, lookback_years: int = 2):
        """
        Fetches normalized OHLCV data using yfinance. 
        Note: Indian stocks on Yahoo Finance need the .NS extension.
        """
        yf_symbol = f"{symbol}.NS"
        
        # Try to check cache first for live/short-term data (skipped for brevity, but could use MarketDataCache)
        
        try:
            ticker = yf.Ticker(yf_symbol)
            # Fast fetch for short term (e.g. 60 days to compute 20d avg padding and 30d resistance)
            short_term_data = ticker.history(period=f"{lookback_days}d")
            
            if short_term_data.empty:
                return None
            
            current_price = float(short_term_data['Close'].iloc[-1])
            volume_today = int(short_term_data['Volume'].iloc[-1])
            
            # Format history for internal use
            ohlcv_short = []
            for date, row in short_term_data.iterrows():
                ohlcv_short.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })

            return {
                "symbol": symbol,
                "current_price": current_price,
                "volume_today": volume_today,
                "ohlcv_short": ohlcv_short,
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_historical_data_for_backtest(self, symbol: str, lookback_years: int = 2):
        """Fetch 2-year history for backtesting"""
        yf_symbol = f"{symbol}.NS"
        try:
            ticker = yf.Ticker(yf_symbol)
            hist_data = ticker.history(period=f"{lookback_years}y")
            if hist_data.empty:
                return []
            
            ohlcv = []
            for date, row in hist_data.iterrows():
                ohlcv.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching backtest history for {symbol}: {str(e)}")
            return []

    def get_bulk_deals(self, symbol: str):
        """
        Usually fetches from NSE via a CSV endpoint or similar.
        In this hackathon stub, we'll return a mock list of bulk deals 
        or query the local `bulk_deals` table if pre-seeded.
        """
        from models.db.bulk_deal import BulkDeal
        # Fetch deals in the last 60 days
        cutoff = datetime.date.today() - datetime.timedelta(days=60)
        deals = self.db.query(BulkDeal).filter(
            BulkDeal.symbol == symbol,
            BulkDeal.deal_date >= cutoff
        ).all()
        
        return [{
            "date": d.deal_date.strftime('%Y-%m-%d'),
            "client_name": d.client_name,
            "deal_type": d.deal_type,
            "quantity": d.quantity,
            "price": float(d.price)
        } for d in deals]
