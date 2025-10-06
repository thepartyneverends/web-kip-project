import math
from datetime import date

from fastapi import FastAPI, Query, Depends, Request, HTTPException, Form, Cookie
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

import auth
import crud
import models
import schemas
from auth import security, config, authenticate_user, get_user_info_from_token, require_kip
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')

templates = Jinja2Templates(directory='static/templates')


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code in [401, 403]:
        return RedirectResponse(url='/form-login', status_code=302)

    return HTMLResponse(
        content=f'<h1>Ошибка {exc.status_code} </h1><p>{exc.detail}</p>',
        status_code=exc.status_code
    )


@app.get('/gauges/search/?gauge_title={gauge_title}')
async def gauge_by_title(request: Request,
                         gauge_title: str,
                         db: Session = Depends(get_db),
                         ):
    return templates.TemplateResponse('gauge_search.html', {'request': request,
                                      'gauges': crud.get_gauge_by_title(db, gauge_title)})


@app.get('/gauges')
def read_all_gauges(db: Session = Depends(get_db)):
    return crud.read_all_gauges(db)


@app.get('/')
async def base(request: Request, db: Session = Depends(get_db),
                user: dict = Depends(auth.require_user),
               search: str | None = None,
               page: int = Query(1, ge=1, description="Номер страницы")
               ):
    is_authenticated = True

    items_per_page = 10
    skip = (page - 1) * items_per_page

    if search and search.strip():
        gauges, total_count = crud.search_gauges_strict(
            db,
            search_term=search,
            skip=skip,
            limit=items_per_page
        )
    else:
        gauges, total_count = crud.get_gauges_with_pagination(
            db,
            skip=skip,
            limit=items_per_page
        )

    # Вычисляем общее количество страниц
    total_pages = math.ceil(total_count / items_per_page) if total_count > 0 else 1

    user_full_names = {}

    for gauge in gauges:
        if gauge.by_user not in user_full_names:
            user_full_names[gauge.by_user] = crud.get_full_name_by_id(db, gauge.by_user)
    return templates.TemplateResponse('base.html', {'request': request,
                                                    "search_query": search,
                                                    "current_page": page,
                                                    "total_pages": total_pages,
                                                    "total_count": total_count,
                                                    "is_authenticated": is_authenticated,
                                                    'full_name': user['full_name'],
                                                    'role': user['role'],
                                                    'gauges': gauges,
                                                    'user_names': user_full_names})


@app.get("/form/", response_class=HTMLResponse)
async def show_form(request: Request,
                    user: dict = Depends(auth.require_kip)):
    return templates.TemplateResponse("form.html", {"request": request})


@app.get('/delete-form/{gauge_id}', response_class=HTMLResponse)
async def delete_form(request: Request,
                      gauge_id: int,
                      user: dict = Depends(auth.require_master),
                      db: Session = Depends(get_db),
                      ):
    gauge = crud.read_gauge(db, gauge_id)
    user_full_name = crud.get_full_name_by_id(db, gauge.by_user)
    return templates.TemplateResponse('gauge.html', {'request': request,
                                                    'gauge': gauge,
                                                    'full_name': user_full_name})


@app.post("/delete-gauge/{gauge_id}")
async def delete_gauge(request: Request,
        gauge_id: int,
        db: Session = Depends(get_db),
        user_role: str = Depends(auth.require_master)
):
    crud.delete_gauge(db, gauge_id)
    return templates.TemplateResponse('success-delete.html', {'request': request})


@app.get('/edit-gauge/{gauge_id}', response_class=HTMLResponse)
async def edit_gauge(request: Request,
                     gauge_id: int,
                     user: dict = Depends(auth.require_master),
                     db: Session = Depends(get_db)):

    gauge = crud.read_gauge(db, gauge_id)
    return templates.TemplateResponse(
        "edit_gauge.html",
        {"request": request, "gauge": gauge}
    )


@app.post("/update-gauge/{gauge_id}")
async def update_gauge_endpoint(
        gauge_id: int,
        request: Request,
        db: Session = Depends(get_db),
        title: str = Form(...),
        view: str = Form(...),
        type: str = Form(...),
        min: float = Form(...),
        max: float = Form(...),
        measure_unit: str = Form(...),
        low_low: str = Form(...),
        low: str = Form(...),
        high: str = Form(...),
        high_high: str = Form(...),
        description: str = Form(...),
        system: str = Form(...),
        tag: str = Form(...),
        device: str = Form(...),
        verification_date: date = Form(...),
        user: dict = Depends(auth.require_master)
):

    gauge_update = schemas.GaugeUpdate(
        device=device,
        title=title,
        view=view,
        type=type,
        min=min,
        max=max,
        measure_unit=measure_unit,
        low_low=low_low,
        low=low,
        high=high,
        high_high=high_high,
        description=description,
        system=system,
        verification_date=verification_date,
        tag=tag
    )

    crud.update_gauge(db, gauge_id, gauge_update)

    return RedirectResponse(url='/', status_code=303)


