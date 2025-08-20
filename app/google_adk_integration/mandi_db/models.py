# ============================================================================
# app/database/models.py - Core Database Models
# ============================================================================
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import json

Base = declarative_base()


class MarketPrice(Base):
    """Core market prices table with all essential fields"""
    __tablename__ = 'market_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    market = Column(String(200), nullable=False)
    commodity = Column(String(100), nullable=False)
    variety = Column(String(100))
    grade = Column(String(50))
    arrival_date = Column(DateTime, nullable=False)

    # Price data
    min_price = Column(Float)
    max_price = Column(Float)
    modal_price = Column(Float, nullable=False)

    # Computed trend fields
    price_change = Column(Float, default=0)  # Change from previous day
    percentage_change = Column(Float, default=0)  # Percentage change
    trend = Column(String(10), default='stable')  # up, down, stable

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Essential indexes for performance
    __table_args__ = (
        Index('idx_commodity_date', 'commodity', 'arrival_date'),
        Index('idx_state_district', 'state', 'district'),
        Index('idx_market_commodity', 'market', 'commodity'),
        Index('idx_arrival_date', 'arrival_date'),
    )


class MarketAnalytics(Base):
    """Simplified analytics table for core insights"""
    __tablename__ = 'market_analytics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity = Column(String(100), nullable=False)
    analysis_date = Column(DateTime, nullable=False)

    # Key price metrics
    avg_price = Column(Float)
    highest_price = Column(Float)
    lowest_price = Column(Float)
    price_volatility = Column(Float)  # Standard deviation

    # Market summary
    total_markets = Column(Integer)
    top_market = Column(String(200))
    top_market_price = Column(Float)

    # Simple trends
    weekly_trend = Column(String(10))  # up, down, stable
    monthly_trend = Column(String(10))

    # Basic predictions
    predicted_price_7d = Column(Float)
    predicted_price_14d = Column(Float)
    prediction_confidence = Column(Float)

    # JSON data for additional info
    price_history = Column(Text)  # JSON string for last 30 days
    recommendations = Column(Text)  # JSON array of recommendations

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_commodity_analysis_date', 'commodity', 'analysis_date'),
    )


class DataSyncLog(Base):
    """Sync logging table"""
    __tablename__ = 'data_sync_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_date = Column(DateTime, nullable=False)
    sync_type = Column(String(50), nullable=False)  # 'full', 'incremental'
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'partial'
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    error_message = Column(Text)
    duration_seconds = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)