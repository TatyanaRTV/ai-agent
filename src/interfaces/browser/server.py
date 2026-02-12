"""
ВЕБ-СЕРВЕР ДЛЯ ЕЛЕНЫ (FASTAPI)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent.parent))

# ЛЕНИВЫЙ ИМПОРТ — агент загружается только когда нужен
def get_agent_class():
    from src.core.brain.agent import ElenaAgent
    return ElenaAgent

from src.utils.logging.logger import ElenaLogger

class WebInterface:
    """Веб-интерфейс для Елены"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.app = FastAPI(title="Елена AI Assistant")
        self.logger = ElenaLogger("web_interface")
        self.agent: Optional[Any] = None
        self.active_connections = []
        
        # Настройка статических файлов и шаблонов
        self.templates = Jinja2Templates(directory="templates")
        
        # Настройка маршрутов
        self._setup_routes()
        
    def _setup_routes(self):
        """Настройка маршрутов"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            return self.templates.TemplateResponse(
                "index.html",
                {"request": request, "title": "Елена AI Assistant"}
            )
            
        @self.app.get("/api/status")
        async def get_status():
            return JSONResponse({
                "status": "online",
                "agent": "Елена",
                "version": "1.0.0",
                "connected_clients": len(self.active_connections)
            })
            
        @self.app.post("/api/chat")
        async def chat(request: Request):
            try:
                data = await request.json()
                message = data.get("message", "")
                
                if not message:
                    return JSONResponse({"error": "No message provided"})
                    
                # Обработка сообщения агентом
                if self.agent:
                    response = await self.agent.process_query(message)
                else:
                    response = f"Елена: Я получила ваше сообщение: '{message}'"
                    
                return JSONResponse({
                    "response": response,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
            except Exception as e:
                self.logger.error(f"Chat error: {e}")
                return JSONResponse({"error": str(e)})
                
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                # Отправляем приветственное сообщение
                await websocket.send_json({
                    "type": "greeting",
                    "message": "Привет! Я Елена, ваш ИИ-помощник. Чем могу помочь?"
                })
                
                while True:
                    # Получаем сообщение от клиента
                    data = await websocket.receive_json()
                    message_type = data.get("type", "message")
                    
                    if message_type == "message":
                        user_message = data.get("message", "")
                        
                        if user_message:
                            self.logger.info(f"WebSocket message: {user_message}")
                            
                            if self.agent:
                                response = await self.agent.process_query(user_message)
                            else:
                                response = f"Елена: '{user_message}'"
                                
                            await websocket.send_json({
                                "type": "response",
                                "message": response,
                                "timestamp": asyncio.get_event_loop().time()
                            })
                            
                    elif message_type == "command":
                        command = data.get("command", "")
                        await self._handle_command(websocket, command)
                        
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                self.logger.info("WebSocket client disconnected")
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                await websocket.close()
                
    async def _handle_command(self, websocket: WebSocket, command: str):
        """Обработка команд"""
        commands = {
            "status": self._handle_status_command,
            "help": self._handle_help_command,
            "clear": self._handle_clear_command,
            "voice": self._handle_voice_command,
        }
        
        handler = commands.get(command)
        if handler:
            await handler(websocket)
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown command: {command}"
            })
            
    async def _handle_status_command(self, websocket: WebSocket):
        """Обработка команды статуса"""
        status_info = {
            "agent": "Елена",
            "status": "active" if self.agent else "inactive",
            "memory_usage": "0MB",
            "connected_clients": len(self.active_connections),
            "uptime": "0 seconds"
        }
        
        await websocket.send_json({
            "type": "status",
            "data": status_info
        })
        
    async def _handle_help_command(self, websocket: WebSocket):
        """Обработка команды помощи"""
        help_text = """
Доступные команды:
• /status - статус системы
• /help - эта справка
• /clear - очистка чата
• /voice - голосовой режим

Просто отправьте сообщение, и я отвечу!
        """.strip()
        
        await websocket.send_json({
            "type": "help",
            "message": help_text
        })
        
    async def _handle_clear_command(self, websocket: WebSocket):
        """Обработка команды очистки"""
        await websocket.send_json({
            "type": "clear",
            "message": "Чат очищен"
        })
        
    async def _handle_voice_command(self, websocket: WebSocket):
        """Обработка голосовой команды"""
        await websocket.send_json({
            "type": "info",
            "message": "Голосовой режим пока не доступен через веб-интерфейс"
        })
        
    def initialize_agent(self):
        """Инициализация ИИ-агента"""
        try:
            AgentClass = get_agent_class()
            self.agent = AgentClass()
            self.logger.info("ИИ-агент инициализирован")
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            self.agent = None
            
    async def run(self):
        """Запуск веб-сервера"""
        self.logger.info(f"Starting web server on {self.host}:{self.port}")
        
        self.initialize_agent()
        
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        await server.serve()
        
    def run_sync(self):
        """Синхронный запуск"""
        import asyncio
        asyncio.run(self.run())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Web interface for Elena AI")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    
    args = parser.parse_args()
    
    web_interface = WebInterface(host=args.host, port=args.port)
    web_interface.run_sync()