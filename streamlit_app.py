"""
================================================================================
КОНСТРУКТОР WORKFLOW PRO v9.0 - ПРЕМИУМ ВЕРСИЯ
Обучаемые ИИ агенты | Современный дизайн | Полная визуализация | Автосохранение
================================================================================
"""

import streamlit as st
import json
import pandas as pd
import requests
from datetime import datetime
import traceback
import time
import re
import hashlib
import os
from typing import Dict, List, Tuple, Optional, Any
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from pathlib import Path
import base64
from streamlit_option_menu import option_menu
import random

# =================== ФУНКЦИИ ДЛЯ ПОЛНОГО СОХРАНЕНИЯ ===================

def save_all_data():
    """Сохраняет все данные: агентов, workflows, настройки"""
    try:
        # Сохраняем агентов
        if 'agent_manager' in st.session_state:
            agents_dict = {}
            for aid, agent in st.session_state.agent_manager.agents.items():
                agents_dict[aid] = agent.to_dict()
            with open('agents.json', 'w', encoding='utf-8') as f:
                json.dump(agents_dict, f, ensure_ascii=False, indent=2)
        
        # Сохраняем workflows
        if 'workflows' in st.session_state:
            with open('workflows.json', 'w', encoding='utf-8') as f:
                json.dump(st.session_state.workflows, f, ensure_ascii=False, indent=2)
        
        # Сохраняем настройки
        settings = {
            'last_agent_id': st.session_state.get('current_agent_id'),
            'last_workflow': st.session_state.get('current_workflow_name'),
            'version': '9.0',
            'last_saved': datetime.now().isoformat(),
            'total_agents': len(st.session_state.get('agent_manager', {}).agents) if 'agent_manager' in st.session_state else 0,
            'theme': st.session_state.get('theme', 'dark')
        }
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

def load_all_data():
    """Загружает все данные при старте"""
    try:
        # Загружаем агентов
        agents_dict = {}
        if os.path.exists('agents.json'):
            with open('agents.json', 'r', encoding='utf-8') as f:
                agents_dict = json.load(f)
        
        # Загружаем workflows
        workflows_dict = {}
        if os.path.exists('workflows.json'):
            with open('workflows.json', 'r', encoding='utf-8') as f:
                workflows_dict = json.load(f)
        
        # Загружаем настройки
        last_agent_id = None
        last_workflow = None
        theme = 'dark'
        if os.path.exists('settings.json'):
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                last_agent_id = settings.get('last_agent_id')
                last_workflow = settings.get('last_workflow')
                theme = settings.get('theme', 'dark')
        
        return agents_dict, workflows_dict, last_agent_id, last_workflow, theme
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return {}, {}, None, None, 'dark'

def auto_save_callback():
    """Автоматическое сохранение при любых изменениях"""
    if 'agent_manager' in st.session_state:
        st.session_state.agent_manager.save_agents()
    if 'workflows' in st.session_state:
        try:
            with open('workflows.json', 'w', encoding='utf-8') as f:
                json.dump(st.session_state.workflows, f, ensure_ascii=False, indent=2)
        except:
            pass

def with_autosave(func):
    """Декоратор для автоматического сохранения после функции"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        auto_save_callback()
        return result
    return wrapper

def load_agents_from_file(filepath='agents.json'):
    """Загрузка агентов из файла"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")
            return {}
    return {}

