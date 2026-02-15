#!/usr/bin/env python3
# Путь: /mnt/ai_data/ai-agent/src/security/auth.py
"""
Модуль безопасности и аутентификации Елены
Управляет доступом, шифрованием и безопасностью данных
"""

import hashlib
import jwt
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger


class Authenticator:
    """
    Класс для аутентификации и управления безопасностью
    """

    def __init__(self, config):
        """
        Инициализация модуля безопасности

        Args:
            config: словарь с конфигурацией
        """
        self.config = config

        # Пути для хранения данных безопасности
        self.security_dir = Path(config["paths"]["data"]) / "security"
        self.security_dir.mkdir(parents=True, exist_ok=True)

        # Файлы
        self.key_file = self.security_dir / "key.bin"
        self.users_file = self.security_dir / "users.json"
        self.tokens_file = self.security_dir / "tokens.json"

        # Инициализация
        self.secret_key = self._get_or_create_key()
        self.users = self._load_users()
        self.active_tokens = self._load_tokens()

        # Статистика
        self.auth_attempts = {}

        logger.info("🔒 Модуль безопасности инициализирован")

    def _get_or_create_key(self):
        """Получение или создание ключа шифрования"""
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                key = f.read()
            logger.debug("🔑 Ключ шифрования загружен")
            return key
        else:
            # Создаём новый ключ
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            logger.info("🔑 Создан новый ключ шифрования")
            return key

    def _load_users(self):
        """Загрузка пользователей из файла"""
        if self.users_file.exists():
            try:
                with open(self.users_file, "r") as f:
                    users = json.load(f)
                logger.debug(f"👥 Загружено {len(users)} пользователей")
                return users
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки пользователей: {e}")
                return {}
        else:
            # Создаём администратора по умолчанию
            default_users = {
                "admin": {
                    "password_hash": self._hash_password("admin123"),  # Изменить при первом входе!
                    "role": "admin",
                    "created": datetime.now().isoformat(),
                    "last_login": None,
                }
            }
            self._save_users(default_users)
            logger.warning("⚠️ Создан пользователь admin с паролем по умолчанию")
            return default_users

    def _save_users(self, users=None):
        """Сохранение пользователей в файл"""
        if users is None:
            users = self.users

        with open(self.users_file, "w") as f:
            json.dump(users, f, indent=2)

    def _load_tokens(self):
        """Загрузка активных токенов"""
        if self.tokens_file.exists():
            try:
                with open(self.tokens_file, "r") as f:
                    tokens = json.load(f)
                return tokens
            except:
                return {}
        return {}

    def _save_tokens(self):
        """Сохранение активных токенов"""
        with open(self.tokens_file, "w") as f:
            json.dump(self.active_tokens, f, indent=2)

    def _hash_password(self, password: str, salt=None):
        """
        Хеширование пароля

        Args:
            password: пароль
            salt: соль (если не указана, создаётся новая)

        Returns:
            строка с солью и хешем
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # Используем PBKDF2HMAC для усиления
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        return f"{salt}${key.decode()}"

    def _verify_password(self, password: str, password_hash: str):
        """Проверка пароля"""
        try:
            salt, hash_value = password_hash.split("$")
            expected_hash = self._hash_password(password, salt)
            return expected_hash == password_hash
        except:
            return False

    def create_user(self, username: str, password: str, role: str = "user"):
        """
        Создание нового пользователя

        Args:
            username: имя пользователя
            password: пароль
            role: роль (admin/user)

        Returns:
            bool: успешно или нет
        """
        if username in self.users:
            logger.warning(f"⚠️ Пользователь {username} уже существует")
            return False

        self.users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
            "created": datetime.now().isoformat(),
            "last_login": None,
            "failed_attempts": 0,
        }

        self._save_users()
        logger.info(f"👤 Создан пользователь: {username} (роль: {role})")
        return True

    def authenticate(self, username: str, password: str, ip_address: str = None):
        """
        Аутентификация пользователя

        Args:
            username: имя пользователя
            password: пароль
            ip_address: IP адрес для логирования

        Returns:
            tuple: (success, token, user_data)
        """
        # Проверка на блокировку по IP
        if ip_address:
            if ip_address in self.auth_attempts:
                attempts = self.auth_attempts[ip_address]
                if attempts["count"] >= 5:
                    time_since = datetime.now() - datetime.fromisoformat(attempts["last"])
                    if time_since < timedelta(minutes=15):
                        logger.warning(f"🚫 IP {ip_address} временно заблокирован")
                        return False, None, None

        # Проверка пользователя
        if username not in self.users:
            logger.warning(f"⚠️ Попытка входа несуществующего пользователя: {username}")
            self._record_failed_attempt(ip_address)
            return False, None, None

        user = self.users[username]

        # Проверка блокировки пользователя
        if user.get("locked", False):
            logger.warning(f"🚫 Пользователь {username} заблокирован")
            return False, None, None

        # Проверка пароля
        if not self._verify_password(password, user["password_hash"]):
            logger.warning(f"⚠️ Неверный пароль для пользователя: {username}")

            # Увеличиваем счётчик неудачных попыток
            user["failed_attempts"] = user.get("failed_attempts", 0) + 1
            if user["failed_attempts"] >= 5:
                user["locked"] = True
                logger.warning(f"🔒 Пользователь {username} заблокирован (5 неудачных попыток)")

            self._save_users()
            self._record_failed_attempt(ip_address)

            return False, None, None

        # Успешная аутентификация
        user["last_login"] = datetime.now().isoformat()
        user["failed_attempts"] = 0
        user["locked"] = False
        self._save_users()

        # Создаём токен
        token = self._create_token(username, user["role"])

        # Сохраняем токен
        self.active_tokens[token] = {
            "username": username,
            "role": user["role"],
            "created": datetime.now().isoformat(),
            "ip": ip_address,
        }
        self._save_tokens()

        logger.info(f"✅ Успешный вход: {username} с IP {ip_address}")

        return True, token, {"username": username, "role": user["role"], "last_login": user["last_login"]}

    def _record_failed_attempt(self, ip_address):
        """Запись неудачной попытки входа"""
        if not ip_address:
            return

        now = datetime.now()
        if ip_address not in self.auth_attempts:
            self.auth_attempts[ip_address] = {"count": 1, "first": now.isoformat(), "last": now.isoformat()}
        else:
            self.auth_attempts[ip_address]["count"] += 1
            self.auth_attempts[ip_address]["last"] = now.isoformat()

    def _create_token(self, username: str, role: str):
        """Создание JWT токена"""
        payload = {
            "username": username,
            "role": role,
            "exp": datetime.utcnow() + timedelta(days=1),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16),
        }

        # Используем наш секретный ключ для подписи
        secret = base64.urlsafe_b64decode(self.secret_key)
        token = jwt.encode(payload, secret, algorithm="HS256")

        return token

    def verify_token(self, token: str):
        """
        Проверка токена

        Args:
            token: JWT токен

        Returns:
            dict: данные пользователя или None
        """
        try:
            # Проверяем, активен ли токен
            if token not in self.active_tokens:
                logger.warning("⚠️ Попытка использования неактивного токена")
                return None

            # Проверяем подпись
            secret = base64.urlsafe_b64decode(self.secret_key)
            payload = jwt.decode(token, secret, algorithms=["HS256"])

            # Проверяем, не истёк ли
            exp = datetime.fromtimestamp(payload["exp"])
            if exp < datetime.utcnow():
                logger.warning("⚠️ Токен истёк")
                self.revoke_token(token)
                return None

            return {"username": payload["username"], "role": payload["role"]}

        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Токен истёк")
            self.revoke_token(token)
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка проверки токена: {e}")
            return None

    def revoke_token(self, token: str):
        """Отзыв токена"""
        if token in self.active_tokens:
            del self.active_tokens[token]
            self._save_tokens()
            logger.debug(f"🔓 Токен отозван")

    def revoke_all_user_tokens(self, username: str):
        """Отзыв всех токенов пользователя"""
        to_revoke = []
        for token, data in self.active_tokens.items():
            if data["username"] == username:
                to_revoke.append(token)

        for token in to_revoke:
            del self.active_tokens[token]

        self._save_tokens()
        logger.info(f"🔓 Отозвано {len(to_revoke)} токенов пользователя {username}")

    def change_password(self, username: str, old_password: str, new_password: str):
        """
        Смена пароля

        Args:
            username: имя пользователя
            old_password: старый пароль
            new_password: новый пароль

        Returns:
            bool: успешно или нет
        """
        if username not in self.users:
            return False

        user = self.users[username]

        if not self._verify_password(old_password, user["password_hash"]):
            return False

        # Меняем пароль
        user["password_hash"] = self._hash_password(new_password)
        user["password_changed"] = datetime.now().isoformat()

        self._save_users()

        # Отзываем все токены пользователя для безопасности
        self.revoke_all_user_tokens(username)

        logger.info(f"🔐 Пароль изменён для пользователя {username}")
        return True

    def encrypt_data(self, data: str):
        """Шифрование данных"""
        fernet = Fernet(self.secret_key)
        encrypted = fernet.encrypt(data.encode())
        return encrypted.decode()

    def decrypt_data(self, encrypted_data: str):
        """Дешифрование данных"""
        try:
            fernet = Fernet(self.secret_key)
            decrypted = fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"❌ Ошибка дешифрования: {e}")
            return None

    def check_permission(self, username: str, required_role: str):
        """
        Проверка прав пользователя

        Args:
            username: имя пользователя
            required_role: требуемая роль

        Returns:
            bool: есть ли права
        """
        if username not in self.users:
            return False

        user_role = self.users[username].get("role", "user")

        # Иерархия ролей: admin > user > guest
        role_hierarchy = {"admin": 3, "user": 2, "guest": 1}

        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

    def get_users_list(self, requester: str):
        """
        Получение списка пользователей (только для admin)

        Args:
            requester: запрашивающий пользователь

        Returns:
            список пользователей или None
        """
        if not self.check_permission(requester, "admin"):
            logger.warning(f"🚫 {requester} попытался получить список пользователей без прав")
            return None

        users_list = []
        for username, data in self.users.items():
            users_list.append(
                {
                    "username": username,
                    "role": data.get("role"),
                    "created": data.get("created"),
                    "last_login": data.get("last_login"),
                    "locked": data.get("locked", False),
                }
            )

        return users_list

    def delete_user(self, requester: str, username_to_delete: str):
        """
        Удаление пользователя (только для admin)

        Args:
            requester: запрашивающий пользователь
            username_to_delete: пользователь для удаления

        Returns:
            bool: успешно или нет
        """
        if not self.check_permission(requester, "admin"):
            logger.warning(f"🚫 {requester} попытался удалить пользователя без прав")
            return False

        if username_to_delete == "admin":
            logger.warning("🚫 Нельзя удалить администратора по умолчанию")
            return False

        if username_to_delete in self.users:
            del self.users[username_to_delete]
            self._save_users()
            self.revoke_all_user_tokens(username_to_delete)
            logger.info(f"🗑️ Пользователь {username_to_delete} удалён")
            return True

        return False

    def get_security_stats(self):
        """Получение статистики безопасности"""
        return {
            "total_users": len(self.users),
            "active_tokens": len(self.active_tokens),
            "blocked_ips": len([ip for ip, data in self.auth_attempts.items() if data["count"] >= 5]),
            "admin_count": len([u for u, d in self.users.items() if d.get("role") == "admin"]),
            "locked_users": len([u for u, d in self.users.items() if d.get("locked", False)]),
        }
