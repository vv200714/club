from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from routers import auth, users, computers, bookings, tournaments, admin
from websocket.notifications import websocket_endpoint, manager
from database import engine, Base
from config import settings

# Создание таблиц в БД (для первого запуска)
Base.metadata.create_all(bind=engine)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создание приложения
app = FastAPI(
    title="Computer Club API",
    description="API for computer club mobile application",
    version="1.0.0"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(computers.router)
app.include_router(bookings.router)
app.include_router(tournaments.router)
app.include_router(admin.router)
from datetime import datetime

# WebSocket для уведомлений
@app.websocket("/ws/{user_id}")
async def websocket_route(websocket, user_id: int):
    await websocket_endpoint(websocket, user_id)

# Тестовый эндпоинт
@app.get("/")
async def root():
    return {
        "message": "Computer Club API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/auth - аутентификация",
            "/api/users - пользователи",
            "/api/computers - компьютеры",
            "/api/bookings - бронирования",
            "/api/tournaments - турниры",
            "/api/admin - админ панель",
            "/ws/{user_id} - WebSocket уведомления"
        ]
    }

# Эндпоинт для проверки здоровья
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }