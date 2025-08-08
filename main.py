from fastapi import FastAPI, Request, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import os
from typing import Optional

# Получаем абсолютный путь к директории проекта
BASE_DIR = Path(__file__).parent

app = FastAPI()
# Используем абсолютный путь для статических файлов
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Создаем папки для статических файлов
(BASE_DIR / "static" / "images").mkdir(parents=True, exist_ok=True)

# Проверяем изображения
logo_exists = os.path.exists(BASE_DIR / "static" / "images" / "logo.png")
title_exists = os.path.exists(BASE_DIR / "static" / "images" / "title.png")

# База данных (в памяти)
users = {}
products = [
    {"id": 1, "name": "Джиббитсы Nike Air", "price": 8500, "brand": "Nike", "size": "M", "color": "Черный", "image": "product1.jpg"},
    {"id": 2, "name": "Джиббитсы Adidas Ultra", "price": 7900, "brand": "Adidas", "size": "L", "color": "Белый", "image": "product2.jpg"},
    {"id": 3, "name": "Джиббитсы Puma RS", "price": 7200, "brand": "Puma", "size": "S", "color": "Красный", "image": "product3.jpg"},
    {"id": 4, "name": "Джиббитсы Reebok Classic", "price": 6800, "brand": "Reebok", "size": "M", "color": "Синий", "image": "product4.jpg"},
    {"id": 5, "name": "Джиббитсы Nike Jordan", "price": 9200, "brand": "Nike", "size": "L", "color": "Черный", "image": "product5.jpg"},
    {"id": 6, "name": "Джиббитсы Adidas Superstar", "price": 8100, "brand": "Adidas", "size": "S", "color": "Белый", "image": "product6.jpg"},
    {"id": 7, "name": "Джиббитсы Puma Future", "price": 7500, "brand": "Puma", "size": "M", "color": "Серый", "image": "product7.jpg"},
    {"id": 8, "name": "Джиббитсы New Balance", "price": 6900, "brand": "New Balance", "size": "L", "color": "Синий", "image": "product8.jpg"},
    {"id": 9, "name": "Джиббитсы Vans Old Skool", "price": 6500, "brand": "Vans", "size": "S", "color": "Черный", "image": "product9.jpg"},
]

# Глобальные переменные для корзины и избранного
user_sessions = {}

def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    return user_sessions.get(session_id, {"username": None, "favorites": [], "cart": []})

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_data = get_current_user(request)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "logo_exists": logo_exists,
        "title_exists": title_exists,
        "user": user_data["username"],
        "favorites": user_data["favorites"],
        "cart": user_data["cart"]
    })

@app.get("/catalog", response_class=HTMLResponse)
async def catalog(request: Request):
    user_data = get_current_user(request)
    # Разбиваем товары на ряды по 3
    product_rows = [products[i:i + 3] for i in range(0, len(products), 3)]
    return templates.TemplateResponse("catalog.html", {
        "request": request,
        "product_rows": product_rows,
        "brands": list(set(p["brand"] for p in products)),
        "user": user_data["username"],
        "favorites": user_data["favorites"],
        "cart": user_data["cart"]
    })

@app.get("/favorites", response_class=HTMLResponse)
async def favs(request: Request):
    user_data = get_current_user(request)
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "favorites": user_data["favorites"],
        "user": user_data["username"],
        "cart": user_data["cart"]
    })

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    user_data = get_current_user(request)
    total = sum(item["price"] for item in user_data["cart"])
    return templates.TemplateResponse("cart.html", {
        "request": request,
        "cart": user_data["cart"],
        "total": total,
        "user": user_data["username"],
        "favorites": user_data["favorites"]
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    user_data = get_current_user(request)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "user": user_data["username"],
        "favorites": user_data["favorites"],
        "cart": user_data["cart"]
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user_data = get_current_user(request)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "user": user_data["username"],
        "favorites": user_data["favorites"],
        "cart": user_data["cart"]
    })

@app.post("/add_favorite")
async def add_fav(request: Request, product_id: int = Form(...)):
    user_data = get_current_user(request)
    if not user_data["username"]:
        return RedirectResponse("/login", status_code=303)
    
    product = next(p for p in products if p["id"] == product_id)
    if product not in user_data["favorites"]:
        user_data["favorites"].append(product)
    
    response = RedirectResponse(url=request.headers.get('referer', '/catalog'), status_code=303)
    return response

@app.post("/add_cart")
async def add_cart(request: Request, product_id: int = Form(...)):
    user_data = get_current_user(request)
    product = next(p for p in products if p["id"] == product_id)
    user_data["cart"].append(product)
    
    response = RedirectResponse(url=request.headers.get('referer', '/catalog'), status_code=303)
    return response

@app.post("/remove_favorite")
async def remove_fav(request: Request, product_id: int = Form(...)):
    user_data = get_current_user(request)
    user_data["favorites"] = [item for item in user_data["favorites"] if item["id"] != product_id]
    
    response = RedirectResponse(url=request.headers.get('referer', '/favorites'), status_code=303)
    return response

@app.post("/remove_cart")
async def remove_cart(request: Request, product_id: int = Form(...)):
    user_data = get_current_user(request)
    user_data["cart"] = [item for item in user_data["cart"] if item["id"] != product_id]
    
    response = RedirectResponse(url=request.headers.get('referer', '/cart'), status_code=303)
    return response

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...)
):
    if password != password_confirm:
        return RedirectResponse("/register?error=passwords_mismatch", status_code=303)
    if username in users:
        return RedirectResponse("/register?error=username_taken", status_code=303)
    
    users[username] = {"email": email, "password": password}
    
    # Создаем сессию для пользователя
    import uuid
    session_id = str(uuid.uuid4())
    user_sessions[session_id] = {"username": username, "favorites": [], "cart": []}
    
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="session_id", value=session_id)
    return response

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if users.get(username, {}).get("password") == password:
        # Создаем сессию для пользователя
        import uuid
        session_id = str(uuid.uuid4())
        user_sessions[session_id] = {"username": username, "favorites": [], "cart": []}
        
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(key="session_id", value=session_id)
        return response
    return RedirectResponse("/login?error=invalid_credentials", status_code=303)

@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("session_id")
    return response