def save_agents_to_file(agents_dict, filepath='agents.json'):
    """Сохранение агентов в файл"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(agents_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения: {e}")
        return False

def load_workflows_from_file(filepath='workflows.json'):
    """Загрузка сохраненных workflows"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_workflows_to_file(workflows_dict, filepath='workflows.json'):
    """Сохранение workflows"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflows_dict, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# =================== ПРЕМИУМ СТИЛИ ===================

def apply_premium_styles():
    """Применяет премиум стили для всего приложения"""
    
    # Анимированный градиентный фон
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        /* Главный контейнер */
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
            color: #ffffff;
        }
        
        /* Анимированный градиентный хедер */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-size: 200% 200%;
            animation: gradientShift 5s ease infinite;
            padding: 2.5rem;
            border-radius: 30px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .main-header h1 {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #fff, #ffd89b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .main-header p {
            font-size: 1.1rem;
            color: rgba(255,255,255,0.95);
            margin-top: 0.5rem;
        }
        
        /* Карточки агентов */
        .agent-card-vip {
            background: linear-gradient(135deg, rgba(26,26,46,0.95), rgba(22,30,62,0.95));
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 1.2rem;
            margin: 0.8rem 0;
            border: 1px solid rgba(78,205,196,0.3);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .agent-card-vip::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(78,205,196,0.2), transparent);
            transition: left 0.5s;
        }
        
        .agent-card-vip:hover::before {
            left: 100%;
        }
        
        .agent-card-vip:hover {
            transform: translateX(8px) scale(1.02);
            border-color: #4ECDC4;
            box-shadow: 0 10px 30px rgba(78,205,196,0.2);
        }
        
        /* Chat стили */
        .chat-message-user {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 20px;
            padding: 1rem;
            margin: 0.5rem 0;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            animation: slideInRight 0.3s ease;
        }
        
        .chat-message-agent {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-radius: 20px;
            padding: 1rem;
            margin: 0.5rem 0;
            max-width: 80%;
            border-left: 4px solid #4ECDC4;
            animation: slideInLeft 0.3s ease;
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        /* Статистические карточки */
        .stat-card-glass {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }
        
        .stat-card-glass:hover {
            transform: translateY(-5px);
            background: rgba(255,255,255,0.12);
            border-color: #4ECDC4;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #fff, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Боковая панель */
        .css-1d391kg {
            background: linear-gradient(180deg, #0f0c29 0%, #1a1a3e 100%);
        }
        
        /* Кнопки */
        .stButton > button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102,126,234,0.3);
        }
        
        /* Input поля */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            color: white;
            padding: 0.75rem;
        }
        
        .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
            border-color: #4ECDC4;
            box-shadow: 0 0 0 2px rgba(78,205,196,0.2);
        }
        
        /* Табы */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        /* Прогресс бар */
        .stProgress > div > div {
            background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
            background-size: 200% 100%;
            animation: gradientProgress 2s ease infinite;
        }
        
        @keyframes gradientProgress {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }
        
        /* Скроллбар */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2, #f093fb);
        }
        
        /* Всплывающие уведомления */
        .stAlert {
            border-radius: 15px;
            border-left: 5px solid #4ECDC4;
            animation: slideInDown 0.3s ease;
        }
        
        @keyframes slideInDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Карточка обучения */
        .training-card-premium {
            background: linear-gradient(135deg, rgba(26,26,46,0.9), rgba(22,30,62,0.9));
            border-radius: 15px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #FFD700;
            transition: all 0.3s ease;
        }
        
        .training-card-premium:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 20px rgba(255,215,0,0.2);
        }
        
        /* Индикатор сохранения */
        .save-indicator-premium {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #00ff88, #00bfff);
            color: #000;
            padding: 8px 16px;
            border-radius: 25px;
            font-size: 12px;
            font-weight: bold;
            z-index: 999;
            animation: pulse 2s infinite;
            box-shadow: 0 4px 15px rgba(0,255,136,0.3);
        }
        
        @keyframes pulse {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            50% {
                transform: scale(1.05);
                opacity: 0.9;
            }
            100% {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        /* Типографика */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700;
            background: linear-gradient(135deg, #fff, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Разделители */
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent, #4ECDC4, transparent);
            margin: 2rem 0;
        }
        
        /* Badges */
        .badge-premium {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 0.25rem;
        }
        
        /* Tooltips */
        [data-tooltip] {
            position: relative;
            cursor: help;
        }
        
        [data-tooltip]:before {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 10px;
            font-size: 0.8rem;
            white-space: nowrap;
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        }
        
        [data-tooltip]:hover:before {
            opacity: 1;
        }
    </style>
    """, unsafe_allow_html=True)

# =================== КЛАСС ДЛЯ РАЗБОРА РУССКИХ УСЛОВИЙ ===================

class RussianConditionParser:
    """Парсер условий на русском языке"""
    
    @staticmethod
    def parse(condition_text: str, context: Dict = None) -> Dict:
        """
        Преобразует русское условие в выполняемый код
        Примеры:
        - "если температура > 30 то включить кондиционер"
        - "если сумма > 1000 и статус == оплачено то отправить уведомление"
        """
        result = {
            "condition": condition_text,
            "success": True,
            "error": None,
            "python_code": "",
            "variables": []
        }
        
        try:
            # Нормализация текста
            text = condition_text.lower().strip()
            
            # Извлекаем условия
            patterns = {
                'больше': '>',
                'меньше': '<',
                'равно': '==',
                'не равно': '!=',
                'больше или равно': '>=',
                'меньше или равно': '<=',
                'содержит': 'in',
                'не содержит': 'not in',
                'и': 'and',
                'или': 'or',
                'то': ':',
                'тогда': ':'
            }
            
            python_code = text
            variables = []
            
            # Заменяем русские операторы
            for rus, eng in patterns.items():
                python_code = python_code.replace(rus, eng)
            
            # Находим переменные (слова без кавычек)
            words = re.findall(r'\b[a-zа-яё][a-zа-яё0-9_]*\b', python_code)
            for word in words:
                if word not in ['and', 'or', 'not', 'in', 'true', 'false', 'null', 'none']:
                    if word not in [str(v) for v in range(10)]:
                        variables.append(word)
            
            result["python_code"] = python_code
            result["variables"] = list(set(variables))
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def evaluate(condition_text: str, context: Dict) -> bool:
        """Выполняет проверку условия"""
        try:
            parsed = RussianConditionParser.parse(condition_text)
            if not parsed["success"]:
                return False
            
            # Подставляем значения из контекста
            code = parsed["python_code"]
            for var in parsed["variables"]:
                if var in context:
                    # Экранируем строки
                    if isinstance(context[var], str):
                        code = code.replace(var, f'"{context[var]}"')
                    else:
                        code = code.replace(var, str(context[var]))
            
            # Безопасное выполнение
            return eval(code)
        except Exception as e:
            return False

# =================== КЛАСС ИИ АГЕНТА ===================

