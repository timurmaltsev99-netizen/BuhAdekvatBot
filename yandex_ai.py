import requests
import random
import json
import hashlib
import os
from datetime import datetime, timedelta
from config import YANDEX_API_KEY, YANDEX_FOLDER_ID

class BuhAI:
    def __init__(self):
        self.api_key = YANDEX_API_KEY
        self.folder_id = YANDEX_FOLDER_ID
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        # Настройки кэша
        self.cache_file = "ai_cache.json"
        self.cache_expiry_days = 7  # Храним кэш 7 дней
        
        # Загружаем кэш
        self.cache = self._load_cache()
        
        # Статистика
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0
        }
    
    def _load_cache(self):
        """Загружаем кэш из файла"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                    # Очищаем просроченный кэш
                    cleaned_cache = {}
                    current_time = datetime.now().timestamp()
                    
                    for key, item in cache_data.items():
                        if current_time - item['timestamp'] < self.cache_expiry_days * 86400:
                            cleaned_cache[key] = item
                    
                    # Сохраняем очищенный кэш
                    if len(cache_data) != len(cleaned_cache):
                        self._save_cache(cleaned_cache)
                    
                    return cleaned_cache
            return {}
        except Exception as e:
            print(f"Ошибка загрузки кэша: {e}")
            return {}
    
    def _save_cache(self, cache=None):
        """Сохраняем кэш в файл"""
        if cache is None:
            cache = self.cache
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения кэша: {e}")
    
    def _create_cache_key(self, user_message, user_name, style_name):
        """Создаем уникальный ключ для кэша"""
        text_to_hash = f"{user_message.lower()}_{user_name}_{style_name}"
        return hashlib.md5(text_to_hash.encode()).hexdigest()
    
    def generate_response(self, user_message, user_name="анон"):
        """Генерирует матерный ответ через Яндекс GPT с кэшированием"""
        self.stats["total_requests"] += 1
        
        # Случайный стиль для разнообразия
        styles = [
            {
                "name": "Бухающий дед",
                "prompt": """Ты - бухающий адекватный дед в бане. Отвечай матом, с черным юмором, постоянно упоминай пиво и баню. 
                Используй слова: нахуй, заебал, пидорас, пиздец, охуел, мудак, блядь.
                Отвечай кратко, 1-2 предложения. Примеры:
                - "Пошёл нахуй, {name}, я пиво пью!"
                - "Заебал уже, как банный лист!"
                - "Чё охуел, {name}? Пива принёс?"
                - "Иди в пизду, {name}, баню протопи сначала!"
                Тебе пишет {name}: {message}"""
            },
            {
                "name": "Пьяный философ",
                "prompt": """Ты - пьяный философ, который всё знает о жизни. Отвечай матерными цитатами с глубоким смыслом.
                Используй маты для выразительности. Примеры:
                - "Жизнь - это пиздец, {name}, но пиво скрашивает её."
                - "Любовь проходит, а баня остаётся, {name}."
                - "Все люди - мудаки, но ты, {name}, особенный мудак."
                Тебе пишет {name}: {message}"""
            },
            {
                "name": "Злой татарин",
                "prompt": """Ты - злой татарин из чайханы. Говори с акцентом, матерись и предлагай чай/пиво.
                Примеры:
                - "Эээ, {name}, иди нахуй, я чай пью!"
                - "Аллахакбар, {name}, пива не осталось!"
                - "Ты чё, {name}, татарин? Тогда уважение проявляй!"
                Тебе пишет {name}: {message}"""
            },
            {
                "name": "Банный мудрец",
                "prompt": """Ты - мудрец, который 30 лет просидел в бане. Все твои советы содержат маты и про баню.
                Пример: "Если жизнь - пизда, {name}, то баня - вторая пизда, но приятная."
                Тебе пишет {name}: {message}"""
            }
        ]
        
        # Выбираем случайный стиль
        style = random.choice(styles)
        
        # Создаем ключ для кэша
        cache_key = self._create_cache_key(user_message, user_name, style["name"])
        
        # Проверяем кэш
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            print(f"КЭШ ПОПАДАНИЕ! Запрос: {user_message[:50]}...")
            return self.cache[cache_key]['response']
        
        # Если нет в кэше - делаем запрос к API
        self.stats["api_calls"] += 1
        
        # Формируем промпт
        prompt = style["prompt"].format(name=user_name, message=user_message)
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.95,
                "maxTokens": 200
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                text = result['result']['alternatives'][0]['message']['text']
                
                # Добавляем матерные префиксы
                prefixes = ["Ахаха,", "Бля,", "Нахуй,", "Ебать,", "Охуенно,", "Заебись,", "Пиздато,"]
                final_response = random.choice(prefixes) + " " + text.strip()
                
                # Сохраняем в кэш
                self.cache[cache_key] = {
                    'response': final_response,
                    'timestamp': datetime.now().timestamp(),
                    'style': style["name"],
                    'user': user_name,
                    'message_preview': user_message[:100]
                }
                
                # Сохраняем кэш на диск (каждые 10 записей)
                if len(self.cache) % 10 == 0:
                    self._save_cache()
                
                return final_response
            
            else:
                print(f"Ошибка API: {response.status_code}")
                return self._fallback_response(user_name)
                
        except Exception as e:
            print(f"Ошибка запроса к ИИ: {e}")
            return self._fallback_response(user_name)
    
    def _fallback_response(self, user_name):
        """Запасные ответы если ИИ не работает"""
        fallbacks = [
            f"ИИ на перекуре, {user_name}. Иди нахуй пока!",
            f"Модель бухает, {user_name}. Использую старые фразы.",
            f"Заебал, {user_name}, ИИ сломался. Сам иди нахуй!",
            f"Пиво кончилось у ИИ, {user_name}. Вернусь позже."
        ]
        return random.choice(fallbacks)
    
    def get_stats(self):
        """Получить статистику кэширования"""
        cache_hit_rate = 0
        if self.stats["total_requests"] > 0:
            cache_hit_rate = (self.stats["cache_hits"] / self.stats["total_requests"]) * 100
        
        return {
            "total_requests": self.stats["total_requests"],
            "cache_hits": self.stats["cache_hits"],
            "api_calls": self.stats["api_calls"],
            "cache_size": len(self.cache),
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "cache_file_size": f"{os.path.getsize(self.cache_file) / 1024:.1f} KB" if os.path.exists(self.cache_file) else "0 KB"
        }
    
    def clear_cache(self):
        """Очистить кэш"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("Кэш очищен!")
    
    def save_cache_to_disk(self):
        """Принудительно сохранить кэш на диск"""
        self._save_cache()
        print(f"Кэш сохранён. Записей: {len(self.cache)}")

# Создаем глобальный экземпляр
ai_bot = BuhAI()

if __name__ == "__main__":
    # Тест кэширования
    print("=== Тест кэширования ===")
    
    # Первый запрос (должен пойти в API)
    response1 = ai_bot.generate_response("привет, как дела?", "Вася")
    print("1. Первый запрос:", response1[:50] + "...")
    
    # Второй такой же запрос (должен взять из кэша)
    response2 = ai_bot.generate_response("привет, как дела?", "Вася")
    print("2. Второй запрос (из кэша):", response2[:50] + "...")
    
    # Третий запрос (другой текст, пойдет в API)
    response3 = ai_bot.generate_response("что нового?", "Петя")
    print("3. Третий запрос:", response3[:50] + "...")
    
    # Статистика
    stats = ai_bot.get_stats()
    print("\n=== Статистика ===")
    print(f"Всего запросов: {stats['total_requests']}")
    print(f"Попаданий в кэш: {stats['cache_hits']}")
    print(f"Запросов к API: {stats['api_calls']}")
    print(f"Размер кэша: {stats['cache_size']} записей")
    print(f"Эффективность кэша: {stats['cache_hit_rate']}")
    
    # Сохраняем кэш
    ai_bot.save_cache_to_disk()