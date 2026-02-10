"""
ВЬЮХИ ДЛЯ ВЕБ-ИНТЕРФЕЙСА
"""

from typing import Dict, Any
from pathlib import Path

class WebViews:
    """Управление веб-страницами"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        
    def get_home_page(self, context: Dict[str, Any] = None) -> str:
        """Главная страница"""
        context = context or {}
        context.setdefault("title", "Елена AI Assistant")
        context.setdefault("version", "1.0.0")
        
        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{context['title']}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }}
                
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                
                .header h1 {{
                    font-size: 2.5em;
                    margin: 0;
                    color: #FF6B9D;
                }}
                
                .header p {{
                    font-size: 1.2em;
                    opacity: 0.9;
                }}
                
                .chat-container {{
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 20px;
                    max-height: 400px;
                    overflow-y: auto;
                }}
                
                .message {{
                    margin-bottom: 15px;
                    padding: 10px 15px;
                    border-radius: 15px;
                    max-width: 80%;
                }}
                
                .user-message {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin-left: auto;
                    color: white;
                }}
                
                .bot-message {{
                    background: rgba(255, 255, 255, 0.1);
                    margin-right: auto;
                }}
                
                .input-container {{
                    display: flex;
                    gap: 10px;
                }}
                
                input[type="text"] {{
                    flex: 1;
                    padding: 15px;
                    border: none;
                    border-radius: 25px;
                    background: rgba(255, 255, 255, 0.1);
                    color: white;
                    font-size: 1em;
                }}
                
                input[type="text"]::placeholder {{
                    color: rgba(255, 255, 255, 0.6);
                }}
                
                button {{
                    padding: 15px 30px;
                    border: none;
                    border-radius: 25px;
                    background: linear-gradient(135deg, #FF6B9D 0%, #FF8E53 100%);
                    color: white;
                    font-size: 1em;
                    cursor: pointer;
                    transition: transform 0.2s;
                }}
                
                button:hover {{
                    transform: translateY(-2px);
                }}
                
                .features {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }}
                
                .feature-card {{
                    background: rgba(255, 255, 255, 0.05);
                    padding: 20px;
                    border-radius: 15px;
                    text-align: center;
                }}
                
                .feature-icon {{
                    font-size: 2em;
                    margin-bottom: 10px;
                }}
                
                .status-bar {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 20px;
                    font-size: 0.9em;
                    opacity: 0.8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎀 Елена AI Assistant</h1>
                    <p>Универсальный ИИ-помощник с женским голосом</p>
                </div>
                
                <div class="chat-container" id="chatContainer">
                    <div class="message bot-message">
                        Привет! Я Елена, ваш ИИ-помощник. Чем могу помочь?
                    </div>
                </div>
                
                <div class="input-container">
                    <input type="text" id="messageInput" placeholder="Введите сообщение...">
                    <button onclick="sendMessage()">Отправить</button>
                </div>
                
                <div class="features">
                    <div class="feature-card">
                        <div class="feature-icon">🎤</div>
                        <h3>Голос</h3>
                        <p>Разговор женским голосом</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📄</div>
                        <h3>Документы</h3>
                        <p>Чтение всех форматов</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🖼️</div>
                        <h3>Изображения</h3>
                        <p>Анализ и описание</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🧠</div>
                        <h3>Память</h3>
                        <p>Запоминает всё важное</p>
                    </div>
                </div>
                
                <div class="status-bar">
                    <div>Версия: {context['version']}</div>
                    <div id="connectionStatus">🟢 Подключено</div>
                </div>
            </div>
            
            <script>
                let ws = new WebSocket('ws://' + window.location.host + '/ws');
                
                ws.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    addMessage(data.message, 'bot');
                }};
                
                ws.onopen = function() {{
                    document.getElementById('connectionStatus').textContent = '🟢 Подключено';
                }};
                
                ws.onclose = function() {{
                    document.getElementById('connectionStatus').textContent = '🔴 Отключено';
                }};
                
                function sendMessage() {{
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    
                    if (message) {{
                        addMessage(message, 'user');
                        ws.send(JSON.stringify({{type: 'message', message: message}}));
                        input.value = '';
                    }}
                }}
                
                function addMessage(text, sender) {{
                    const container = document.getElementById('chatContainer');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${{sender}}-message`;
                    messageDiv.textContent = text;
                    container.appendChild(messageDiv);
                    container.scrollTop = container.scrollHeight;
                }}
                
                // Enter key support
                document.getElementById('messageInput').addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        sendMessage();
                    }}
                }});
            </script>
        </body>
        </html>
        """