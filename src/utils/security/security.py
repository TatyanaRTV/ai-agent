"""
СИСТЕМА БЕЗОПАСНОСТИ ЕЛЕНЫ
"""

import hashlib
import hmac
import secrets
import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import base64
from datetime import datetime, timedelta
import jwt

class SecurityManager:
    """Менеджер безопасности"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or self._generate_secret_key()
        self.fernet = Fernet(self._get_encryption_key())
        
    def _generate_secret_key(self) -> str:
        """Генерация секретного ключа"""
        return secrets.token_hex(32)
        
    def _get_encryption_key(self) -> bytes:
        """Получение ключа шифрования"""
        key = hashlib.sha256(self.secret_key.encode()).digest()
        return base64.urlsafe_b64encode(key)
        
    def encrypt_data(self, data: Any) -> str:
        """Шифрование данных"""
        if isinstance(data, dict):
            data_str = json.dumps(data, ensure_ascii=False)
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = str(data)
            
        encrypted = self.fernet.encrypt(data_str.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
        
    def decrypt_data(self, encrypted_data: str) -> Any:
        """Дешифрование данных"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
            decrypted = self.fernet.decrypt(encrypted_bytes).decode()
            
            # Пробуем распарсить JSON
            try:
                return json.loads(decrypted)
            except json.JSONDecodeError:
                return decrypted
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
            
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        )
        return f"{salt}${hash_obj.hex()}"
        
    def verify_password(self, password: str, hashed: str) -> bool:
        """Проверка пароля"""
        try:
            salt, hash_hex = hashed.split('$')
            new_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                100000
            ).hex()
            return hmac.compare_digest(new_hash, hash_hex)
        except:
            return False
            
    def generate_token(self, data: Dict[str, Any], expires_hours: int = 24) -> str:
        """Генерация JWT токена"""
        payload = data.copy()
        payload['exp'] = datetime.utcnow() + timedelta(hours=expires_hours)
        payload['iat'] = datetime.utcnow()
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Верификация JWT токена"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
    def secure_file(self, file_path: str, output_path: Optional[str] = None):
        """Защита файла шифрованием"""
        with open(file_path, 'rb') as f:
            data = f.read()
            
        encrypted = self.fernet.encrypt(data)
        
        if output_path is None:
            output_path = file_path + '.enc'
            
        with open(output_path, 'wb') as f:
            f.write(encrypted)
            
        return output_path
        
    def unsecure_file(self, encrypted_path: str, output_path: Optional[str] = None):
        """Расшифровка файла"""
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
            
        decrypted = self.fernet.decrypt(encrypted_data)
        
        if output_path is None:
            output_path = encrypted_path.replace('.enc', '')
            
        with open(output_path, 'wb') as f:
            f.write(decrypted)
            
        return output_path
        
    def create_checksum(self, data: Any) -> str:
        """Создание контрольной суммы"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            data_str = str(data)
            
        return hashlib.sha256(data_str.encode()).hexdigest()
        
    def verify_checksum(self, data: Any, checksum: str) -> bool:
        """Проверка контрольной суммы"""
        return self.create_checksum(data) == checksum
        
    def sanitize_input(self, input_str: str) -> str:
        """Санация ввода пользователя"""
        import html
        
        # Экранирование HTML
        sanitized = html.escape(input_str)
        
        # Удаление опасных паттернов
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+=',
            r'data:',
        ]
        
        import re
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
            
        return sanitized.strip()
        
    def check_password_strength(self, password: str) -> Dict[str, Any]:
        """Проверка сложности пароля"""
        score = 0
        feedback = []
        
        # Длина
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        else:
            feedback.append("Пароль должен быть не менее 8 символов")
            
        # Разнообразие символов
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if has_lower:
            score += 1
        if has_upper:
            score += 1
        if has_digit:
            score += 1
        if has_special:
            score += 1
            
        if not has_lower:
            feedback.append("Добавьте строчные буквы")
        if not has_upper:
            feedback.append("Добавьте заглавные буквы")
        if not has_digit:
            feedback.append("Добавьте цифры")
        if not has_special:
            feedback.append("Добавьте специальные символы")
            
        # Оценка
        if score >= 7:
            strength = "strong"
        elif score >= 5:
            strength = "medium"
        else:
            strength = "weak"
            
        return {
            "score": score,
            "strength": strength,
            "feedback": feedback,
            "length": len(password)
        }