from authx import AuthXConfig, AuthX
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from starlette.templating import Jinja2Templates

import models
from database import get_db
import crud

config = AuthXConfig()
config.JWT_SECRET_KEY = 'SECRET_KEY'
config.JWT_ACCESS_COOKIE_NAME = 'my_access_token'
config.JWT_TOKEN_LOCATION = ['cookies']
config.JWT_ALGORITHM = 'HS256'

security = AuthX(config=config)

# Инициализация для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


templates = Jinja2Templates(directory="static/templates")


def is_password_hashed(password: str) -> bool:
    """Проверяет, является ли строка хэшированным паролем"""
    if password.startswith("$2b$") or password.startswith("$2a$") or password.startswith("$2y$"):
        return True
    return False


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Простая проверка пароля"""
    # Сначала пытаемся проверить как хэш
    try:
        if stored_password.startswith("$2"):
            return pwd_context.verify(plain_password, stored_password)
    except:
        pass

    # Если не получилось - проверяем как plain text
    return plain_password == stored_password


def get_password_hash(password: str) -> str:
    """Создает хэш пароля"""
    return pwd_context.hash(password)


def authenticate_user(full_name: str, password: str, db: Session = Depends(get_db)):
    login_user = crud.get_user_by_name(db, full_name)
    if not login_user:
        return False

    # Проверяем пароль
    if is_password_hashed(login_user.password):
        # Пароль уже хэширован
        if verify_password(password, login_user.password):
            return login_user
    return False


def get_user_info_from_token(token: str) -> str | None:
    """Извлекаем информацию из JWT токена authx"""
    if not token:
        return None

    try:
        payload = jwt.decode(token, key=config.JWT_SECRET_KEY, algorithms=config.JWT_ALGORITHM)
        if payload:
            # Authx сохраняет uid в поле 'sub'
            full_name = payload.get("full_name")
            return f'{full_name}'
    except Exception:
        pass

    return None


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
        my_access_token: str = Cookie(None, alias=config.JWT_ACCESS_COOKIE_NAME),
        db: Session = Depends(get_db)
):
    if not my_access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    full_name = get_user_info_from_token(my_access_token)
    if not full_name:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.full_name == full_name).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        'full_name': user.full_name,
        'role': user.role,
        'active': user.active,
        'id': user.id,
    }


def require_master(user: dict = Depends(get_current_user)):
    if user['role'] != 'мастер' or not user['active']:
        raise HTTPException(status_code=403)
    return user


def require_kip(user: dict = Depends(get_current_user)):
    if user['role'] not in ('кип', 'мастер') or not user['active']:
        raise HTTPException(status_code=403)
    return user


def require_user(user: dict = Depends(get_current_user)):
    if user['role'] not in ('кип', 'мастер', 'пользователь') or not user['active']:
        raise HTTPException(status_code=403)
    return user




# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     """Создает JWT токен"""
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt
#
#
# async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     """Получает текущего пользователя из токена"""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Неверные учетные данные",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#
#     user = get_user_by_name(db, username=username)
#     if user is None:
#         raise credentials_exception
#     return user