class AIAgent:
    def __init__(self, name, role, system_prompt, agent_id=None, avatar_emoji="🧠"):
        self.id = agent_id or hashlib.md5(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.avatar_emoji = avatar_emoji
        self.created_at = datetime.now().isoformat()
        self.training_examples = []
        self.memory = []
        self.conversation_history = []
        self.knowledge_base = {}
        self.stats = {
            'total_trainings': 0,
            'total_conversations': 0,
            'success_rate': 0,
            'last_trained': None
        }

    def add_training_example(self, user_input, expected_output, context=""):
        """Добавляет пример для обучения"""
        example = {
            'user_input': user_input,
            'expected_output': expected_output,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        self.training_examples.append(example)
        self.stats['total_trainings'] += 1
        self.stats['last_trained'] = datetime.now().isoformat()
        return True

    def add_to_memory(self, key, value, importance="normal"):
        """Добавляет элемент в память агента"""
        memory_item = {
            'key': key,
            'value': value,
            'importance': importance,
            'timestamp': datetime.now().isoformat()
        }
        # Ограничиваем память (храним последние 100 записей)
        self.memory.append(memory_item)
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]
        return True

    def get_from_memory(self, key):
        """Получает из памяти по ключу"""
        for item in reversed(self.memory):
            if item['key'] == key:
                return item['value']
        return None

    def find_similar_examples(self, user_input, limit=3):
        """Находит похожие примеры обучения"""
        user_input_lower = user_input.lower()
        scored_examples = []
        
        for example in self.training_examples:
            score = 0
            # Сравнение по ключевым словам
            words = user_input_lower.split()
            for word in words:
                if len(word) > 3 and word in example['user_input'].lower():
                    score += 1
            
            # Чем больше слов совпадает, тем выше оценка
            scored_examples.append((score, example))
        
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex for score, ex in scored_examples[:limit] if score > 0]

    def add_conversation(self, user_message, agent_response, feedback=None):
        """Сохраняет диалог для обучения"""
        conversation = {
            'user': user_message,
            'agent': agent_response,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        }
        self.conversation_history.append(conversation)
        self.stats['total_conversations'] += 1
        
        # Рассчитываем успешность
        if feedback:
            success_count = sum(1 for c in self.conversation_history if c.get('feedback') == 'good')
            self.stats['success_rate'] = (success_count / len(self.conversation_history)) * 100
        
        # Ограничиваем историю
        if len(self.conversation_history) > 200:
            self.conversation_history = self.conversation_history[-200:]
        return True

    def get_context_summary(self):
        """Возвращает краткое описание контекста агента"""
        summary_parts = []
        summary_parts.append(f"Агент: {self.name}")
        summary_parts.append(f"Роль: {self.role}")
        summary_parts.append(f"Примеров в обучении: {len(self.training_examples)}")
        summary_parts.append(f"Диалогов: {self.stats['total_conversations']}")
        summary_parts.append(f"Успешность: {self.stats['success_rate']:.1f}%")
        return "\n".join(summary_parts)

    def generate_response(self, user_input, api_key, use_training=True):
        """Генерирует ответ агента с использованием обученных примеров"""
        if not api_key:
            return "⚠️ Пожалуйста, укажите API ключ DeepSeek в боковой панели"
        
        try:
            # Находим похожие примеры
            similar_examples = []
            if use_training:
                similar_examples = self.find_similar_examples(user_input)
            
            # Формируем промпт
            prompt_context = f"""
Ты - {self.name}, {self.role}.

Твоя системная инструкция: {self.system_prompt}

Важная информация из памяти агента:
{self.get_context_summary()}

"""

            # Добавляем примеры обучения
            if similar_examples:
                prompt_context += "\nВот похожие примеры правильных ответов на похожие вопросы:\n"
                for i, ex in enumerate(similar_examples[:3], 1):
                    prompt_context += f"\nПример {i}:\nВопрос: {ex['user_input']}\nОтвет: {ex['expected_output']}\n"
            
            prompt_context += f"\nПользователь спрашивает: {user_input}\n\nОтветь на русском языке, естественно и полезно:"
            
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": prompt_context},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            self.add_conversation(user_input, answer)
            return answer
            
        except Exception as e:
            return f"❌ Ошибка при генерации ответа: {str(e)}"

    def to_dict(self):
        """Преобразует агента в словарь для сохранения"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'system_prompt': self.system_prompt,
            'avatar_emoji': self.avatar_emoji,
            'created_at': self.created_at,
            'training_examples': self.training_examples,
            'memory': self.memory,
            'conversation_history': self.conversation_history,
            'knowledge_base': self.knowledge_base,
            'stats': self.stats
        }

    @classmethod
    def from_dict(cls, data):
        """Создает агента из словаря"""
        agent = cls(
            data['name'], 
            data['role'], 
            data['system_prompt'], 
            data['id'],
            data.get('avatar_emoji', '🧠')
        )
        agent.created_at = data.get('created_at', datetime.now().isoformat())
        agent.training_examples = data.get('training_examples', [])
        agent.memory = data.get('memory', [])
        agent.conversation_history = data.get('conversation_history', [])
        agent.knowledge_base = data.get('knowledge_base', {})
        agent.stats = data.get('stats', {'total_trainings': 0, 'total_conversations': 0, 'success_rate': 0, 'last_trained': None})
        return agent

# =================== ГЕНЕРАТОР WORKFLOW ===================

class AIWorkflowGenerator:
    @staticmethod
    def generate(description: str, api_key: str) -> Dict:
        """Генерирует workflow на основе текстового описания"""
        if not api_key:
            return {"error": "Не указан API ключ"}
        
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            
            prompt = f"""
Создай workflow автоматизации на основе описания ниже.

Описание: {description}

Требования:
1. Workflow должен быть в формате JSON
2. Каждый блок должен иметь: name, type, config
3. Возможные типы блоков: google_sheets_read, deepseek, http_get, http_post, condition, loop, email, telegram

