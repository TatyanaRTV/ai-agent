/**
 * Основной JavaScript для Елены
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎀 Елена AI Assistant загружен');
    
    // Инициализация компонентов
    initChat();
    initVoice();
    initUpload();
    initNotifications();
    
    // Обновление статуса
    updateStatus();
    
    // Автоматическое обновление каждые 30 секунд
    setInterval(updateStatus, 30000);
});

/**
 * Инициализация чата
 */
function initChat() {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!chatForm || !messageInput) return;
    
    // Отправка сообщения
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Добавление сообщения пользователя
        addMessage(message, 'user');
        messageInput.value = '';
        
        try {
            // Отправка на сервер
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.response) {
                // Имитация задержки для реализма
                setTimeout(() => {
                    addMessage(data.response, 'bot');
                }, 500);
            }
        } catch (error) {
            console.error('Chat error:', error);
            addMessage('Извините, произошла ошибка. Попробуйте еще раз.', 'bot');
        }
    });
    
    // Поддержка Enter для отправки (без Shift)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
    
    /**
     * Добавление сообщения в чат
     */
    function addMessage(text, sender) {
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message fade-in`;
        messageDiv.textContent = text;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * Инициализация голосового интерфейса
 */
function initVoice() {
    const voiceBtn = document.getElementById('voiceBtn');
    const voiceStatus = document.getElementById('voiceStatus');
    
    if (!voiceBtn) return;
    
    let isListening = false;
    let recognition = null;
    
    // Проверка поддержки Web Speech API
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        voiceBtn.disabled = true;
        voiceBtn.title = 'Голосовой ввод не поддерживается вашим браузером';
        return;
    }
    
    // Создание объекта распознавания речи
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    
    // Настройки
    recognition.lang = 'ru-RU';
    recognition.continuous = false;
    recognition.interimResults = false;
    
    // Обработчики событий
    recognition.onstart = function() {
        isListening = true;
        voiceBtn.classList.add('listening');
        voiceStatus.textContent = '🎤 Слушаю...';
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        
        // Отправка распознанного текста в чат
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = transcript;
            
            // Автоматическая отправка
            const chatForm = document.getElementById('chatForm');
            if (chatForm) {
                setTimeout(() => {
                    chatForm.dispatchEvent(new Event('submit'));
                }, 100);
            }
        }
    };
    
    recognition.onend = function() {
        isListening = false;
        voiceBtn.classList.remove('listening');
        voiceStatus.textContent = '🎤 Нажмите для голосового ввода';
    };
    
    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        voiceStatus.textContent = '❌ Ошибка распознавания';
    };
    
    // Обработчик кнопки
    voiceBtn.addEventListener('click', function() {
        if (isListening) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (error) {
                console.error('Failed to start recognition:', error);
                voiceStatus.textContent = '❌ Не удалось начать запись';
            }
        }
    });
}

/**
 * Инициализация загрузки файлов
 */
function initUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadStatus = document.getElementById('uploadStatus');
    
    if (!fileInput || !uploadBtn) return;
    
    uploadBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // Проверка размера (макс 50MB)
        if (file.size > 50 * 1024 * 1024) {
            showNotification('Файл слишком большой (макс 50MB)', 'error');
            return;
        }
        
        // Показать прогресс
        uploadProgress.style.display = 'block';
        uploadStatus.textContent = 'Загрузка...';
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                uploadStatus.textContent = '✅ Загружено!';
                showNotification('Файл успешно загружен', 'success');
                
                // Обработка файла в зависимости от типа
                if (file.type.startsWith('image/')) {
                    processImage(file, data);
                } else if (file.type.includes('pdf') || file.type.includes('document')) {
                    processDocument(file, data);
                } else if (file.type.startsWith('audio/')) {
                    processAudio(file, data);
                }
            } else {
                uploadStatus.textContent = '❌ Ошибка';
                showNotification(data.error || 'Ошибка загрузки', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            uploadStatus.textContent = '❌ Ошибка сети';
            showNotification('Ошибка сети', 'error');
        } finally {
            setTimeout(() => {
                uploadProgress.style.display = 'none';
                uploadStatus.textContent = '';
            }, 2000);
        }
    });
    
    /**
     * Обработка изображения
     */
    function processImage(file, data) {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = `Опиши это изображение: ${file.name}`;
            
            const chatForm = document.getElementById('chatForm');
            if (chatForm) {
                setTimeout(() => {
                    chatForm.dispatchEvent(new Event('submit'));
                }, 500);
            }
        }
    }
    
    /**
     * Обработка документа
     */
    function processDocument(file, data) {
        showNotification(`Документ ${file.name} загружен. Анализирую...`, 'info');
        
        // Запрос анализа документа
        fetch('/api/analyze-document', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: data.filename })
        })
        .then(response => response.json())
        .then(data => {
            if (data.summary) {
                addMessage(`Документ ${file.name} проанализирован. ${data.summary}`, 'bot');
            }
        })
        .catch(error => {
            console.error('Document analysis error:', error);
        });
    }
    
    /**
     * Обработка аудио
     */
    function processAudio(file, data) {
        showNotification(`Аудио ${file.name} загружено. Распознаю...`, 'info');
        
        // Запрос распознавания аудио
        fetch('/api/transcribe-audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: data.filename })
        })
        .then(response => response.json())
        .then(data => {
            if (data.text) {
                addMessage(`Распознанный текст: ${data.text}`, 'bot');
            }
        })
        .catch(error => {
            console.error('Audio transcription error:', error);
        });
    }
}

/**
 * Инициализация уведомлений
 */
function initNotifications() {
    // Создание контейнера для уведомлений
    const notificationContainer = document.createElement('div');
    notificationContainer.id = 'notificationContainer';
    notificationContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 300px;
    `;
    document.body.appendChild(notificationContainer);
}

