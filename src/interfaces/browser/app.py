#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/interfaces/browser/app.py
"""Веб-интерфейс для Елены на FastAPI - финальная версия"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import json
import asyncio
from datetime import datetime
from loguru import logger
import threading
import uvicorn


class ConnectionManager:
    """Менеджер WebSocket соединений"""

    def __init__(self):
        self.active_connections = []
        self.connection_info = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        conn_id = client_id or f"conn_{len(self.active_connections)}"
        self.connection_info[id(websocket)] = {
            "id": conn_id,
            "connected_at": datetime.now().isoformat(),
            "messages_sent": 0,
        }
        logger.info(f"🌐 WebSocket подключён: {conn_id}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            conn_info = self.connection_info.get(id(websocket), {})
            self.active_connections.remove(websocket)
            if id(websocket) in self.connection_info:
                del self.connection_info[id(websocket)]
            logger.info(f"🌐 WebSocket отключён: {conn_info.get('id', 'unknown')}")

    async def send_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            if id(websocket) in self.connection_info:
                self.connection_info[id(websocket)]["messages_sent"] += 1
        except Exception as e:
            logger.error(f"❌ Ошибка отправки WebSocket сообщения: {e}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


class BrowserApp:
    """
    Веб-интерфейс для Елены - финальная версия
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
                "index.html", {"request": request, "agent_name": "Елена", "version": "1.0.0"}
            )

        @self.app.get("/api/status")
        async def get_status():
            """Получение статуса агента"""
            uptime = datetime.now() - self.start_time
            hours, remainder = divmod(uptime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)

            # Получаем информацию о памяти
            memory_usage = {}
            if hasattr(self.agent, "memory"):
                memory_usage = {
                    "short_term": len(getattr(self.agent.memory, "short_term", {})),
                    "vector_db": "active" if hasattr(self.agent.memory, "vector") else "inactive",
                }

            # Список компонентов
            components = list(self.agent.components.keys()) if hasattr(self.agent, "components") else []

            return JSONResponse(
                content={
                    "status": "active",
                    "agent_name": "Елена",
                    "version": "1.0.0",
                    "uptime": f"{int(hours)}ч {int(minutes)}м {int(seconds)}с",
                    "components": components,
                    "memory_usage": memory_usage,
                    "request_count": self.request_count,
                    "active_connections": len(self.manager.active_connections),
                }
            )

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket соединение для реального времени"""
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

                    try:
                        message_data = json.loads(data)
                        user_message = message_data.get("message", "")
                    except json.JSONDecodeError:
                        # Если не JSON, обрабатываем как обычный текст
                        user_message = data

                    logger.info(f"💬 [WebSocket {client_id}]: {user_message[:50]}...")

                    # Получаем настоящий ответ от Елены
                    conversation = None
                    if hasattr(self.agent, "components"):
                        conversation = self.agent.components.get("conversation")

                    if conversation:
                        response = conversation.generate_response(user_message)
                    else:
                        response = "Извини, я временно не могу ответить."

                    # Отправляем ответ
                    await self.manager.send_message(
                        json.dumps({"type": "response", "message": response, "timestamp": datetime.now().isoformat()}),
                        websocket,
                    )

            except WebSocketDisconnect:
                self.manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"❌ Ошибка WebSocket: {e}")
                self.manager.disconnect(websocket)

        @self.app.get("/api/history")
        async def get_history(limit: int = 10):
            """Получение истории сообщений"""
            # Здесь можно добавить загрузку истории из памяти
            return JSONResponse(content={"history": [], "total": 0})

        @self.app.get("/api/metrics")
        async def get_metrics():
            """Получение метрик производительности"""
            return JSONResponse(
                content={
                    "requests": self.request_count,
                    "active_connections": len(self.manager.active_connections),
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "components_status": {name: "active" for name in getattr(self.agent, "components", {}).keys()},
                }
            )

    def run(self, host="127.0.0.1", port=8080):
        """
        Запуск веб-сервера (для отдельного потока)
        """
        logger.info(f"🚀 Запуск веб-интерфейса на http://{host}:{port}")

        # Создаём и запускаем сервер
        config = uvicorn.Config(self.app, host=host, port=port, log_level="warning", reload=False)
        server = uvicorn.Server(config)

        try:
            server.run()
        except KeyboardInterrupt:
            logger.info("⏹️ Веб-интерфейс остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка веб-сервера: {e}")

    async def run_async(self):
        """Асинхронный запуск (для встраивания)"""
        config = uvicorn.Config(self.app, host="127.0.0.1", port=8080, log_level="warning", reload=False)
        server = uvicorn.Server(config)
        await server.serve()


# Функция для запуска в отдельном потоке
def start_browser_interface(config, agent):
    """
    Запуск веб-интерфейса в отдельном потоке

    Args:
        config: конфигурация
        agent: агент Елены
    """
    app = BrowserApp(config, agent)
    app.run()


# Создаём HTML шаблон при импорте
def create_html_template():
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
        
        .typing-indicator {
            display: flex;
            gap: 5px;
            padding: 12px 16px;
            background: white;
            border-radius: 18px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            max-width: 70%;
        }
        
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
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
                    <span class="info-value" id="version">1.0.0</span>
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
                addSystemMessage('🟢 Соединение установлено');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'welcome') {
                    addSystemMessage(data.message);
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
                } else {
                    addSystemMessage('❌ Не удалось подключиться к серверу');
                }
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket ошибка:', error);
            };
        }
        
        // Отправка сообщения
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
        
        // Добавление сообщения в чат
        function addMessage(text, sender) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender;
            
            const time = new Date().toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            messageDiv.innerHTML = `
                <div class="message-content">${escapeHtml(text)}</div>
                <div class="message-time">${time}</div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function addSystemMessage(text) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message system';
            messageDiv.style.textAlign = 'center';
            messageDiv.style.color = '#666';
            messageDiv.style.fontSize = '12px';
            messageDiv.style.margin = '10px';
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Обновление статуса
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uptime').textContent = data.uptime;
                    document.getElementById('version').textContent = data.version;
                    
                    const componentsList = document.getElementById('components');
                    componentsList.innerHTML = '';
                    data.components.forEach(comp => {
                        const li = document.createElement('li');
                        li.textContent = comp;
                        componentsList.appendChild(li);
                    });
                    
                    let memoryText = 'N/A';
                    if (data.memory_usage) {
                        if (data.memory_usage.short_term) {
                            memoryText = data.memory_usage.short_term + ' элементов';
                        }
                    }
                    document.getElementById('memory-usage').textContent = memoryText;
                    document.getElementById('request-count').textContent = data.request_count || 0;
                })
                .catch(error => {
                    console.error('Ошибка получения статуса:', error);
                });
        }
        
        // Инициализация
        window.onload = function() {
            connectWebSocket();
            updateStatus();
            setInterval(updateStatus, 5000);
            
            setTimeout(() => {
                addMessage('Здравствуйте! Я Елена, ваш персональный ассистент. Чем я могу помочь?', 'assistant');
            }, 500);
        };
        
        window.onbeforeunload = function() {
            if (ws) {
                ws.close();
            }
        };
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
