from fastapi import FastAPI, Request, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import os
import hashlib
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, declarative_base, Session

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

# Делаем флаги доступными глобально во всех шаблонах
templates.env.globals.update({
    "logo_exists": logo_exists,
    "title_exists": title_exists,
})

# Доступные изображения товаров, реально лежащие в static/images
available_product_images = {
    name for name in ("product1.jpg", "product2.jpg", "product3.jpg")
    if os.path.exists(BASE_DIR / "static" / "images" / name)
}

# --- SQLAlchemy: БД пользователей (SQLite) ---
DATABASE_URL = f"sqlite:///{BASE_DIR / 'app.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)

    # relationship not strictly needed for this simple app
    # cart_items = relationship("CartItem", back_populates="user")


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    # Item snapshot fields
    name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=True)
    size = Column(String(10), nullable=True)
    color = Column(String(20), nullable=True)
    image = Column(String(200), nullable=True)
    price = Column(Integer, nullable=False, default=0)
    base_product_id = Column(Integer, nullable=True)
    is_custom = Column(Boolean, nullable=False, default=False)


Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
products = [
    {"id": 1, "name": "Джиббитсы Nike Air", "price": 8500, "brand": "Nike", "size": "M", "color": "Черный", "image": "product1.jpg"},
    {"id": 2, "name": "Джиббитсы Adidas Ultra", "price": 7900, "brand": "Adidas", "size": "L", "color": "Белый", "image": "product2.jpg"},
    {"id": 3, "name": "Джиббитсы Puma RS", "price": 7200, "brand": "Puma", "size": "S", "color": "Красный", "image": "product3.jpg"},
    # Далее используем существующие изображения как плейсхолдеры, чтобы избежать 404
    {"id": 4, "name": "Джиббитсы Reebok Classic", "price": 6800, "brand": "Reebok", "size": "M", "color": "Синий", "image": "product1.jpg"},
    {"id": 5, "name": "Джиббитсы Nike Jordan", "price": 9200, "brand": "Nike", "size": "L", "color": "Черный", "image": "product2.jpg"},
    {"id": 6, "name": "Джиббитсы Adidas Superstar", "price": 8100, "brand": "Adidas", "size": "S", "color": "Белый", "image": "product3.jpg"},
    {"id": 7, "name": "Джиббитсы Puma Future", "price": 7500, "brand": "Puma", "size": "M", "color": "Серый", "image": "product1.jpg"},
    {"id": 8, "name": "Джиббитсы New Balance", "price": 6900, "brand": "New Balance", "size": "L", "color": "Синий", "image": "product2.jpg"},
    {"id": 9, "name": "Джиббитсы Vans Old Skool", "price": 6500, "brand": "Vans", "size": "S", "color": "Черный", "image": "product3.jpg"},
]

# Глобальные переменные для корзины и избранного
user_sessions = {}
custom_product_counter = 1000

def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    default = {"username": None, "favorites": [], "cart": []}
    session_data = user_sessions.get(session_id)
    if not session_data or not session_data.get("username"):
        return default
    username = session_data["username"]
    # Load cart from DB so that it persists across restarts
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return default
        items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
        cart = [
            {
                "id": item.id,
                "name": item.name,
                "brand": item.brand,
                "size": item.size,
                "color": item.color,
                "image": item.image,
                "price": item.price,
                "base_product_id": item.base_product_id,
                "is_custom": item.is_custom,
            }
            for item in items
        ]
        return {"username": username, "favorites": [], "cart": cart}
    finally:
        db.close()

def find_product_by_id(product_id: int) -> Optional[dict]:
    return next((p for p in products if p["id"] == product_id), None)

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