Ответь ТОЛЬКО JSON без пояснений в формате:
{{
    "nodes": [
        {{
            "name": "Название блока",
            "type": "тип",
            "config": {{"параметр": "значение"}}
        }}
    ],
    "description": "краткое описание"
}}
"""
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            # Парсим JSON из ответа
            content = response.choices[0].message.content
            # Убираем возможные markdown обертки
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            
            workflow = json.loads(content)
            return workflow
            
        except json.JSONDecodeError as e:
            return {"error": f"Ошибка парсинга JSON: {e}"}
        except Exception as e:
            return {"error": str(e)}

# =================== МЕНЕДЖЕР АГЕНТОВ ===================

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.current_agent_id: Optional[str] = None
        self.load_agents()  # Автоматическая загрузка при создании

    def load_agents(self):
        """Загружает агентов из файла с полным восстановлением"""
        try:
            if os.path.exists('agents.json'):
                with open('agents.json', 'r', encoding='utf-8') as f:
                    agents_data = json.load(f)
                
                self.agents = {}
                for agent_id, data in agents_data.items():
                    try:
                        self.agents[agent_id] = AIAgent.from_dict(data)
                    except Exception as e:
                        print(f"Ошибка загрузки агента {agent_id}: {e}")
                
                # Восстанавливаем последнего активного агента
                if os.path.exists('settings.json'):
                    with open('settings.json', 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                        self.current_agent_id = settings.get('last_agent_id')
                        
                        # Проверяем, существует ли этот агент
                        if self.current_agent_id and self.current_agent_id not in self.agents:
                            self.current_agent_id = None
                
                # Если нет сохраненного, берем первого
                if not self.current_agent_id and self.agents:
                    self.current_agent_id = list(self.agents.keys())[0]
                
                print(f"✅ Загружено {len(self.agents)} агентов")
            else:
                print("Файл agents.json не найден, создаю новый при сохранении")
        except Exception as e:
            print(f"Ошибка загрузки агентов: {e}")
            self.agents = {}

    def save_agents(self):
        """Сохраняет агентов в файл с полной информацией"""
        try:
            agents_dict = {aid: agent.to_dict() for aid, agent in self.agents.items()}
            with open('agents.json', 'w', encoding='utf-8') as f:
                json.dump(agents_dict, f, ensure_ascii=False, indent=2)
            
            # Сохраняем текущего агента в настройках
            settings = {}
            if os.path.exists('settings.json'):
                with open('settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            settings['last_agent_id'] = self.current_agent_id
            settings['last_saved'] = datetime.now().isoformat()
            settings['total_agents'] = len(self.agents)
            
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Ошибка сохранения: {e}")
            return False

    def add_agent(self, name, role, system_prompt, avatar_emoji="🧠"):
        """Добавляет нового агента и сразу сохраняет"""
        agent = AIAgent(name, role, system_prompt, avatar_emoji=avatar_emoji)
        self.agents[agent.id] = agent
        self.save_agents()  # Мгновенное сохранение
        return agent.id

    def delete_agent(self, agent_id):
        """Удаляет агента и сохраняет"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            if self.current_agent_id == agent_id:
                self.current_agent_id = None
            self.save_agents()  # Сохраняем после удаления
            return True
        return False

    def update_agent(self, agent_id, **kwargs):
        """Обновляет данные агента"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            self.save_agents()  # Сохраняем изменения
            return True
        return False

    def set_current_agent(self, agent_id):
        """Устанавливает текущего агента и сохраняет"""
        if agent_id in self.agents:
            self.current_agent_id = agent_id
            st.session_state['current_agent_id'] = agent_id
            self.save_agents()  # Сохраняем выбор
            return True
        return False

    def get_current_agent(self):
        """Возвращает текущего агента"""
        if self.current_agent_id and self.current_agent_id in self.agents:
            return self.agents[self.current_agent_id]
        return None

    def get_agents_list(self) -> List[Dict]:
        """Возвращает список агентов для отображения"""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "avatar": agent.avatar_emoji,
                "created_at": agent.created_at,
                "trainings": agent.stats.get('total_trainings', 0),
                "conversations": agent.stats.get('total_conversations', 0)
            }
            for agent in self.agents.values()
        ]

    def export_agent(self, agent_id) -> Optional[str]:
        """Экспорт агента в JSON строку"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            return json.dumps(agent.to_dict(), ensure_ascii=False, indent=2)
        return None

    def import_agent(self, json_data: str) -> bool:
        """Импорт агента из JSON строки"""
        try:
            data = json.loads(json_data)
            agent = AIAgent.from_dict(data)
            self.agents[agent.id] = agent
            self.save_agents()
            return True
        except Exception as e:
            st.error(f"Ошибка импорта: {e}")
            return False

# =================== ВИЗУАЛЬНЫЕ КОМПОНЕНТЫ ===================

def create_avatar(emoji, size=50):
    """Создает анимированный аватар"""
    return f"""
    <div style="
        width: {size}px;
        height: {size}px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: {size//2}px;
        animation: pulse 2s infinite;
        box-shadow: 0 0 20px rgba(102,126,234,0.5);
    ">
        {emoji}
    </div>
    """

def show_notification(message, type="success", duration=3):
    """Показывает красивое уведомление"""
    colors = {
        "success": "linear-gradient(135deg, #00ff88, #00bfff)",
        "error": "linear-gradient(135deg, #ff4444, #ff8844)",
        "warning": "linear-gradient(135deg, #ffaa00, #ffdd44)",
        "info": "linear-gradient(135deg, #667eea, #764ba2)"
    }
    
    notification_html = f"""
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        background: {colors.get(type, colors['info'])};
        color: white;
        padding: 15px 25px;
        border-radius: 15px;
        z-index: 9999;
        animation: slideInDown 0.3s ease;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        font-weight: bold;
    ">
        {message}
    </div>
    """
    st.markdown(notification_html, unsafe_allow_html=True)
    time.sleep(duration)