@app.get('/form-login/', response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@app.get('/logout/', response_class=HTMLResponse)
async def logout():
    response = RedirectResponse(url='/')
    response.delete_cookie(config.JWT_ACCESS_COOKIE_NAME)
    return response


@app.get('/register-kip')
async def register_new_kip(request: Request,
                           user: dict = Depends(auth.require_master)):
    return templates.TemplateResponse('register_kip.html', {'request': request})


@app.get('/edit-user/{user_id}')
async def edit_kip(request: Request,
                   user_id: int,
                   db: Session = Depends(get_db),
                   user: dict = Depends(auth.require_master)):
    user = crud.read_user(db, user_id)
    return templates.TemplateResponse('user_update.html', {'request': request,
                                                           'user': user})


@app.post('/user-update/{user_id}')
async def deactivate_user(user_id: int,
                          request: Request,
                          user: dict = Depends(auth.require_master),
                          db: Session = Depends(get_db),
                        full_name: str = Form(...),
                        active: bool = Form(...),
                        phone_number: str = Form(...)
                          ):
    user_update = schemas.UserUpdate(full_name=full_name,
                                     active=active,
                                     phone_number=phone_number)
    crud.update_user(db, user_id, user_update)
    return RedirectResponse(url='/users', status_code=303)


@app.post('/register')
async def register(request: Request,
                   full_name: str = Form(...),
                   password: str = Form(...),
                   phone_number: str = Form(...),
                   db: Session = Depends(get_db)):
    if crud.register_user(db, full_name, password, phone_number, role='кип'):
        return templates.TemplateResponse('success-user-create.html', {'request': request})
    return templates.TemplateResponse('register_kip.html', {'request': request,
                                                            'error': 'Пользователь с таким ФИО уже существует'})


@app.get('/users')
async def read_users(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse('users.html', {'request': request,
                                                     'users': crud.read_all_users(db)})


@app.post('/submit-login/')
async def handle_login(request: Request,
        full_name: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    try:
        if authenticate_user(full_name, password, db):
            token = security.create_access_token(uid='1234', data={'full_name': full_name})
            response = RedirectResponse(url='/', status_code=303)

            response.set_cookie(key=config.JWT_ACCESS_COOKIE_NAME,
                                value=token,
                                httponly=True,
                                path='/',
                max_age=3600,  # 1 час
                secure=False,  # True в production с HTTPS
                samesite="lax")

            return response
        return templates.TemplateResponse('login.html', {'request': request,
                                                         'error': 'Неверное ФИО или пароль'})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/success-login/')
async def success_login(request: Request):
    return templates.TemplateResponse('success.html', {'request': request})


@app.post("/submit-form/")
async def handle_form(
        request: Request,
        title: str = Form(...),
        view: str = Form(...),
        type: str = Form(...),
        min: float = Form(...),
        max: float = Form(...),
        measure_unit: str = Form(...),
        low_low: str = Form(...),
        low: str = Form(...),
        high: str = Form(...),
        high_high: str = Form(...),
        description: str = Form(...),
        system: str = Form(...),
        tag: str = Form(...),
        device: str = Form(...),
        verification_date: str = Form(...),
        db: Session = Depends(get_db),
        my_access_token: str = Cookie(None, alias=config.JWT_ACCESS_COOKIE_NAME)
):
    full_name = get_user_info_from_token(my_access_token)

    try:
        db_gauge = models.Gauge(
            title=title,
            view=view,
            type=type,
            min=min,
            max=max,
            measure_unit=measure_unit,
            low_low=low_low,
            low=low,
            high=high,
            high_high=high_high,
            description=description,
            system=system,
            tag=tag,
            device=device,
            verification_date=verification_date,
            by_user=crud.get_user_id_by_name(db, full_name)
        )

        db.add(db_gauge)
        db.commit()
        db.refresh(db_gauge)

        # Перенаправляем на страницу успеха
        return RedirectResponse(url="/success/", status_code=303)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Страница успеха
@app.get("/success/", response_class=HTMLResponse)
async def success_page(request: Request):
    return templates.TemplateResponse('success-create.html', {'request': request})
