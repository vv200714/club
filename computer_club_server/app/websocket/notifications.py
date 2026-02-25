from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Управление WebSocket соединениями"""
    
    def __init__(self):
        # active_connections: {user_id: [websocket1, websocket2]}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Отправить сообщение конкретному пользователю"""
        
        if user_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Удаляем отключившиеся соединения
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast(self, message: dict, role: str = None):
        """Отправить сообщение всем пользователям (или по ролям)"""
        
        for user_id, connections in self.active_connections.items():
            # Здесь можно добавить фильтрацию по ролям
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    
    try:
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to notification server",
            "user_id": user_id
        })
        
        # Слушаем входящие сообщения
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.info(f"Received message from {user_id}: {message}")
                
                # Обработка разных типов сообщений
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {user_id}: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        
        # Уведомляем админов об отключении
        await manager.broadcast({
            "type": "user_disconnected",
            "user_id": user_id
        })