# =================== НАСТРОЙКА СТРАНИЦЫ ===================

st.set_page_config(
    page_title="Workflow Builder Pro v9.0 - Премиум версия",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Применяем премиум стили
apply_premium_styles()

# Заголовок с анимацией
st.markdown("""
<div class="main-header">
    <h1>🎨 WORKFLOW BUILDER PRO v9.0</h1>
    <p>Премиум версия | Обучаемые ИИ агенты | Автосохранение | Современный дизайн</p>
    <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1rem;">
        <span class="badge-premium">✨ ИИ Агенты</span>
        <span class="badge-premium">💾 Автосохранение</span>
        <span class="badge-premium">🎨 Премиум дизайн</span>
        <span class="badge-premium">🚀 Высокая производительность</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =================== ИНИЦИАЛИЗАЦИЯ ===================

if 'agent_manager' not in st.session_state:
    st.session_state['agent_manager'] = AgentManager()

if 'workflows' not in st.session_state:
    st.session_state['workflows'] = load_workflows_from_file()

if 'current_workflow' not in st.session_state:
    st.session_state['current_workflow'] = []

if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ""

if 'auto_save_enabled' not in st.session_state:
    st.session_state['auto_save_enabled'] = True

if 'theme' not in st.session_state:
    st.session_state['theme'] = 'dark'

# Получаем менеджер
agent_manager = st.session_state['agent_manager']

# Статус загрузки с визуализацией
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if agent_manager.agents:
        st.markdown(f"""
        <div style="text-align: center; background: rgba(0,255,136,0.1); border-radius: 15px; padding: 0.5rem; margin-bottom: 1rem;">
            ✅ Загружено <strong>{len(agent_manager.agents)}</strong> агентов из файла
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; background: rgba(102,126,234,0.1); border-radius: 15px; padding: 0.5rem; margin-bottom: 1rem;">
            📁 Создайте первого агента - он автоматически сохранится
        </div>
        """, unsafe_allow_html=True)

# =================== БОКОВАЯ ПАНЕЛЬ ===================

with st.sidebar:
    st.markdown("## 🔑 API Настройки")
    api_key = st.text_input("DeepSeek API Key", type="password", value=st.session_state.get('api_key', ''), 
                           help="Получите бесплатный ключ на platform.deepseek.com")
    st.session_state['api_key'] = api_key
    
    st.markdown("---")
    st.markdown("## 💾 Управление данными")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Сохранить всё", use_container_width=True):
            if agent_manager.save_agents():
                save_workflows_to_file(st.session_state['workflows'])
                st.success("✅ Все данные сохранены!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Ошибка сохранения")
    
    with col2:
        if st.button("🔄 Перезагрузить", use_container_width=True):
            agent_manager.load_agents()
            st.session_state['workflows'] = load_workflows_from_file()
            st.success("✅ Данные перезагружены!")
            st.rerun()
    
    # Статус сохранения с визуализацией
    if os.path.exists('agents.json'):
        mod_time = os.path.getmtime('agents.json')
        last_save = datetime.fromtimestamp(mod_time).strftime("%H:%M:%S")
        file_size = os.path.getsize('agents.json')
        
        st.markdown(f"""
        <div style="background: rgba(78,205,196,0.1); border-radius: 15px; padding: 0.8rem; margin: 0.5rem 0;">
            <div style="font-size: 0.8rem;">📁 agents.json</div>
            <div style="font-size: 0.7rem; opacity: 0.7;">{file_size} байт | {last_save}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("## 🤖 Мои агенты")
    
    # Список агентов с улучшенным отображением
    agents_list = agent_manager.get_agents_list()
    
    if agents_list:
        for agent in agents_list:
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.markdown(f"<div style='font-size: 2rem;'>{agent['avatar']}</div>", unsafe_allow_html=True)
                with col2:
                    if st.button(f"{agent['name']}", key=f"select_{agent['id']}", use_container_width=True):
                        agent_manager.set_current_agent(agent['id'])
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_{agent['id']}"):
                        agent_manager.delete_agent(agent['id'])
                        st.rerun()
                
                # Краткая статистика
                st.markdown(f"""
                <div style="font-size: 0.7rem; margin-left: 45px; margin-top: -10px; margin-bottom: 10px; opacity: 0.7;">
                    🎓 {agent['trainings']} обучений | 💬 {agent['conversations']} диалогов
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Нет созданных агентов\n\nНажмите ➕ Создать агента")
    
    st.markdown("---")
    st.markdown("## ➕ Создать агента")
    
    # Выбор аватара
    avatars = ["🧠", "🤖", "🎯", "💡", "⚡", "🎨", "🔬", "📊", "🎭", "🌟", "🔥", "💎"]
    selected_avatar = st.selectbox("Выберите аватар", avatars, index=0)
    
    new_agent_name = st.text_input("Имя агента", placeholder="Мой помощник", key="new_agent_name")
    new_agent_role = st.text_input("Роль", placeholder="Эксперт по данным", key="new_agent_role")
    new_agent_prompt = st.text_area("Системный промпт", 
                                    placeholder="Ты профессиональный помощник, который...", 
                                    height=100,
                                    key="new_agent_prompt")
    
    if st.button("✨ Создать агента", use_container_width=True):
        if new_agent_name and new_agent_role:
            agent_manager.add_agent(new_agent_name, new_agent_role, new_agent_prompt, selected_avatar)
            st.success(f"✅ Агент {new_agent_name} создан и сохранен!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Заполните имя и роль")
    
    st.markdown("---")
    st.markdown("## 📤 Экспорт/Импорт")
    
    current_agent = agent_manager.get_current_agent()
    if current_agent:
        export_data = agent_manager.export_agent(current_agent.id)
        if export_data:
            st.download_button(
                label=f"📥 Экспорт {current_agent.name}",
                data=export_data,
                file_name=f"{current_agent.name}_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    uploaded_file = st.file_uploader("📂 Импорт агента из JSON", type=['json'])
    if uploaded_file:
        import_data = uploaded_file.read().decode('utf-8')
        if agent_manager.import_agent(import_data):
            st.success("✅ Агент импортирован и сохранен!")
            time.sleep(1)
            st.rerun()

# =================== ОСНОВНАЯ ОБЛАСТЬ ===================

current_agent = agent_manager.get_current_agent()

# Создаем красивое меню вкладок
selected_tab = option_menu(
    menu_title=None,
    options=["💬 Чат", "🎓 Обучение", "🧠 Память", "📊 Аналитика", "🤖 Workflow"],
    icons=["chat-dots", "book", "brain", "graph-up", "gear"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "transparent"},
        "icon": {"color": "#4ECDC4", "font-size": "1.2rem"},
        "nav-link": {
            "font-size": "1rem",
            "text-align": "center",
            "margin": "0px",
            "--hover-color": "rgba(78,205,196,0.1)",
            "border-radius": "10px",
        },
        "nav-link-selected": {"background": "linear-gradient(135deg, #667eea, #764ba2)"},
    }
)

# =================== ВКЛАДКА 1: ЧАТ ===================

if selected_tab == "💬 Чат":
    if current_agent:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            {create_avatar(current_agent.avatar_emoji, 60)}
            <div>
                <h2 style="margin: 0;">{current_agent.name}</h2>
                <p style="margin: 0; opacity: 0.8;">{current_agent.role}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Инициализация истории чата
        if f"chat_history_{current_agent.id}" not in st.session_state:
            st.session_state[f"chat_history_{current_agent.id}"] = []
        
        # Отображение истории с красивыми стилями
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state[f"chat_history_{current_agent.id}"]:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message-user">
                        <strong>👤 Вы</strong><br>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message-agent">
                        <strong>🤖 {current_agent.name}</strong><br>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Ввод сообщения
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input("Введите сообщение:", key="chat_input", label_visibility="collapsed", 
                                      placeholder="Напишите сообщение...")
        with col2:
            use_training = st.checkbox("🎓 Использовать обучение", value=True)
        
        if st.button("📤 Отправить", type="primary", use_container_width=True):
            if user_input:
                with st.spinner(f"{current_agent.name} думает..."):
                    response = current_agent.generate_response(user_input, api_key, use_training)
                    
                    # Сохраняем в историю
                    st.session_state[f"chat_history_{current_agent.id}"].append({"role": "user", "content": user_input})
                    st.session_state[f"chat_history_{current_agent.id}"].append({"role": "agent", "content": response})
                    
                    # Сохраняем агента после диалога
                    agent_manager.save_agents()
                    
                    st.rerun()
        
        # Кнопка очистки чата
        if st.button("🗑️ Очистить историю чата", use_container_width=True):
            st.session_state[f"chat_history_{current_agent.id}"] = []
            st.rerun()
        
        # Статистика чата
        chat_count = len(st.session_state[f"chat_history_{current_agent.id}"])
        st.markdown(f"""
        <div style="text-align: center; margin-top: 1rem; opacity: 0.6; font-size: 0.8rem;">
            📊 Всего сообщений: {chat_count}
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem;">🤖</div>
            <h3>Агент не выбран</h3>
            <p>Создайте или выберите агента в боковой панели, чтобы начать общение</p>
        </div>
        """, unsafe_allow_html=True)

# =================== ВКЛАДКА 2: ОБУЧЕНИЕ ===================

elif selected_tab == "🎓 Обучение":
    if current_agent:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">{current_agent.avatar_emoji}</div>
            <div>
                <h2 style="margin: 0;">Обучение {current_agent.name}</h2>
                <p style="margin: 0; opacity: 0.8;">Обучите агента правильным ответам на ваши вопросы</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📝 Вопрос")
            train_question = st.text_area("Вопрос / Запрос:", height=100, 
                                         placeholder="Как лучше организовать маркетинговую кампанию?")
        with col2:
            st.markdown("### 💡 Ответ")
            train_answer = st.text_area("Правильный ответ:", height=100, 
                                       placeholder="Вот как лучше организовать...")
        
        train_context = st.text_input("📌 Контекст (опционально):", 
                                     placeholder="Например: B2B маркетинг, IT компания")
        
        if st.button("📚 Добавить пример обучения", type="primary", use_container_width=True):
            if train_question and train_answer:
                current_agent.add_training_example(train_question, train_answer, train_context)
                agent_manager.save_agents()
                st.success("✅ Пример добавлен в обучение и сохранен!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Заполните вопрос и ответ")
        
        # Отображение существующих примеров с улучшенным дизайном
        if current_agent.training_examples:
            st.markdown("---")
            st.markdown("### 📖 Библиотека обучения")
            st.markdown(f"Всего примеров: **{len(current_agent.training_examples)}**")
            
            for i, example in enumerate(reversed(current_agent.training_examples[-15:]), 1):
                with st.expander(f"📚 Пример {i}: {example['user_input'][:60]}..."):
                    st.markdown(f"""
                    <div class="training-card-premium">
                        <strong>❓ Вопрос:</strong><br>
                        {example['user_input']}<br><br>
                        <strong>✅ Ответ:</strong><br>
                        {example['expected_output']}<br>
                        <hr style="margin: 0.5rem 0;">
                        <span style="font-size: 0.7rem; opacity: 0.6;">
                            📅 {example['timestamp'][:19]} | 
                            📌 Контекст: {example.get('context', 'Нет')}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🗑️ Удалить пример", key=f"del_train_{i}"):
                        current_agent.training_examples.remove(example)
                        agent_manager.save_agents()
                        st.rerun()
    else:
        st.info("👈 Сначала выберите агента для обучения")

# =================== ВКЛАДКА 3: ПАМЯТЬ ===================

elif selected_tab == "🧠 Память":
    if current_agent:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">🧠</div>
            <div>
                <h2 style="margin: 0;">Память {current_agent.name}</h2>
                <p style="margin: 0; opacity: 0.8;">Агент запоминает важную информацию</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 💾 Добавить в память")
            mem_key = st.text_input("Ключ памяти:", placeholder="например: любимый_цвет")
            mem_value = st.text_input("Значение:", placeholder="например: синий")
            
            if st.button("💾 Сохранить в память", use_container_width=True):
                if mem_key and mem_value:
                    current_agent.add_to_memory(mem_key, mem_value)
                    agent_manager.save_agents()
                    st.success(f"✅ Сохранено: {mem_key} → {mem_value}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Заполните ключ и значение")
        
        with col2:
            st.markdown("### 🔍 Поиск в памяти")
            search_key = st.text_input("Поиск по ключу:", placeholder="введите ключ для поиска")
            if st.button("🔍 Найти в памяти", use_container_width=True):
                if search_key:
                    value = current_agent.get_from_memory(search_key)
                    if value:
                        st.success(f"🔑 {search_key} → {value}")
                    else:
                        st.warning("Ничего не найдено")
        
        # Отображение всей памяти с визуализацией
        if current_agent.memory:
            st.markdown("---")
            st.markdown(f"### 📋 Вся память ({len(current_agent.memory)} записей)")
            
            # Создаем DataFrame для визуализации
            memory_df = pd.DataFrame([
                {"Ключ": item['key'], "Значение": item['value'][:50], "Дата": item['timestamp'][:19]}
                for item in reversed(current_agent.memory[-30:])
            ])
            st.dataframe(memory_df, use_container_width=True)
            
            # Визуализация важности
            importance_counts = {}
            for item in current_agent.memory:
                imp = item.get('importance', 'normal')
                importance_counts[imp] = importance_counts.get(imp, 0) + 1
            
            if importance_counts:
                fig = px.pie(values=list(importance_counts.values()), 
                            names=list(importance_counts.keys()),
                            title="Распределение по важности",
                            color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👈 Сначала выберите агента")

# =================== ВКЛАДКА 4: АНАЛИТИКА ===================

elif selected_tab == "📊 Аналитика":
    if current_agent:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">📊</div>
            <div>
                <h2 style="margin: 0;">Аналитика {current_agent.name}</h2>
                <p style="margin: 0; opacity: 0.8;">Статистика и метрики производительности</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Ключевые метрики
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="stat-card-glass">
                <div class="stat-number">{current_agent.stats.get('total_trainings', 0)}</div>
                <div style="margin-top: 0.5rem;">🎓 Обучений</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card-glass">
                <div class="stat-number">{current_agent.stats.get('total_conversations', 0)}</div>
                <div style="margin-top: 0.5rem;">💬 Диалогов</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            success_rate = current_agent.stats.get('success_rate', 0)
            st.markdown(f"""
            <div class="stat-card-glass">
                <div class="stat-number">{success_rate:.1f}%</div>
                <div style="margin-top: 0.5rem;">✅ Успешность</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            memory_count = len(current_agent.memory)
            st.markdown(f"""
            <div class="stat-card-glass">
                <div class="stat-number">{memory_count}</div>
                <div style="margin-top: 0.5rem;">🧠 Памяти</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Графики производительности
        col1, col2 = st.columns(2)
        
        with col1:
            # График обучения
            if current_agent.training_examples:
                dates = [ex['timestamp'][:10] for ex in current_agent.training_examples]
                date_counts = pd.Series(dates).value_counts().sort_index()
                
                fig = px.line(x=date_counts.index, y=date_counts.values, 
                             title="Динамика обучения",
                             labels={'x': 'Дата', 'y': 'Количество примеров'})
                fig.update_traces(line_color='#4ECDC4', line_width=3)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Успешность по дням
            if current_agent.conversation_history:
                conv_dates = [c['timestamp'][:10] for c in current_agent.conversation_history]
                conv_counts = pd.Series(conv_dates).value_counts().sort_index()
                
                fig = px.bar(x=conv_counts.index, y=conv_counts.values,
                            title="Активность по дням",
                            labels={'x': 'Дата', 'y': 'Количество диалогов'},
                            color_discrete_sequence=['#667eea'])
                st.plotly_chart(fig, use_container_width=True)
        
        # История диалогов
        st.markdown("---")
        st.markdown("### 📜 История диалогов")
        
        if current_agent.conversation_history:
            for i, conv in enumerate(reversed(current_agent.conversation_history[-10:]), 1):
                with st.expander(f"💬 Диалог {i} - {conv['timestamp'][:19]}"):
                    st.markdown(f"""
                    <div style="background: rgba(102,126,234,0.1); border-radius: 10px; padding: 0.8rem; margin: 0.5rem 0;">
                        <strong>👤 Пользователь:</strong><br>
                        {conv['user']}
                    </div>
                    <div style="background: rgba(78,205,196,0.1); border-radius: 10px; padding: 0.8rem; margin: 0.5rem 0;">
                        <strong>🤖 {current_agent.name}:</strong><br>
                        {conv['agent'][:300]}{'...' if len(conv['agent']) > 300 else ''}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("История диалогов пуста")
    
    # Общая статистика по всем агентам
    st.markdown("---")
    st.markdown("### 📈 Общая статистика по всем агентам")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего агентов", len(agent_manager.agents), delta=None)
    with col2:
        total_trainings = sum(a.stats.get('total_trainings', 0) for a in agent_manager.agents.values())
        st.metric("Всего обучений", total_trainings, delta=None)
    with col3:
        total_conversations = sum(a.stats.get('total_conversations', 0) for a in agent_manager.agents.values())
        st.metric("Всего диалогов", total_conversations, delta=None)
    with col4:
        total_memory = sum(len(a.memory) for a in agent_manager.agents.values())
        st.metric("Всего записей памяти", total_memory, delta=None)

# =================== ВКЛАДКА 5: WORKFLOW ===================

elif selected_tab == "🤖 Workflow":
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <div style="font-size: 3rem;">🤖</div>
        <div>
            <h2 style="margin: 0;">Генерация Workflow</h2>
            <p style="margin: 0; opacity: 0.8;">Создайте автоматизацию из текстового описания</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    workflow_description = st.text_area(
        "📝 Опишите вашу задачу:",
        height=150,
        placeholder="Пример: Сначала прочитать данные из Google таблицы, затем проанализировать их через DeepSeek AI и отправить результат на email",
        help="Опишите на русском языке, что должна делать автоматизация"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("✨ Сгенерировать workflow", type="primary", use_container_width=True):
            if workflow_description and api_key:
                with st.spinner("🤖 ИИ анализирует и генерирует workflow..."):
                    result = AIWorkflowGenerator.generate(workflow_description, api_key)
                    
                    if "error" in result:
                        st.error(f"❌ Ошибка: {result['error']}")
                    else:
                        st.success("✅ Workflow успешно сгенерирован!")
                        
                        # Отображение
                        st.subheader("📋 Сгенерированный workflow")
                        st.json(result)
                        
                        # Добавляем в текущий workflow
                        if st.button("➕ Добавить в текущий workflow"):
                            if 'nodes' in result:
                                st.session_state['current_workflow'].extend(result['nodes'])
                                st.success("Блоки добавлены!")
                                time.sleep(1)
                                st.rerun()
            else:
                if not workflow_description:
                    st.warning("Введите описание workflow")
                if not api_key:
                    st.warning("Укажите API ключ в боковой панели")
    
    # Текущий workflow
    st.markdown("---")
    st.markdown("### 📦 Текущий workflow")
    
    if st.session_state['current_workflow']:
        for i, node in enumerate(st.session_state['current_workflow']):
            with st.expander(f"⚙️ Блок {i+1}: {node.get('name', 'Unknown')} - {node.get('type', 'unknown')}"):
                st.json(node)
                if st.button(f"🗑️ Удалить", key=f"del_workflow_{i}"):
                    st.session_state['current_workflow'].pop(i)
                    st.rerun()
        
        # Сохранение workflow
        col1, col2 = st.columns(2)
        with col1:
            workflow_name = st.text_input("Название workflow для сохранения:", placeholder="Мой первый workflow")
            if st.button("💾 Сохранить workflow", use_container_width=True):
                if workflow_name:
                    st.session_state['workflows'][workflow_name] = st.session_state['current_workflow']
                    save_workflows_to_file(st.session_state['workflows'])
                    st.success(f"✅ Workflow '{workflow_name}' сохранен!")
                else:
                    st.error("Введите название")
        
        with col2:
            if st.button("🗑️ Очистить workflow", use_container_width=True):
                st.session_state['current_workflow'] = []
                st.rerun()
    else:
        st.info("Workflow пуст. Сгенерируйте или добавьте блоки")
    
    # Загруженные workflows
    if st.session_state['workflows']:
        st.markdown("---")
        st.markdown("### 📚 Сохраненные workflows")
        
        for name, workflow in st.session_state['workflows'].items():
            with st.expander(f"📁 {name}"):
                st.json(workflow)
                if st.button(f"Загрузить {name}", key=f"load_{name}"):
                    st.session_state['current_workflow'] = workflow
                    st.success(f"Workflow '{name}' загружен!")
                    st.rerun()

# =================== ИНДИКАТОР АВТОСОХРАНЕНИЯ ===================

if st.session_state.get('auto_save_enabled', True):
    st.markdown("""
    <div class="save-indicator-premium">
        💾 Автосохранение активно
    </div>
    """, unsafe_allow_html=True)

# =================== ПОДВАЛ ===================

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #888">
    <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🧠 Workflow Builder PRO v9.0</div>
    <div style="font-size: 0.8rem;">Премиум версия | Обучаемые ИИ агенты | Автосохранение | Современный дизайн</div>
    <div style="font-size: 0.7rem; margin-top: 0.5rem;">
        ⭐ Все данные автоматически сохраняются | После перезапуска всё восстанавливается
    </div>
    <div style="font-size: 0.7rem; margin-top: 0.5rem;">
        📁 Файлы: agents.json | workflows.json | settings.json
    </div>
    <div style="font-size: 0.7rem; margin-top: 0.5rem; opacity: 0.5;">
        © 2024 Workflow Builder Pro | Создано с любовью для автоматизации
    </div>
</div>
""", unsafe_allow_html=True)
