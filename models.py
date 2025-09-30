import enum
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime, func, Date, Boolean
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql.roles import SQLRole

from database import Base


class Gauge(Base):
    __tablename__ = 'gauges'
    id: int = Column(Integer, primary_key=True, index=True)
    title: str = Column(String(255))
    view: str = Column(String(50))
    type: str = Column(String(50))
    min: float = Column(Float)
    max: float = Column(Float)
    measure_unit: str = Column(String(10))
    low_low: Optional[str] = Column(String(50))
    low: Optional[str] = Column(String(50))
    high: Optional[str] = Column(String(50))
    high_high: Optional[str] = Column(String(50))
    description: Optional[str] = Column(String(255))
    system: str = Column(String(50))
    tag: str = Column(String(50))
    device: str = Column(String(50))
    by_user: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    verification_date = Column(Date, nullable=True)
    users = relationship('User', back_populates='gauges')


class User(Base):
    __tablename__ = 'users'
    id: int = Column(Integer, primary_key = True, index=True)
    full_name: str = Column(String(255), nullable=False)
    password: str = Column(String(255))
    role: str = Column(String(20), nullable=False, default='kip')
    active: bool = Column(Boolean, default=True)
    phone_number: str = Column(String(20))
    gauges = relationship('Gauge', back_populates='users')