/**
 * Показать уведомление
 */
function showNotification(message, type = 'info') {
    const notificationContainer = document.getElementById('notificationContainer');
    if (!notificationContainer) return;
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.innerHTML = `
        ${getNotificationIcon(type)} ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    notificationContainer.appendChild(notification);
    
    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Получение иконки для уведомления
 */
function getNotificationIcon(type) {
    const icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    };
    return icons[type] || 'ℹ️';
}

/**
 * Обновление статуса системы
 */
async function updateStatus() {
    const statusElement = document.getElementById('systemStatus');
    if (!statusElement) return;
    
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        let statusHTML = '';
        
        if (data.status === 'online') {
            statusHTML = `
                <div class="d-flex align-items-center">
                    <span class="status-indicator status-online me-2"></span>
                    <span>Онлайн</span>
                    <small class="text-muted ms-2">${data.connected_clients} подключений</small>
                </div>
            `;
        } else {
            statusHTML = `
                <div class="d-flex align-items-center">
                    <span class="status-indicator status-offline me-2"></span>
                    <span>Офлайн</span>
                </div>
            `;
        }
        
        statusElement.innerHTML = statusHTML;
    } catch (error) {
        console.error('Status update error:', error);
    }
}

/**
 * Управление темами (темная/светлая)
 */
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('elena-theme', newTheme);
    
    showNotification(`Тема изменена на ${newTheme === 'dark' ? 'темную' : 'светлую'}`, 'info');
}

/**
 * Копирование текста в буфер обмена
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Скопировано в буфер обмена', 'success');
    }).catch(err => {
        console.error('Copy failed:', err);
        showNotification('Не удалось скопировать', 'error');
    });
}

/**
 * Форматирование даты
 */
function formatDate(date) {
    return new Date(date).toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Проверка подключения к интернету
 */
function checkInternetConnection() {
    if (!navigator.onLine) {
        showNotification('Нет подключения к интернету', 'warning');
        return false;
    }
    return true;
}

// Экспорт функций для использования в других модулях
window.ElenaAI = {
    showNotification,
    copyToClipboard,
    formatDate,
    toggleTheme
};