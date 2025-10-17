import enum
from datetime import date

from enum import Enum

from pydantic import BaseModel, EmailStr


class Role(str, Enum):
    MASTER = 'master'
    KIP = 'kip'


class GaugeBase(BaseModel):
    title: str
    view: str
    type: str
    min: float
    max: float
    measure_unit: str
    low_low: str | None = None
    low: str | None = None
    high: str | None = None
    high_high: str | None = None
    description: str | None = None
    system: str
    type: str
    device: str
    tag: str
    verification_date: date | None = None


class GaugeCreate(GaugeBase):
    by_user: int


class GaugeUpdate(GaugeBase):
    pass


class GaugeRead(GaugeBase):
    id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    full_name: str
    password: str
    role: Role = str
    active: bool
    phone_number: str
    email: EmailStr


class UserLoginSchema(UserBase):
    pass


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    role: Role = Role.KIP


class UserUpdate(BaseModel):
    full_name: str
    role: Role = str
    active: bool
    phone_number: str
    email: EmailStr