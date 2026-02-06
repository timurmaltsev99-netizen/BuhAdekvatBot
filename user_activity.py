import time
import json
import os
from datetime import datetime, timedelta

class UserActivity:
    def __init__(self):
        self.activity_file = "user_activity.json"
        self.activity = self._load_activity()
        
        # Настройки
        self.cooldown_seconds = 60  # 1 минута между ответами одному пользователю
        self.max_messages_per_hour = 10  # Максимум ответов в час
    
    def _load_activity(self):
        try:
            if os.path.exists(self.activity_file):
                with open(self.activity_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def _save_activity(self):
        try:
            with open(self.activity_file, 'w', encoding='utf-8') as f:
                json.dump(self.activity, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения активности: {e}")
    
    def should_respond(self, user_id):
        """Проверяем, стоит ли отвечать пользователю"""
        current_time = time.time()
        user_id_str = str(user_id)
        
        # Получаем данные пользователя
        user_data = self.activity.get(user_id_str, {
            'last_response': 0,
            'responses_today': 0,
            'last_reset': current_time
        })
        
        # Сбрасываем счетчик если прошло больше часа
        if current_time - user_data['last_reset'] > 3600:
            user_data['responses_today'] = 0
            user_data['last_reset'] = current_time
        
        # Проверяем кд
        time_since_last = current_time - user_data['last_response']
        
        if time_since_last < self.cooldown_seconds:
            return False, f"КД: {int(self.cooldown_seconds - time_since_last)} сек"
        
        if user_data['responses_today'] >= self.max_messages_per_hour:
            return False, "Лимит ответов в час"
        
        # Обновляем данные
        user_data['last_response'] = current_time
        user_data['responses_today'] += 1
        self.activity[user_id_str] = user_data
        
        # Сохраняем каждые 10 записей
        if len(self.activity) % 10 == 0:
            self._save_activity()
        
        return True, "OK"
    
    def get_user_stats(self, user_id):
        """Получить статистику пользователя"""
        user_id_str = str(user_id)
        user_data = self.activity.get(user_id_str, {})
        
        responses_today = user_data.get('responses_today', 0)
        last_response = user_data.get('last_response', 0)
        
        if last_response > 0:
            time_since = time.time() - last_response
            time_str = f"{int(time_since // 60)} мин назад"
        else:
            time_str = "никогда"
        
        return {
            'responses_today': responses_today,
            'last_response': time_str,
            'limit': self.max_messages_per_hour,
            'cooldown': self.cooldown_seconds
        }
    
    def clear_activity(self):
        """Очистить статистику"""
        self.activity = {}
        if os.path.exists(self.activity_file):
            os.remove(self.activity_file)

# Глобальный экземпляр
user_activity = UserActivity()