@app.get("/customize", response_class=HTMLResponse)
async def customize(request: Request):
    user_data = get_current_user(request)
    default_color = "#e74c3c"
    default_size = "M"

    # Формируем список базовых товаров для выбора (только с существующими изображениями, без дублей)
    base_products = []
    used_images = set()
    for p in products:
        img = p.get("image")
        if img in available_product_images and img not in used_images:
            base_products.append(p)
            used_images.add(img)
    if not base_products:
        base_products = products[:1]

    return templates.TemplateResponse("customize.html", {
        "request": request,
        "user": user_data["username"],
        "favorites": user_data["favorites"],
        "cart": user_data["cart"],
        "default_color": default_color,
        "default_size": default_size,
        "base_products": base_products,
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

    product = find_product_by_id(product_id)
    if not product:
        return RedirectResponse("/catalog?error=product_not_found", status_code=303)

    if product not in user_data["favorites"]:
        user_data["favorites"].append(product)
    
    response = RedirectResponse(url=request.headers.get('referer', '/catalog'), status_code=303)
    return response

@app.post("/add_cart")
async def add_cart(request: Request, product_id: int = Form(...)):
    user_data = get_current_user(request)
    if not user_data["username"]:
        return RedirectResponse("/login", status_code=303)

    product = find_product_by_id(product_id)
    if not product:
        return RedirectResponse("/catalog?error=product_not_found", status_code=303)

    # Persist to DB
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == user_data["username"]).first()
        if user:
            db_item = CartItem(
                user_id=user.id,
                name=product["name"],
                brand=product.get("brand"),
                size=product.get("size"),
                color=product.get("color"),
                image=product.get("image"),
                price=int(product.get("price", 0)),
                base_product_id=product.get("id"),
                is_custom=False,
            )
            db.add(db_item)
            db.commit()
    finally:
        db.close()

    response = RedirectResponse(url=request.headers.get('referer', '/catalog'), status_code=303)
    return response

@app.post("/remove_favorite")
async def remove_fav(request: Request, product_id: int = Form(...)):
    user_data = get_current_user(request)
    if not user_data["username"]:
        return RedirectResponse("/login", status_code=303)
    user_data["favorites"] = [item for item in user_data["favorites"] if item["id"] != product_id]
    
    response = RedirectResponse(url=request.headers.get('referer', '/favorites'), status_code=303)
    return response

@app.post("/remove_cart")
async def remove_cart(request: Request, product_id: int = Form(...)):
    user_data = get_current_user(request)
    if not user_data["username"]:
        return RedirectResponse("/login", status_code=303)
    # Here product_id represents cart item id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == user_data["username"]).first()
        if user:
            item = db.query(CartItem).filter(CartItem.id == product_id, CartItem.user_id == user.id).first()
            if item:
                db.delete(item)
                db.commit()
    finally:
        db.close()

    response = RedirectResponse(url=request.headers.get('referer', '/cart'), status_code=303)
    return response

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    if password != password_confirm:
        return RedirectResponse("/register?error=passwords_mismatch", status_code=303)
    # Проверка существующего пользователя
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return RedirectResponse("/register?error=username_taken", status_code=303)

    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    db_user = User(username=username, email=email, password_hash=password_hash)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Создаем сессию для пользователя
    import uuid
    session_id = str(uuid.uuid4())
    user_sessions[session_id] = {"username": username, "favorites": [], "cart": []}
    
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="session_id", value=session_id)
    return response

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if user:
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if user.password_hash == password_hash:
            import uuid
            session_id = str(uuid.uuid4())
            user_sessions[session_id] = {"username": username, "favorites": [], "cart": []}
            response = RedirectResponse("/", status_code=303)
            response.set_cookie(key="session_id", value=session_id)
            return response
    return RedirectResponse("/login?error=invalid_credentials", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    # Удаляем серверную сессию, если есть
    session_id = request.cookies.get("session_id")
    if session_id:
        user_sessions.pop(session_id, None)
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("session_id")
    return response

@app.post("/customize_add_cart")
async def customize_add_cart(
    request: Request,
    base_product_id: int = Form(...),
    color: str = Form(...),
    size: str = Form(...),
):
    user_data = get_current_user(request)
    if not user_data["username"]:
        return RedirectResponse("/login", status_code=303)

    allowed_sizes = {"S", "M", "L"}

    size_valid = size in allowed_sizes
    color_valid = isinstance(color, str) and color.startswith("#") and len(color) in {4, 7}
    base_product = find_product_by_id(base_product_id)
    base_valid = base_product is not None

    if not (base_valid and size_valid and color_valid):
        return RedirectResponse("/customize?error=invalid_params", status_code=303)

    # Создаём виртуальный товар и сохраняем в БД
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == user_data["username"]).first()
        if user:
            db_item = CartItem(
                user_id=user.id,
                name=f"{base_product['name']} — кастом ({size}, {color})",
                brand=base_product.get("brand", "Custom"),
                size=size,
                color=color,
                image=base_product.get("image", "product1.jpg"),
                price=int(base_product.get("price", 0)),
                base_product_id=base_product_id,
                is_custom=True,
            )
            db.add(db_item)
            db.commit()
    finally:
        db.close()
    response = RedirectResponse("/cart", status_code=303)
    return response
