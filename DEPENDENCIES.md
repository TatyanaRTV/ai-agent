# Манифест зависимостей проекта Елена

## Критические связи между файлами

### bootstrap.py
- Зависит от: всех __init__.py, config_loader.py, logger.py
- Влияет на: _stop_services() → вызывает unload_model() во всех движках

### conversation_tools.py
- Зависит от: config.yaml (model, device)
- Влияет на: telegram/bot.py (через agent.components['conversation'])
- Важно: при смене модели (7B/14B) менять параметры temperature/repetition_penalty

### vision_engine.py
- Зависит от: config.yaml (device)
- Влияет на: _stop_services() (unload_model)
- Важно: при смене модели (Moondream/nanoLLaVA) менять весь метод _try_load

### telegram/bot.py
- Зависит от: agent.components, _processed_messages, _running
- Влияет на: основной поток (через _run_bot цикл)

### vector_memory.py
- Зависит от: sentence_transformers, chromadb
- Важно: всегда на CPU, device="cpu" обязателен

### audio_processor.py / audio_engine.py
- Зависит от: whisper
- Важно: везде использовать exist_ok=True

Перед любым изменением отвечать на вопросы:
# Чек-лист совместимости
1. Какой файл меняем? _______________
2. Какие файлы от него зависят? _______________
3. Какие параметры конфига затрагивает? _______________
4. Нужно ли менять _stop_services? _______________
5. Нужно ли менять импорты? _______________
6. Тестировать после изменения: 
   [ ] Запуск без ошибок
   [ ] Telegram не падает
   [ ] Голос работает
   [ ] Память чистится