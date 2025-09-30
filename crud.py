from sqlalchemy import select
from sqlalchemy.orm import Session, Query

import auth
import models
from models import Gauge, User
import schemas


def create_gauge(db: Session, gauge: schemas.GaugeCreate):
    db_gauge = Gauge(**gauge.dict())
    db.add(db_gauge)
    db.commit()
    db.refresh(db_gauge)
    return db_gauge


def delete_gauge(db: Session, gauge_id: int):
    db_gauge = db.query(models.Gauge).filter(Gauge.id == gauge_id).first()
    if db_gauge:
        db.delete(db_gauge)
        db.commit()
    return True


def read_all_gauges(db: Session):
    result = db.query(models.Gauge).filter().all()
    return result


def read_gauge(db: Session, gauge_id: int):
    gauge = db.query(models.Gauge).filter(Gauge.id == gauge_id).first()
    return gauge


def get_user_by_name(db: Session, full_name: str):
    user = db.query(models.User).filter(User.full_name == full_name).first()
    return user


def read_all_users(db: Session):
    result = db.query(models.User).filter().all()
    return result


def update_gauge(db: Session, gauge_id: int, gauge_update: schemas.GaugeUpdate):
    # Находим датчик
    db_gauge = db.query(models.Gauge).filter(models.Gauge.id == gauge_id).first()

    # Обновляем поля
    update_data = gauge_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_gauge, field, value)

    db.commit()
    db.refresh(db_gauge)
    return db_gauge


def register_user(db: Session, full_name: str, password: str, phone_number: str, role: str):
    existing_user = get_user_by_name(db, full_name)
    if existing_user:
        raise ValueError("Пользователь с таким именем уже существует")
    hashed_password = auth.get_password_hash(password)
    db_user = User(
        full_name=full_name,
        password=hashed_password,
        phone_number=phone_number,
        role=role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_id_by_name(db: Session, full_name: str):
    user_id = db.query(models.User).filter(models.User.full_name == full_name).first().id
    return user_id


def get_full_name_by_id(db: Session, user_id: int):
    full_name = db.query(models.User).filter(models.User.id == user_id).first().full_name
    return full_name


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    # Находим датчик
    db_user = db.query(models.User).filter(models.User.id == user_id).first()


    # Обновляем поля
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user



def read_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    return db_user