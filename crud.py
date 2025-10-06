from typing import List, Tuple

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
        return None
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


def get_gauge_by_title(db: Session, gauge_title: str) -> dict:
    db_gauge = db.query(models.Gauge).filter(models.Gauge.title == gauge_title).all()
    return db_gauge


def get_gauges_with_pagination(
        db: Session,
        search: str | None = None,
        skip: int = 0,
        limit: int = 10
)  -> Tuple[List[models.Gauge], int]:
    query = db.query(models.Gauge)

    # Поиск по наименованию
    if search and search.strip():
        search_term = search.strip()
        query = query.filter(models.Gauge.title==search_term)

    # Получаем общее количество для пагинации
    total = query.count()

    # Применяем пагинацию
    gauges = query.offset(skip).limit(limit).all()

    return gauges, total


def search_gauges_strict(
        db: Session,
        search_term: str,
        skip: int = 0,
        limit: int = 10
) -> Tuple[List[models.Gauge], int]:
    """
    Строгий поиск датчиков по наименованию
    """
    if not search_term or not search_term.strip():
        # Если поисковый запрос пустой, возвращаем пустой результат
        return [], 0

    search_term = search_term.strip()
    print(f"🔍 Строгий поиск: '{search_term}'")

    query = db.query(models.Gauge).filter(
        models.Gauge.title.ilike(f"%{search_term}%")
    )

    total = query.count()
    gauges = query.offset(skip).limit(limit).all()

    print(f"🔍 Найдено датчиков: {total}")
    for gauge in gauges:
        print(f"🔍 - {gauge.title}")

    return gauges, total