#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/interfaces/app.py
"""
Веб-интерфейс для Елены на FastAPI
Позволяет общаться с агентом через браузер
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, cast
import asyncio
import json
from datetime import datetime
from pathlib import Path
import threading
import uvicorn

from loguru import logger


# Модели данных для API
class ChatMessage(BaseModel):
    """Модель сообщения чата"""

    message: str
    user_id: str = "anonymous"


class ChatResponse(BaseModel):
    """Модель ответа чата"""

    response: str
    timestamp: str
    message_id: str


class CommandRequest(BaseModel):
    """Модель команды"""

    command: str
    params: dict = {}


class StatusResponse(BaseModel):
    """Модель статуса"""

    status: str
    agent_name: str
    version: str
    uptime: str
    components: List[str]
    memory_usage: dict


# Класс для управления WebSocket соединениями
class ConnectionManager:
    """Менеджер WebSocket соединений"""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[int, Dict[str, Any]] = {}

    # Исправлено MyPy: добавлен -> None (строка 58)
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        conn_id = client_id or f"conn_{len(self.active_connections)}"
        self.connection_info[id(websocket)] = {
            "id": conn_id,
            "connected_at": datetime.now().isoformat(),
            "messages_sent": 0,
        }
        logger.info(f"🌐 WebSocket подключён: {conn_id}")

    # Исправлено MyPy: добавлен -> None (строка 59)
    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            conn_info = self.connection_info.get(id(websocket), {})
            self.active_connections.remove(websocket)
            if id(websocket) in self.connection_info:
                del self.connection_info[id(websocket)]
            logger.info(f"🌐 WebSocket отключён: {conn_info.get('id', 'unknown')}")

    # Исправлено MyPy: добавлен -> None
    async def send_message(self, message: str, websocket: WebSocket) -> None:
        try:
            await websocket.send_text(message)
            if id(websocket) in self.connection_info:
                self.connection_info[id(websocket)]["messages_sent"] += 1
        except Exception as e:
            logger.error(f"❌ Ошибка отправки WebSocket сообщения: {e}")

    # Исправлено MyPy: добавлен -> None
    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


# Основной класс веб-приложения
class BrowserApp:
    """
    Веб-интерфейс для Елены
    """

    def __init__(self, config, agent):
        """
        Инициализация веб-приложения

        Args:
            config: конфигурация
            agent: ссылка на агента Елены
        """
        self.config = config
        self.agent = agent
        self.app = FastAPI(title="Елена - ИИ Ассистент")
        self.manager = ConnectionManager()

        # Настройка шаблонов и статики
        templates_path = Path(__file__).parent / "templates"
        self.templates = Jinja2Templates(directory=str(templates_path))

        # Регистрация маршрутов
        self._register_routes()

        # Статистика
        self.start_time = datetime.now()
        self.request_count = 0

        logger.info("🌐 BrowserApp инициализирован")

    def _register_routes(self):
        """Регистрация всех маршрутов"""

        @self.app.get("/", response_class=HTMLResponse)
        async def get_index(request: Request):
            """Главная страница"""
            self.request_count += 1
            return self.templates.TemplateResponse(
                "index.html", {"request": request, "agent_name": "Елена", "version": "0.1.0"}
            )

        @self.app.get("/api/status", response_model=StatusResponse)
        async def get_status():
            """Получение статуса агента"""
            uptime = datetime.now() - self.start_time
            hours, remainder = divmod(uptime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)

            # Получаем информацию о памяти
            memory_usage = {}
            agent_any = cast(Any, self.agent)
            if hasattr(agent_any, "memory"):
                memory_usage = {
                    "short_term": len(getattr(agent_any.memory, "short_term", {})),
                    "vector_db": "active" if hasattr(agent_any.memory, "vector") else "inactive",
                }

            # Список компонентов
            components = list(agent_any.components.keys()) if hasattr(agent_any, "components") else []

            return StatusResponse(
                status="active",
                agent_name="Елена",
                version="0.1.0",
                uptime=f"{int(hours)}ч {int(minutes)}м {int(seconds)}с",
                components=components,
                memory_usage=memory_usage,
            )

        @self.app.post("/api/chat", response_model=ChatResponse)
        async def chat(message: ChatMessage):
            """
            Отправка сообщения агенту и получение ответа
            """
            try:
                logger.info(f"💬 [Веб] {message.user_id}: {message.message[:50]}...")

                agent_any = cast(Any, self.agent)
                # Генерируем ответ через агента
                if hasattr(agent_any, "conversation"):
                    response_text = agent_any.conversation.generate_response(message.message)
                else:
                    response_text = "Извини, я временно не могу обработать запрос."

                # Если есть голос, произносим (опционально)
                if hasattr(agent_any, "voice") and message.user_id != "anonymous":
                    agent_any.voice.speak(response_text)

                return ChatResponse(
                    response=response_text, timestamp=datetime.now().isoformat(), message_id=f"msg_{self.request_count}"
                )

            except Exception as e:
                logger.error(f"❌ Ошибка обработки чата: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/command")
        async def execute_command(command: CommandRequest):
            """
            Выполнение команды через tool_executor
            """
            try:
                agent_any = cast(Any, self.agent)
                if not hasattr(agent_any, "tool_executor"):
                    return JSONResponse(status_code=400, content={"error": "ToolExecutor не доступен"})

                # Преобразуем команду в действие
                action = {"type": command.command, **command.params}

                result = await agent_any.tool_executor.execute(action)

                return JSONResponse(content=result)

            except Exception as e:
                logger.error(f"❌ Ошибка выполнения команды: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """
            WebSocket соединение для реального времени
            """
            client_id = websocket.query_params.get("client_id", "anonymous")
            await self.manager.connect(websocket, client_id)

            try:
                # Отправляем приветственное сообщение
                await self.manager.send_message(
                    json.dumps(
                        {
                            "type": "welcome",
                            "message": "Добро пожаловать! Я Елена, ваш ассистент.",
                            "timestamp": datetime.now().isoformat(),
                        }
                    ),
                    websocket,
                )

                # Обрабатываем сообщения
                while True:
                    data = await websocket.receive_text()
                    agent_any = cast(Any, self.agent)

                    try:
                        message_data = json.loads(data)
                        user_message = message_data.get("message", "")

                        logger.info(f"💬 [WebSocket {client_id}]: {user_message[:50]}...")

                        # Генерируем ответ
                        if hasattr(agent_any, "conversation"):
                            response = agent_any.conversation.generate_response(user_message)
                        else:
                            response = "Извини, я временно недоступна."

                        # Отправляем ответ
                        await self.manager.send_message(
                            json.dumps(
                                {"type": "response", "message": response, "timestamp": datetime.now().isoformat()}
                            ),
                            websocket,
                        )

                    except json.JSONDecodeError:
                        # Если не JSON, обрабатываем как обычный текст
                        if hasattr(agent_any, "conversation"):
                            response = agent_any.conversation.generate_response(data)
                        else:
                            response = "Извини, я временно недоступна."

                        await self.manager.send_message(
                            json.dumps(
                                {"type": "response", "message": response, "timestamp": datetime.now().isoformat()}
                            ),
                            websocket,
                        )
            except WebSocketDisconnect:
                self.manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"❌ Ошибка WebSocket: {e}")
                self.manager.disconnect(websocket)

        @self.app.get("/api/history")
        async def get_history(limit: int = 10):
            """
            Получение истории сообщений
            """
            # Здесь можно добавить загрузку истории из памяти
            return JSONResponse(content={"history": [], "total": 0})

        @self.app.get("/api/metrics")
        async def get_metrics():
            """
            Получение метрик производительности
            """
            agent_any = cast(Any, self.agent)
            return JSONResponse(
                content={
                    "requests": self.request_count,
                    "active_connections": len(self.manager.active_connections),
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "components_status": {name: "active" for name in getattr(agent_any, "components", {}).keys()},
                }
            )

    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """
        Запуск веб-сервера (для отдельного потока)
        """
        logger.info(f"🚀 Запуск веб-интерфейса на http://{host}:{port}")

        # Создаём и запускаем сервер
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info", reload=False)
        server = uvicorn.Server(config)

        try:
            server.run()
        except KeyboardInterrupt:
            logger.info("⏹️ Веб-интерфейс остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка веб-сервера: {e}")

    async def run_async(self) -> None:
        """Асинхронный запуск (для встраивания)"""
        config = uvicorn.Config(self.app, host="127.0.0.1", port=8000, log_level="info", reload=False)
        server = uvicorn.Server(config)
        await server.serve()


# Функция для запуска в отдельном потоке
def start_browser_interface(config: Any, agent: Any) -> None:
    """
    Запуск веб-интерфейса в отдельном потоке

    Args:
        config: конфигурация
        agent: агент Елены
    """
    app = BrowserApp(config, agent)
    app.run()


# Шаблон HTML для главной страницы
def create_html_template() -> None:
    """Создание HTML шаблона"""
    html_content = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Елена - ИИ Ассистент</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #333;
        }

        .container {
            width: 90%;
            max-width: 1200px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            overflow: hidden;
        }
        
        .sidebar {
            width: 300px;
            background: #f8f9fa;
            padding: 20px;
            border-right: 1px solid #dee2e6;
            overflow-y: auto;
        }
        
        .sidebar-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .avatar {
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 40px;
        }
        
        .agent-name {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .agent-status {
            color: #28a745;
            font-size: 14px;
        }
        
        .info-box {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .info-box h3 {
            font-size: 16px;
            margin-bottom: 10px;
            color: #666;
        }
        
        .info-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .info-label {
            color: #666;
        }
        
        .info-value {
            font-weight: 600;
            color: #333;
        }
        
        .component-list {
            list-style: none;
        }
        
        .component-list li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
            font-size: 14px;
            display: flex;
            align-items: center;
        }
        
        .component-list li:before {
            content: "✅";
            margin-right: 8px;
            font-size: 12px;
        }
        
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-title {
            font-size: 18px;
            font-weight: 600;
        }
        
        .connection-status {
            font-size: 14px;
            padding: 5px 10px;
            border-radius: 20px;
        }
        
        .connected {
            background: #d4edda;
            color: #155724;
        }
        
        .disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        
        .messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
        }
        
        .message.user {
            align-items: flex-end;
        }
        
        .message.assistant {
            align-items: flex-start;
        }

        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .assistant .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .message-time {
            font-size: 11px;
            color: #999;
            margin-top: 4px;
        }
        
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
        }
        
        .message-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e1e1e1;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .message-input:focus {
            border-color: #667eea;
        }
        
        .send-button {
            width: 50px;
            height: 50px;
            border: none;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 20px;
            cursor: pointer;
            transition: transform 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .send-button:hover {
            transform: scale(1.1);
        }
        
        .command-buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        
        .command-btn {
            padding: 8px 15px;
            background: #e9ecef;
            border: none;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .command-btn:hover {
            background: #dee2e6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="avatar">👩</div>
                <div class="agent-name">Елена</div>
                <div class="agent-status" id="status">⚡ Онлайн</div>
            </div>
            
            <div class="info-box">
                <h3>📊 Системная информация</h3>
                <div class="info-item">
                    <span class="info-label">Версия:</span>
                    <span class="info-value">0.1.0</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Время работы:</span>
                    <span class="info-value" id="uptime">...</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Запросов:</span>
                    <span class="info-value" id="request-count">0</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Память:</span>
                    <span class="info-value" id="memory-usage">...</span>
                </div>
            </div>
            
            <div class="info-box">
                <h3>🔧 Активные компоненты</h3>
                <ul class="component-list" id="components">
                    <li>Загрузка...</li>
                </ul>
            </div>
            
            <div class="command-buttons">
                <button class="command-btn" onclick="sendCommand('status')">📊 Статус</button>
                <button class="command-btn" onclick="sendCommand('help')">❓ Помощь</button>
                <button class="command-btn" onclick="sendCommand('clear')">🧹 Очистить</button>
                <button class="command-btn" onclick="takeScreenshot()">📸 Скриншот</button>
            </div>
        </div>
        
        <div class="main">
            <div class="chat-header">
                <span class="chat-title">💬 Диалог с Еленой</span>
                <span class="connection-status connected" id="connection-status">● Подключено</span>
            </div>
            
            <div class="messages" id="messages"></div>
            
            <div class="input-area">
                <input type="text" class="message-input" id="message-input" 
                       placeholder="Напишите сообщение..." 
                       onkeypress="if(event.key==='Enter') sendMessage()">
                <button class="send-button" onclick="sendMessage()">➤</button>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket соединение
        let ws = null;
        let messageCount = 0;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        function connectWebSocket() {
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            
            ws.onopen = function() {
                console.log('WebSocket подключён');
                document.getElementById('connection-status').className = 'connection-status connected';
                document.getElementById('connection-status').textContent = '● Подключено';
                reconnectAttempts = 0;
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'welcome') {
                    addMessage(data.message, 'assistant');
                } else if (data.type === 'response') {
                    addMessage(data.message, 'assistant');
                }
            };
            
            ws.onclose = function() {
                console.log('WebSocket отключён');
                document.getElementById('connection-status').className = 'connection-status disconnected';
                document.getElementById('connection-status').textContent = '● Отключено';
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    setTimeout(connectWebSocket, 3000);
                }
            };
        }
        
        function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            if (message && ws && ws.readyState === WebSocket.OPEN) {
                addMessage(message, 'user');
                ws.send(JSON.stringify({message: message}));
                input.value = '';
                messageCount++;
                document.getElementById('request-count').textContent = messageCount;
            }
        }
        
        function addMessage(text, sender) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender;
            const time = new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
            messageDiv.innerHTML = `<div class="message-content">${text}</div><div class="message-time">${time}</div>`;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function sendCommand(cmd) {
            let message = '';
            switch(cmd) {
                case 'status': message = 'Покажи статус системы'; break;
                case 'help': message = 'Что ты умеешь?'; break;
                case 'clear': document.getElementById('messages').innerHTML = ''; return;
                default: message = cmd;
            }
            document.getElementById('message-input').value = message;
            sendMessage();
        }
        
        function takeScreenshot() {
            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: 'take_screenshot', params: {}})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) { addMessage('📸 Скриншот создан', 'assistant'); }
            });
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uptime').textContent = data.uptime;
                    const componentsList = document.getElementById('components');
                    componentsList.innerHTML = '';
                    data.components.forEach(comp => {
                        const li = document.createElement('li');
                        li.textContent = comp;
                        componentsList.appendChild(li);
                    });
                    if (data.memory_usage && data.memory_usage.short_term) {
                        document.getElementById('memory-usage').textContent = data.memory_usage.short_term + ' элементов';
                    }
                });
        }
        
        window.onload = function() { connectWebSocket(); updateStatus(); setInterval(updateStatus, 5000); };
    </script>
</body>
</html>"""

    # Создаём директорию и файл
    template_dir = Path("/mnt/ai_data/ai-agent/src/interfaces/browser/templates")
    template_dir.mkdir(parents=True, exist_ok=True)

    with open(template_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"📄 HTML шаблон создан: {template_dir}/index.html")


# Создаём HTML шаблон при импорте
create_html_template()
