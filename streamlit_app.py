"""
================================================================================
КОНСТРУКТОР WORKFLOW PRO v7.0 - ПОЛНАЯ ВЕРСИЯ (РАСШИРЕННАЯ)
Обучаемые ИИ агенты | Сохранение | Русские условия | Полный функционал
ДОБАВЛЕНО: Email/Outlook | Google Sheets API | Голосовой ввод | Мобильная адаптация
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
from typing import Dict, List, Optional, Any
import plotly.express as px
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import speech_recognition as sr

# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ КЛАССЫ (ДОБАВЛЕНЫ БЕЗ ИЗМЕНЕНИЯ ОСНОВНОГО КОДА)
# ============================================================================

class EmailSender:
    """Класс для отправки email через SMTP"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, smtp_server: str = "smtp.gmail.com", 
                   smtp_port: int = 587, sender_email: str = None, sender_password: str = None) -> Dict:
        try:
            if not sender_email or not sender_password:
                return {"success": False, "error": "Не указаны учетные данные отправителя"}
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            return {"success": True, "to": to_email, "subject": subject, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_outlook(to_email: str, subject: str, body: str, sender_email: str = None, sender_password: str = None) -> Dict:
        return EmailSender.send_email(to_email, subject, body, "smtp-mail.outlook.com", 587, sender_email, sender_password)
    
    @staticmethod
    def send_yandex(to_email: str, subject: str, body: str, sender_email: str = None, sender_password: str = None) -> Dict:
        return EmailSender.send_email(to_email, subject, body, "smtp.yandex.ru", 587, sender_email, sender_password)
    
    @staticmethod
    def send_mailru(to_email: str, subject: str, body: str, sender_email: str = None, sender_password: str = None) -> Dict:
        return EmailSender.send_email(to_email, subject, body, "smtp.mail.ru", 587, sender_email, sender_password)

class GoogleSheetsManager:
    """Класс для работы с Google Sheets API"""
    
    def __init__(self, credentials_json: str = None):
        self.client = None
        self.sheet = None
        self.worksheet = None
        if credentials_json:
            self.authenticate(credentials_json)
    
    def authenticate(self, credentials_json: str):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds_dict = json.loads(credentials_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            self.client = gspread.authorize(creds)
            return True
        except Exception as e:
            st.error(f"Ошибка аутентификации: {e}")
            return False
    
    def open_sheet(self, sheet_url: str, worksheet_name: str = None):
        try:
            if self.client is None:
                st.error("Клиент Google Sheets не инициализирован. Проверьте JSON-ключ.")
                return False
            if '/d/' in sheet_url:
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url
            self.sheet = self.client.open_by_key(sheet_id)
            if worksheet_name:
                self.worksheet = self.sheet.worksheet(worksheet_name)
            else:
                self.worksheet = self.sheet.sheet1
            return True
        except Exception as e:
            st.error(f"Ошибка открытия таблицы: {e}")
            return False
    
    def append_row(self, row_data: List) -> Dict:
        try:
            self.worksheet.append_row(row_data, value_input_option='USER_ENTERED')
            return {"success": True, "row": row_data, "row_number": len(self.worksheet.get_all_values()) + 1, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_cell(self, row: int, col: int, value: str) -> Dict:
        try:
            self.worksheet.update_cell(row, col, str(value))
            return {"success": True, "cell": f"{chr(64+col)}{row}", "value": value}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_data(self) -> List[List]:
        try:
            return self.worksheet.get_all_values()
        except Exception as e:
            st.error(f"Ошибка получения данных: {e}")
            return []
    
    def find_last_row(self, column: str = 'A') -> int:
        try:
            col_idx = ord(column.upper()) - 64
            col_data = self.worksheet.col_values(col_idx)
            return len(col_data)
        except:
            return 0
    
    def find_cell_by_value(self, value: str, column: str = 'A') -> Optional[int]:
        try:
            col_idx = ord(column.upper()) - 64
            col_data = self.worksheet.col_values(col_idx)
            for i, cell_value in enumerate(col_data, 1):
                if cell_value == value:
                    return i
            return None
        except:
            return None
    
    def batch_update(self, updates: List[Dict]) -> Dict:
        try:
            for update in updates:
                cell = update.get('cell')
                value = update.get('value')
                if cell:
                    self.worksheet.update_acell(cell, str(value))
            return {"success": True, "updates": len(updates)}
        except Exception as e:
            return {"success": False, "error": str(e)}

class VoiceInput:
    """Класс для голосового ввода"""
    
    @staticmethod
    def recognize_speech(language: str = 'ru-RU') -> str:
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("🎤 Слушаю... Говорите...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                st.info("🔄 Распознаю...")
            try:
                text = recognizer.recognize_google(audio, language=language)
                return text
            except sr.UnknownValueError:
                return "❌ Не удалось распознать речь"
            except sr.RequestError as e:
                return f"❌ Ошибка сервиса: {e}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

# ============================================================================ 
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================================

st.set_page_config(
    page_title="Workflow Builder Pro - Обучаемые ИИ Агенты v7.0",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Мобильная адаптация
is_mobile = False
try:
    import user_agents
    user_agent_str = st.context.headers.get('User-Agent', '')
    user_agent = user_agents.parse(user_agent_str)
    is_mobile = user_agent.is_mobile
except:
    pass

# Стили CSS (СВЕТЛАЯ ТЕМА, ТЕКСТ ВИДИМЫЙ)
st.markdown(f"""
<style>
    /* ===== СВЕТЛАЯ ТЕМА ===== */
    [data-testid="stAppViewContainer"], 
    [data-testid="stSidebar"] {{
        background-color: #ffffff;
    }}
    [data-testid="stSidebar"] {{
        background-color: #f0f2f6;
        color: #000033;
    }}
    /* Текст в боковой панели */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stTextInput input, 
    [data-testid="stSidebar"] .stTextArea textarea,
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] .stSelectbox label {{
        color: #000033 !important;
    }}
    [data-testid="stSidebar"] .stTextInput input, 
    [data-testid="stSidebar"] .stTextArea textarea {{
        background: rgba(0,0,0,0.05) !important;
        border: 1px solid rgba(0,0,0,0.2) !important;
    }}
    [data-testid="stSidebar"] .stButton button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }}

    /* Основные заголовки и текст */
    .stMarkdown, .stText, .stCaption, label, .stSelectbox label, .stCheckbox label {{
        color: #000033;
    }}

    /* Поля ввода глобально */
    input, textarea {{
        color: #000033 !important;
        background: rgba(0,0,0,0.03) !important;
        border: 1px solid rgba(0,0,0,0.2) !important;
    }}
    input::placeholder, textarea::placeholder {{
        color: rgba(0,0,0,0.4) !important;
    }}

    /* Мобильная адаптация */
    @media (max-width: 768px) {{
        .main-header {{
            padding: 1rem !important;
        }}
        .main-header h1 {{
            font-size: 1.5rem !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            flex-wrap: wrap !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.7rem !important;
            padding: 0.3rem 0.5rem !important;
        }}
        .agent-card {{
            padding: 0.5rem !important;
        }}
        .chat-message-user, .chat-message-agent {{
            max-width: 95% !important;
            font-size: 0.85rem !important;
        }}
        .stButton button {{
            font-size: 0.8rem !important;
            padding: 0.3rem 0.6rem !important;
        }}
        .stat-card h3 {{
            font-size: 1.2rem !important;
        }}
    }}
    
    /* Основные стили */
    .main-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        animation: fadeIn 1s ease-in;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(-20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }}
    .main-header p {{
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
    }}
    .agent-card {{
        background: linear-gradient(135deg, #e6e6fa 0%, #d8bfd8 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4ECDC4;
        transition: all 0.3s;
        cursor: pointer;
    }}
    .agent-card:hover {{
        transform: translateX(5px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }}
    .agent-card-selected {{
        border-left-color: #00ff88;
        background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
    }}
    .stat-card {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        transition: transform 0.3s;
    }}
    .stat-card:hover {{
        transform: translateY(-5px);
    }}
    .stat-card h3 {{
        color: white;
        margin: 0;
        font-size: 1.5rem;
    }}
    .stat-card p {{
        color: rgba(255,255,255,0.9);
        margin: 0;
    }}
    .memory-box {{
        background: #f3e5f5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffa500;
        margin: 0.5rem 0;
        color: #000033;
    }}
    .training-example {{
        background: #e8eaf6;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        font-size: 0.9rem;
        color: #000033;
    }}
    .workflow-node {{
        background: linear-gradient(135deg, #e6e6fa 0%, #d8bfd8 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #000033;
        border-left: 4px solid #4ECDC4;
        transition: all 0.3s;
    }}
    .workflow-node:hover {{
        transform: translateX(5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }}
    .workflow-node-success {{
        border-left-color: #00ff88;
        background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
    }}
    .workflow-node-error {{
        border-left-color: #ff4444;
        background: linear-gradient(135deg, #ffcdd2 0%, #ef9a9a 100%);
    }}
    .info-box {{
        background: #e8eaf6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 1rem 0;
        color: #000033;
    }}
    .info-box h4 {{
        color: #000033;
        margin: 0 0 0.5rem 0;
    }}
    .info-box p {{
        color: #333;
        margin: 0;
    }}
    .condition-box {{
        background: #fff3e0;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffa500;
        margin: 0.5rem 0;
        font-family: monospace;
        color: #000080;
    }}
    .stButton button {{
        border-radius: 10px !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }}
    .stButton button:hover {{
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }}
    .stTextArea textarea {{
        border-radius: 10px;
    }}
    .stTextInput input {{
        border-radius: 10px;
    }}
    div[data-testid="stExpander"] details {{
        background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
        border-radius: 15px;
        border: none;
    }}
    div[data-testid="stExpander"] summary {{
        color: #000033;
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# Заголовок с индикатором мобильной версии
st.markdown(f"""
<div class="main-header">
    <h1>🧠 WORKFLOW BUILDER PRO v7.0</h1>
    <p>Обучаемые ИИ агенты | Сохранение контекста | Персональные помощники | Русские условия</p>
    <p style="font-size: 0.9rem;">⭐ Создавайте и обучайте своих ИИ агентов | 💾 Сохраняйте навсегда | 🔄 Обменивайтесь агентами</p>
    {'<p style="font-size: 0.8rem; background: #4ECDC4; display: inline-block; padding: 0.2rem 1rem; border-radius: 20px;">📱 МОБИЛЬНАЯ ВЕРСИЯ</p>' if is_mobile else ''}
</div>
""", unsafe_allow_html=True)

# ============================================================================ 
# КЛАСС ДЛЯ ПРЕОБРАЗОВАНИЯ РУССКИХ УСЛОВИЙ
# ============================================================================

class RussianConditionParser:
    """Преобразует условия на русском языке в исполняемый код"""
    
    @staticmethod
    def parse(condition_text: str) -> Dict:
        """Преобразует русское условие в структуру"""
        condition_text = condition_text.lower().strip()
        
        patterns = {
            'больше': r'(.+?)\s+(больше|выше|>)\s+(.+)',
            'меньше': r'(.+?)\s+(меньше|ниже|<)\s+(.+)',
            'равно': r'(.+?)\s+(равно|равняется|==|=)\s+(.+)',
            'содержит': r'(.+?)\s+(содержит|включает|имеет)\s+(.+)',
            'начинается': r'(.+?)\s+(начинается с|начинается)\s+(.+)',
            'заканчивается': r'(.+?)\s+(заканчивается на|заканчивается)\s+(.+)',
            'пусто': r'(.+?)\s+(пусто|не заполнено|отсутствует)',
            'между': r'(.+?)\s+(между|от)\s+(.+?)\s+(до|и)\s+(.+)',
        }
        
        result = {
            'original': condition_text,
            'type': 'unknown',
            'condition': condition_text,
            'code': None,
            'examples': []
        }
        
        if 'если' in condition_text and 'то' in condition_text:
            match = re.search(r'если\s+(.+?)\s+то', condition_text)
            if match:
                condition_part = match.group(1)
                result['type'] = 'if_then'
                result['condition'] = condition_part
                result['code'] = f"if {RussianConditionParser._to_code(condition_part)}:"
        
        elif 'иначе' in condition_text:
            parts = condition_text.split('иначе')
            if len(parts) == 2:
                result['type'] = 'if_else'
                result['true_branch'] = parts[0].replace('если', '').strip()
                result['false_branch'] = parts[1].strip()
                result['code'] = f"if {RussianConditionParser._to_code(result['true_branch'])}:\n    # действие\nelse:\n    # другое действие"
        
        else:
            for pattern_type, pattern in patterns.items():
                match = re.search(pattern, condition_text)
                if match:
                    result['type'] = pattern_type
                    result['matches'] = match.groups()
                    result['code'] = RussianConditionParser._generate_code(pattern_type, match.groups())
                    break
        
        result['examples'] = RussianConditionParser._get_examples()
        return result
    
    @staticmethod
    def _to_code(condition: str) -> str:
        replacements = {
            'больше': '>', 'выше': '>', 'меньше': '<', 'ниже': '<',
            'равно': '==', 'равняется': '==', 'содержит': 'in',
            'начинается с': '.startswith', 'заканчивается на': '.endswith'
        }
        for rus, eng in replacements.items():
            if rus in condition:
                condition = condition.replace(rus, eng)
        condition = re.sub(r'\{\{([^}]+)\}\}', r'data.get("\1", None)', condition)
        return condition
    
    @staticmethod
    def _generate_code(pattern_type: str, groups: tuple) -> str:
        codes = {
            'больше': f"if {groups[0].strip()} > {groups[2].strip()}:",
            'меньше': f"if {groups[0].strip()} < {groups[2].strip()}:",
            'равно': f"if {groups[0].strip()} == {groups[2].strip()}:",
            'содержит': f"if {groups[2].strip()} in {groups[0].strip()}:",
            'пусто': f"if not {groups[0].strip()}:"
        }
        return codes.get(pattern_type, f"if {pattern_type}: # {groups}")
    
    @staticmethod
    def _get_examples() -> List[str]:
        return [
            "если цена больше 1000 то отправить уведомление",
            "если статус равно 'успех' иначе отправить ошибку",
            "если количество меньше 5 то пополнить склад",
            "если текст содержит 'срочно' то отметить как важное",
            "если поле пусто то заполнить значением по умолчанию"
        ]

# ============================================================================ 
# КЛАСС ДЛЯ ХРАНЕНИЯ И ОБУЧЕНИЯ ИИ АГЕНТОВ
# ============================================================================

class AIAgent:
    """Класс для создания и обучения ИИ агентов"""
    
    def __init__(self, name: str, role: str, system_prompt: str, agent_id: str = None):
        self.id = agent_id or hashlib.md5(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
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
    
    def add_training_example(self, user_input: str, expected_output: str, context: str = ""):
        example = {
            'id': len(self.training_examples) + 1,
            'user_input': user_input,
            'expected_output': expected_output,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'used_count': 0
        }
        self.training_examples.append(example)
        self.stats['total_trainings'] += 1
        self.stats['last_trained'] = datetime.now().isoformat()
        return example
    
    def add_to_memory(self, key: str, value: Any, importance: str = "normal"):
        memory_item = {
            'key': key,
            'value': value,
            'importance': importance,
            'timestamp': datetime.now().isoformat(),
            'access_count': 0
        }
        existing_idx = None
        for i, mem in enumerate(self.memory):
            if mem['key'] == key:
                existing_idx = i
                break
        
        if existing_idx is not None:
            self.memory[existing_idx] = memory_item
        else:
            self.memory.append(memory_item)
    
    def get_from_memory(self, key: str) -> Any:
        for mem in self.memory:
            if mem['key'] == key:
                mem['access_count'] += 1
                return mem['value']
        return None
    
    def add_conversation(self, user_message: str, agent_response: str, feedback: str = None):
        conversation = {
            'user': user_message,
            'agent': agent_response,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat(),
            'context': self.get_context_summary()
        }
        self.conversation_history.append(conversation)
        self.stats['total_conversations'] += 1
        
        if feedback == 'positive':
            self.stats['success_rate'] = (self.stats['success_rate'] * (self.stats['total_conversations'] - 1) + 100) / self.stats['total_conversations']
        elif feedback == 'negative':
            self.stats['success_rate'] = (self.stats['success_rate'] * (self.stats['total_conversations'] - 1) + 0) / self.stats['total_conversations']
    
    def get_context_summary(self) -> str:
        summary = f"Роль: {self.role}\n"
        summary += f"Память: {len(self.memory)} фактов\n"
        summary += f"Обучен на: {len(self.training_examples)} примерах\n"
        return summary
    
    def generate_response(self, user_input: str, api_key: str, use_training: bool = True) -> str:
        if not api_key:
            return "❌ API ключ не указан. Получите бесплатно на platform.deepseek.com"
        
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            
            memory_context = ""
            if self.memory:
                memory_context = "\n\nЗНАНИЯ АГЕНТА (из памяти):\n"
                for mem in self.memory[-5:]:
                    memory_context += f"- {mem['key']}: {mem['value']}\n"
            
            training_context = ""
            if use_training and self.training_examples:
                training_context = "\n\nПРИМЕРЫ ОБУЧЕНИЯ:\n"
                for ex in self.training_examples[-3:]:
                    training_context += f"Пользователь: {ex['user_input']}\n"
                    training_context += f"Правильный ответ: {ex['expected_output']}\n\n"
            
            history_context = ""
            if self.conversation_history:
                history_context = "\n\nИСТОРИЯ ДИАЛОГОВ:\n"
                for conv in self.conversation_history[-3:]:
                    history_context += f"Пользователь: {conv['user']}\n"
                    history_context += f"Агент: {conv['agent']}\n\n"
            
            device_context = "\n\nУстройство: " + ("Мобильное (отвечай кратко)" if is_mobile else "Десктоп")
            
            full_prompt = f"""
Ты - ИИ агент с именем "{self.name}" и ролью "{self.role}".
 
{self.system_prompt}

{memory_context}

{training_context}

{history_context}

{device_context}

Текущий запрос пользователя: "{user_input}"

Ответь, используя полученные знания, примеры обучения и память.
Будь полезным, точным и дружелюбным.
"""
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                max_tokens=600 if is_mobile else 1000
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'system_prompt': self.system_prompt,
            'created_at': self.created_at,
            'training_examples': self.training_examples,
            'memory': self.memory,
            'conversation_history': self.conversation_history[-50:],
            'knowledge_base': self.knowledge_base,
            'stats': self.stats
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AIAgent':
        agent = cls(
            name=data['name'],
            role=data['role'],
            system_prompt=data['system_prompt'],
            agent_id=data['id']
        )
        agent.created_at = data.get('created_at', datetime.now().isoformat())
        agent.training_examples = data.get('training_examples', [])
        agent.memory = data.get('memory', [])
        agent.conversation_history = data.get('conversation_history', [])
        agent.knowledge_base = data.get('knowledge_base', {})
        agent.stats = data.get('stats', {
            'total_trainings': len(agent.training_examples),
            'total_conversations': len(agent.conversation_history),
            'success_rate': 0,
            'last_trained': None
        })
        return agent

# ============================================================================ 
# КЛАСС ДЛЯ ГЕНЕРАЦИИ WORKFLOW ЧЕРЕЗ ИИ
# ============================================================================

class AIWorkflowGenerator:
    """Генерирует workflow из текстового описания на русском"""
    
    @staticmethod
    def generate(description: str, api_key: str) -> List[Dict]:
        if not api_key:
            return []
        
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            
            prompt = f"""
Ты эксперт по созданию workflow автоматизации. На основе описания пользователя создай JSON workflow.

Описание пользователя: "{description}"

Правила:
1. Workflow - это массив блоков (nodes)
2. Каждый блок имеет: name (название), type (тип), config (настройки)
3. Доступные типы блоков:
   - google_sheets_read: чтение из Google таблиц (config: sheet_url)
   - google_sheets_write: запись в Google таблицы (config: sheet_url, column_mapping)
   - email_send: отправка email (config: to, subject, body)
   - outlook_send: отправка через Outlook (config: to, subject, body)
   - deepseek: AI анализ (config: system_prompt, user_prompt)
   - http_get: GET запрос к API (config: url)
   - http_post: POST запрос (config: url, body)
   - condition: условие (config: condition на русском)
   - loop: цикл (config: items)

4. Условия пиши на РУССКОМ языке, используя природные фразы

Верни ТОЛЬКО JSON массив блоков, без пояснений.
"""
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Ты генератор workflow автоматизации. Возвращай только JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                workflow = json.loads(json_match.group())
                return workflow
            else:
                return []
                
        except Exception as e:
            st.error(f"Ошибка генерации: {str(e)}")
            return []

# ============================================================================ 
# МЕНЕДЖЕР АГЕНТОВ
# ============================================================================

class AgentManager:
    """Управляет всеми ИИ агентами"""
    
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.current_agent_id: Optional[str] = None
        self.load_agents()
    
    def load_agents(self):
        if 'agents' not in st.session_state:
            default_agents = self._create_default_agents()
            st.session_state.agents = {agent.id: agent.to_dict() for agent in default_agents}
            st.session_state.current_agent_id = default_agents[0].id if default_agents else None
        
        for agent_id, agent_dict in st.session_state.agents.items():
            if agent_id not in self.agents:
                self.agents[agent_id] = AIAgent.from_dict(agent_dict)
        
        self.current_agent_id = st.session_state.get('current_agent_id')
    
    def _create_default_agents(self) -> List[AIAgent]:
        agents = []
        
        analyst = AIAgent(
            name="Аналитик Данных",
            role="эксперт по анализу данных и бизнес-метрикам",
            system_prompt="""Ты профессиональный аналитик данных. Твоя задача:
- Анализировать цифры и метрики
- Находить закономерности и тренды
- Давать практические рекомендации
- Объяснять сложные вещи простым языком"""
        )
        agents.append(analyst)
        
        automation = AIAgent(
            name="Автоматизатор",
            role="специалист по автоматизации бизнес-процессов",
            system_prompt="""Ты эксперт по автоматизации. Твоя задача:
- Предлагать решения для автоматизации
- Оптимизировать рабочие процессы
- Указывать на узкие места
- Давать пошаговые инструкции"""
        )
        agents.append(automation)
        
        manager = AIAgent(
            name="Менеджер Задач",
            role="помощник по управлению задачами и проектами",
            system_prompt="""Ты менеджер проектов. Твоя задача:
- Помогать планировать задачи
- Приоритезировать дела
- Напоминать о важных вещах
- Отслеживать прогресс"""
        )
        agents.append(manager)
        
        return agents
    
    def save_agents(self):
        st.session_state.agents = {agent_id: agent.to_dict() for agent_id, agent in self.agents.items()}
        st.session_state.current_agent_id = self.current_agent_id
    
    def add_agent(self, name: str, role: str, system_prompt: str) -> AIAgent:
        agent = AIAgent(name, role, system_prompt)
        self.agents[agent.id] = agent
        self.save_agents()
        return agent
    
    def delete_agent(self, agent_id: str):
        if agent_id in self.agents:
            del self.agents[agent_id]
            if self.current_agent_id == agent_id:
                self.current_agent_id = next(iter(self.agents.keys())) if self.agents else None
            self.save_agents()
    
    def get_current_agent(self) -> Optional[AIAgent]:
        if self.current_agent_id and self.current_agent_id in self.agents:
            return self.agents[self.current_agent_id]
        return None
    
    def set_current_agent(self, agent_id: str):
        if agent_id in self.agents:
            self.current_agent_id = agent_id
            st.session_state.current_agent_id = agent_id
            self.save_agents()
    
    def export_agent(self, agent_id: str) -> str:
        if agent_id in self.agents:
            return json.dumps(self.agents[agent_id].to_dict(), ensure_ascii=False, indent=2)
        return ""
    
    def import_agent(self, agent_json: str) -> bool:
        try:
            data = json.loads(agent_json)
            agent = AIAgent.from_dict(data)
            self.agents[agent.id] = agent
            self.save_agents()
            return True
        except Exception as e:
            st.error(f"Ошибка импорта: {str(e)}")
            return False

# ============================================================================ 
# КЛАСС ДЛЯ ВЫПОЛНЕНИЯ WORKFLOW (РАСШИРЕННЫЙ)
# ============================================================================

class WorkflowExecutor:
    """Выполняет workflow с поддержкой условий на русском и новыми блоками"""
    
    def __init__(self, workflow: List[Dict], api_key: str = None, agent_manager: AgentManager = None):
        self.workflow = workflow
        self.api_key = api_key
        self.agent_manager = agent_manager
        self.context = {}
        self.results = []
        self.current_node_index = 0
        self.branch_stack = []
        self.gs_manager = None
    
    def execute(self, progress_callback=None) -> Dict:
        start_time = time.time()
        
        while self.current_node_index < len(self.workflow):
            node = self.workflow[self.current_node_index]
            
            if progress_callback:
                progress_callback(self.current_node_index, node)
            
            try:
                result = self._execute_node(node)
                self.results.append({
                    'node': node.get('name'),
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
                if isinstance(result, dict):
                    self.context.update(result)
                
                node['status'] = 'success'
                self.current_node_index += 1
                
            except Exception as e:
                node['status'] = 'error'
                node['error'] = str(e)
                return {
                    'success': False,
                    'error': str(e),
                    'results': self.results,
                    'execution_time': time.time() - start_time
                }
        
        return {
            'success': True,
            'results': self.results,
            'context': self.context,
            'execution_time': time.time() - start_time
        }
    
    def _execute_node(self, node: Dict) -> Any:
        node_type = node.get('type')
        config = node.get('config', {})
        
        if node_type == 'google_sheets_read':
            return self._execute_google_sheets_read(config)
        elif node_type == 'google_sheets_write':
            return self._execute_google_sheets_write(config)
        elif node_type == 'email_send':
            return self._execute_email_send(config)
        elif node_type == 'outlook_send':
            return self._execute_outlook_send(config)
        elif node_type == 'voice_input':
            return self._execute_voice_input(config)
        elif node_type == 'deepseek':
            return self._execute_deepseek(config)
        elif node_type == 'condition':
            return self._execute_condition(config)
        elif node_type == 'loop':
            return self._execute_loop(config)
        elif node_type == 'http_get':
            return self._execute_http_get(config)
        elif node_type == 'http_post':
            return self._execute_http_post(config)
        elif node_type == 'ai_agent':
            return self._execute_ai_agent(config)
        elif node_type == 'email':
            return self._execute_email(config)
        elif node_type == 'telegram':
            return self._execute_telegram(config)
        else:
            return {'status': 'unknown_type', 'type': node_type}
    
    def _execute_google_sheets_read(self, config: Dict) -> Dict:
        sheet_url = config.get('sheet_url', '')
        credentials_json = config.get('credentials_json', '')
        
        if not sheet_url:
            return {'error': 'URL не указан'}
        if not credentials_json:
            return {'error': 'Не указан JSON-ключ сервисного аккаунта'}
        
        try:
            if not self.gs_manager:
                self.gs_manager = GoogleSheetsManager(credentials_json)
                if self.gs_manager.client is None:
                    return {'error': 'Не удалось аутентифицироваться в Google Sheets'}
            if self.gs_manager.open_sheet(sheet_url, config.get('worksheet_name')):
                data = self.gs_manager.get_all_data()
                return {
                    'data': data,
                    'rows': len(data),
                    'columns': len(data[0]) if data else 0,
                    'success': True
                }
            return {'error': 'Не удалось открыть таблицу'}
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_google_sheets_write(self, config: Dict) -> Dict:
        sheet_url = config.get('sheet_url', '')
        credentials_json = config.get('credentials_json', '')
        column_mapping = config.get('column_mapping', {})
        
        if not sheet_url:
            return {'error': 'URL не указан'}
        if not credentials_json:
            return {'error': 'Не указан JSON-ключ сервисного аккаунта'}
        
        try:
            if not self.gs_manager:
                self.gs_manager = GoogleSheetsManager(credentials_json)
                if self.gs_manager.client is None:
                    return {'error': 'Не удалось аутентифицироваться в Google Sheets'}
            if self.gs_manager.open_sheet(sheet_url, config.get('worksheet_name')):
                max_col = 26
                row_data = [''] * max_col
                
                for col_name, source in column_mapping.items():
                    col_idx = ord(col_name.upper()) - 65
                    if 0 <= col_idx < max_col:
                        if source.startswith('{{') and source.endswith('}}'):
                            var_name = source[2:-2]
                            row_data[col_idx] = str(self.context.get(var_name, ''))
                        else:
                            row_data[col_idx] = str(source)
                
                result = self.gs_manager.append_row(row_data)
                return result
            return {'error': 'Не удалось открыть таблицу'}
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_email_send(self, config: Dict) -> Dict:
        to_email = config.get('to', '')
        subject = config.get('subject', 'Уведомление')
        body = config.get('body', '')
        sender_email = config.get('sender_email', '')
        sender_password = config.get('sender_password', '')
        
        for key, value in self.context.items():
            if isinstance(value, str):
                body = body.replace(f"{{{{{key}}}}}", value)
                subject = subject.replace(f"{{{{{key}}}}}", value)
        
        result = EmailSender.send_email(to_email, subject, body, sender_email=sender_email, sender_password=sender_password)
        return result
    
    def _execute_outlook_send(self, config: Dict) -> Dict:
        to_email = config.get('to', '')
        subject = config.get('subject', 'Уведомление')
        body = config.get('body', '')
        sender_email = config.get('sender_email', '')
        sender_password = config.get('sender_password', '')
        
        for key, value in self.context.items():
            if isinstance(value, str):
                body = body.replace(f"{{{{{key}}}}}", value)
                subject = subject.replace(f"{{{{{key}}}}}", value)
        
        result = EmailSender.send_outlook(to_email, subject, body, sender_email, sender_password)
        return result
    
    def _execute_voice_input(self, config: Dict) -> Dict:
        try:
            text = VoiceInput.recognize_speech()
            return {'success': True, 'text': text, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_deepseek(self, config: Dict) -> Dict:
        if not self.api_key:
            return {'error': 'API ключ не указан'}
        
        try:
            client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
            
            user_prompt = config.get('user_prompt', '')
            for key, value in self.context.items():
                if isinstance(value, str):
                    user_prompt = user_prompt.replace(f"{{{{{key}}}}}", value)
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": config.get('system_prompt', 'Ты полезный ассистент')},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=float(config.get('temperature', 0.3))
            )
            
            return {
                'response': response.choices[0].message.content,
                'model': 'deepseek-chat'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_condition(self, config: Dict) -> Dict:
        condition_text = config.get('condition', '')
        result = self._evaluate_condition(condition_text)
        
        return {
            'condition': condition_text,
            'result': result
        }
    
    def _evaluate_condition(self, condition_text: str) -> bool:
        condition_text = condition_text.lower()
        
        if 'больше' in condition_text:
            match = re.search(r'(\w+)\s+больше\s+(\d+)', condition_text)
            if match:
                var_name = match.group(1)
                value = float(match.group(2))
                context_value = self.context.get(var_name, 0)
                return float(context_value) > value
        
        elif 'меньше' in condition_text:
            match = re.search(r'(\w+)\s+меньше\s+(\d+)', condition_text)
            if match:
                var_name = match.group(1)
                value = float(match.group(2))
                context_value = self.context.get(var_name, 0)
                return float(context_value) < value
        
        elif 'равно' in condition_text or 'равняется' in condition_text:
            match = re.search(r'(\w+)\s+равно\s+(.+)', condition_text)
            if match:
                var_name = match.group(1)
                value = match.group(2).strip().strip("'\"")
                context_value = self.context.get(var_name, '')
                return str(context_value) == value
        
        elif 'содержит' in condition_text:
            match = re.search(r'(\w+)\s+содержит\s+(.+)', condition_text)
            if match:
                var_name = match.group(1)
                value = match.group(2).strip().strip("'\"")
                context_value = str(self.context.get(var_name, ''))
                return value in context_value
        
        return True
    
    def _execute_loop(self, config: Dict) -> Dict:
        items = config.get('items', '[]')
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except:
                items = []
        
        batch_size = int(config.get('batch_size', 10))
        
        return {
            'items': items,
            'count': len(items),
            'batch_size': batch_size,
            'processed': 0
        }
    
    def _execute_http_get(self, config: Dict) -> Dict:
        url = config.get('url', '')
        if not url:
            return {'error': 'URL не указан'}
        
        try:
            response = requests.get(url, timeout=30)
            return {
                'status': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'url': url
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_http_post(self, config: Dict) -> Dict:
        url = config.get('url', '')
        if not url:
            return {'error': 'URL не указан'}
        
        try:
            body = config.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
            
            response = requests.post(url, json=body, timeout=30)
            return {
                'status': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'url': url
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_email(self, config: Dict) -> Dict:
        return {
            'to': config.get('to', ''),
            'subject': config.get('subject', ''),
            'body': config.get('body', ''),
            'status': 'ready'
        }
    
    def _execute_telegram(self, config: Dict) -> Dict:
        return {
            'chat_id': config.get('chat_id', ''),
            'message': config.get('message', ''),
            'status': 'ready'
        }
    
    def _execute_ai_agent(self, config: Dict) -> Dict:
        if not self.agent_manager:
            return {'error': 'Менеджер агентов не инициализирован'}
        
        agent_id = config.get('agent_id')
        if not agent_id or agent_id not in self.agent_manager.agents:
            return {'error': 'Агент не найден'}
        
        agent = self.agent_manager.agents[agent_id]
        question = config.get('question', '')
        use_training = config.get('use_training', True)
        
        response = agent.generate_response(question, self.api_key, use_training)
        
        return {
            'agent': agent.name,
            'question': question,
            'response': response
        }

# ============================================================================ 
# ИНИЦИАЛИЗАЦИЯ СЕССИИ
# ============================================================================

if 'agent_manager' not in st.session_state:
    st.session_state.agent_manager = AgentManager()
if 'workflow' not in st.session_state:
    st.session_state.workflow = []
if 'agent_messages' not in st.session_state:
    st.session_state.agent_messages = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'analytics' not in st.session_state:
    st.session_state.analytics = {
        'total_executions': 0,
        'successful_executions': 0,
        'failed_executions': 0
    }

agent_manager = st.session_state.agent_manager

# ============================================================================ 
# БОКОВАЯ ПАНЕЛЬ - АГЕНТЫ (РАСШИРЕННАЯ)
# ============================================================================

with st.sidebar:
    st.markdown("## 🧠 МОИ ИИ АГЕНТЫ")
    
    api_key = st.text_input(
        "🔑 DeepSeek API Ключ",
        type="password",
        help="Нужен для работы ИИ агентов. Бесплатно на platform.deepseek.com",
        key="api_key_main"
    )
    
    st.markdown("---")
    st.markdown("## 📧 EMAIL НАСТРОЙКИ")
    
    sender_email = st.text_input("Email отправителя", key="sender_email", placeholder="your@email.com")
    sender_password = st.text_input("Пароль приложения", type="password", key="sender_password", help="Используйте пароль приложения")
    
    st.markdown("---")
    st.markdown("## 📊 GOOGLE SHEETS")
    
    credentials_json = st.text_area("JSON ключ сервисного аккаунта", height=150, key="credentials_json",
                                    placeholder='{"type": "service_account", "project_id": "...", ...}')
    
    st.markdown("---")
    
    # Список агентов
    for agent in agent_manager.agents.values():
        is_selected = agent_manager.current_agent_id == agent.id
        selected_class = "agent-card-selected" if is_selected else ""
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"📋 {agent.name}", key=f"select_{agent.id}", use_container_width=True):
                agent_manager.set_current_agent(agent.id)
                st.rerun()
        with col2:
            if st.button(f"🗑️", key=f"del_{agent.id}"):
                agent_manager.delete_agent(agent.id)
                st.rerun()
    
    st.markdown("---")
    
    # Создание нового агента
    with st.expander("➕ СОЗДАТЬ НОВОГО АГЕНТА", expanded=False):
        new_name = st.text_input("Имя агента", placeholder="Мой Помощник")
        new_role = st.text_input("Роль", placeholder="эксперт по маркетингу")
        new_prompt = st.text_area("Системный промпт", height=100, 
                                   placeholder="Ты помощник, который...")
        
        if st.button("✨ Создать агента", use_container_width=True):
            if new_name and new_role and new_prompt:
                agent_manager.add_agent(new_name, new_role, new_prompt)
                st.success(f"✅ Агент {new_name} создан!")
                st.rerun()
            else:
                st.warning("Заполните все поля")
    
    st.markdown("---")
    
    # Экспорт/Импорт
    with st.expander("🔄 ЭКСПОРТ/ИМПОРТ АГЕНТА", expanded=False):
        current = agent_manager.get_current_agent()
        if current:
            export_json = agent_manager.export_agent(current.id)
            st.download_button(
                label=f"📤 Экспорт {current.name}",
                data=export_json,
                file_name=f"agent_{current.name}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        import_file = st.file_uploader("Импорт агента", type=['json'])
        if import_file:
            content = import_file.read().decode('utf-8')
            if agent_manager.import_agent(content):
                st.success("✅ Агент импортирован!")
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("## 📊 СТАТИСТИКА")
    st.metric("Всего агентов", len(agent_manager.agents))
    current_agent = agent_manager.get_current_agent()
    if current_agent:
        st.metric("Обучений", current_agent.stats['total_trainings'])
        st.metric("Диалогов", current_agent.stats['total_conversations'])
        if is_mobile:
            st.metric("📱 Моб. режим", "Активен")
    
    st.markdown("---")
    
    # Управление workflow
    st.markdown("## 🛠️ УПРАВЛЕНИЕ")
    if st.button("🗑️ Очистить workflow", use_container_width=True):
        st.session_state.workflow = []
        st.rerun()

# ============================================================================ 
# ОСНОВНЫЕ ВКЛАДКИ
# ============================================================================

tabs = st.tabs(["💬 ДИАЛОГ С АГЕНТОМ", "📚 ОБУЧЕНИЕ", "🧠 ПАМЯТЬ", "📊 АНАЛИТИКА", "🤖 WORKFLOW", "🔀 РУССКИЕ УСЛОВИЯ", "📧 EMAIL/GOOGLE", "🎤 ГОЛОСОВОЙ", "📖 ИНСТРУКЦИЯ"])

# ============================================================================ 
# ВКЛАДКА 1: ДИАЛОГ С АГЕНТОМ (С ГОЛОСОВЫМ ВВОДОМ)
# ============================================================================

with tabs[0]:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Нет выбранного агента. Создайте или выберите агента в боковой панели")
    else:
        st.subheader(f"💬 Диалог с агентом: {current_agent.name}")
        st.markdown(f"*Роль: {current_agent.role}*")
        if is_mobile:
            st.info("📱 Вы используете мобильную версию. Ответы будут краткими.")
        
        # История диалога
        for idx, msg in enumerate(st.session_state.agent_messages):
            if msg['role'] == 'user':
                st.markdown(f"**👤 Вы:** {msg['content']}")
            else:
                st.markdown(f"**🤖 {current_agent.name}:** {msg['content']}")
            st.markdown("---")
        
        # Ввод сообщения
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            user_input = st.text_area("✏️ Ваше сообщение:", height=100, key="agent_input")
        with col2:
            use_training = st.checkbox("Использовать обучение", value=True)
        with col3:
            if st.button("🎤 Голос", use_container_width=True, help="Голосовой ввод"):
                voice_text = VoiceInput.recognize_speech()
                if voice_text and not voice_text.startswith("❌"):
                    st.session_state.agent_messages.append({
                        'role': 'user',
                        'content': voice_text,
                        'timestamp': datetime.now().isoformat()
                    })
                    st.rerun()
        
        if st.button("🚀 Отправить", type="primary", use_container_width=True):
            if user_input:
                st.session_state.agent_messages.append({
                    'role': 'user',
                    'content': user_input,
                    'timestamp': datetime.now().isoformat()
                })
                
                with st.spinner(f"{current_agent.name} думает..."):
                    response = current_agent.generate_response(user_input, api_key, use_training)
                
                st.session_state.agent_messages.append({
                    'role': 'agent',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                current_agent.add_conversation(user_input, response)
                agent_manager.save_agents()
                st.rerun()
        
        if st.button("🗑️ Очистить историю диалога"):
            st.session_state.agent_messages = []
            st.rerun()

# ============================================================================ 
# ВКЛАДКА 2: ОБУЧЕНИЕ
# ============================================================================

with tabs[1]:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента в боковой панели")
    else:
        st.subheader(f"📚 Обучение агента: {current_agent.name}")
        
        st.markdown("""
        <div class="info-box">
        <h4>🎯 Как обучать агента?</h4>
        <p>Добавляйте примеры правильных ответов. Агент будет учиться на них и давать более точные ответы!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Добавление примера
        with st.expander("➕ ДОБАВИТЬ ПРИМЕР ДЛЯ ОБУЧЕНИЯ", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                example_input = st.text_area("📝 Вопрос/Запрос пользователя:", height=100, key="train_input")
            with col2:
                example_output = st.text_area("✅ Ожидаемый ответ агента:", height=100, key="train_output")
            
            example_context = st.text_input("📌 Контекст (необязательно):", key="train_context")
            
            if st.button("✨ Добавить пример обучения", type="primary"):
                if example_input and example_output:
                    current_agent.add_training_example(example_input, example_output, example_context)
                    agent_manager.save_agents()
                    st.success("✅ Пример добавлен! Агент будет использовать его для обучения")
                    st.rerun()
                else:
                    st.warning("Заполните вопрос и ответ")
        
        st.markdown("---")
        
        # Список примеров обучения
        st.subheader(f"📚 Примеры обучения ({len(current_agent.training_examples)})")
        
        if current_agent.training_examples:
            for i, example in enumerate(reversed(current_agent.training_examples[-10:])):
                st.markdown(f"""
                <div class="training-example">
                    <strong>📝 Пример {i+1}:</strong><br>
                    <strong>Вопрос:</strong> {example['user_input']}<br>
                    <strong>Ответ:</strong> {example['expected_output'][:200]}{'...' if len(example['expected_output']) > 200 else ''}<br>
                    <small>📅 {example['timestamp'][:10]} | Использован {example.get('used_count', 0)} раз</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🗑️ Удалить пример {i+1}", key=f"del_example_{i}"):
                    current_agent.training_examples.remove(example)
                    agent_manager.save_agents()
                    st.rerun()
        else:
            st.info("Пока нет примеров обучения. Добавьте первый пример выше!")
        
        # Массовое обучение через текст
        st.markdown("---")
        with st.expander("📚 МАССОВОЕ ОБУЧЕНИЕ (из текста)"):
            bulk_text = st.text_area(
                "Вставьте текст с примерами (каждый пример с новой строки, формат: Вопрос -> Ответ)",
                height=150,
                placeholder="Как анализировать данные? -> Для анализа данных нужно...\nЧто такое автоматизация? -> Автоматизация это..."
            )
            
            if st.button("🚀 Обучить на всех примерах"):
                lines = bulk_text.strip().split('\n')
                added = 0
                for line in lines:
                    if '->' in line:
                        parts = line.split('->', 1)
                        question = parts[0].strip()
                        answer = parts[1].strip()
                        if question and answer:
                            current_agent.add_training_example(question, answer)
                            added += 1
                
                if added > 0:
                    agent_manager.save_agents()
                    st.success(f"✅ Добавлено {added} примеров обучения!")
                    st.rerun()
                else:
                    st.warning("Не найдено примеров в формате Вопрос -> Ответ")

# ============================================================================ 
# ВКЛАДКА 3: ПАМЯТЬ
# ============================================================================

with tabs[2]:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента в боковой панели")
    else:
        st.subheader(f"🧠 Память агента: {current_agent.name}")
        
        st.markdown("""
        <div class="info-box">
        <h4>💾 Что такое память агента?</h4>
        <p>Агент запоминает важные факты о вас, ваших предпочтениях и контексте. 
        Эти знания сохраняются между диалогами!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Добавление в память
        with st.expander("➕ ДОБАВИТЬ В ПАМЯТЬ", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                memory_key = st.text_input("📌 Ключ (что запомнить):", placeholder="любимый_язык")
            with col2:
                memory_value = st.text_input("💾 Значение:", placeholder="Python")
            
            importance = st.selectbox("Важность:", ["low", "normal", "high"])
            
            if st.button("💾 Сохранить в память"):
                if memory_key and memory_value:
                    current_agent.add_to_memory(memory_key, memory_value, importance)
                    agent_manager.save_agents()
                    st.success(f"✅ Запомнено: {memory_key} = {memory_value}")
                    st.rerun()
                else:
                    st.warning("Заполните ключ и значение")
        
        st.markdown("---")
        
        # Отображение памяти
        st.subheader(f"📚 Факты в памяти ({len(current_agent.memory)})")
        
        if current_agent.memory:
            for mem in current_agent.memory:
                importance_icon = "🔴" if mem['importance'] == 'high' else "🟡" if mem['importance'] == 'normal' else "🟢"
                st.markdown(f"""
                <div class="memory-box">
                    {importance_icon} <strong>{mem['key']}</strong> = {mem['value']}<br>
                    <small>📅 {mem['timestamp'][:10]} | Просмотров: {mem['access_count']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🗑️ Удалить", key=f"del_mem_{mem['key']}"):
                    current_agent.memory.remove(mem)
                    agent_manager.save_agents()
                    st.rerun()
        else:
            st.info("Память пуста. Добавьте факты, которые агент должен запомнить!")
        
        # Очистка памяти
        if st.button("🗑️ Очистить всю память", type="secondary"):
            current_agent.memory = []
            agent_manager.save_agents()
            st.success("Память очищена!")
            st.rerun()

# ============================================================================ 
# ВКЛАДКА 4: АНАЛИТИКА
# ============================================================================

with tabs[3]:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента в боковой панели")
    else:
        st.subheader(f"📊 Аналитика агента: {current_agent.name}")
        
        # Общая статистика
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stat-card"><h3>{current_agent.stats["total_trainings"]}</h3><p>Обучений</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-card"><h3>{current_agent.stats["total_conversations"]}</h3><p>Диалогов</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stat-card"><h3>{current_agent.stats["success_rate"]:.0f}%</h3><p>Успешность</p></div>', unsafe_allow_html=True)
        with col4:
            learned_from = len(current_agent.training_examples) + len(current_agent.memory)
            st.markdown(f'<div class="stat-card"><h3>{learned_from}</h3><p>Выучено фактов</p></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # График обучения
        if current_agent.training_examples:
            st.subheader("📈 Прогресс обучения")
            df_data = []
            for i, ex in enumerate(current_agent.training_examples):
                df_data.append({'Дата': ex['timestamp'][:10], 'Пример': i+1})
            if df_data:
                df = pd.DataFrame(df_data)
                fig = px.line(df, x='Дата', y='Пример', title="Накопление примеров обучения")
                st.plotly_chart(fig, use_container_width=True)
        
        # История диалогов
        st.subheader("💬 Последние диалоги")
        if current_agent.conversation_history:
            for conv in current_agent.conversation_history[-5:]:
                with st.expander(f"Диалог от {conv['timestamp'][:19]}"):
                    st.markdown(f"**👤 Пользователь:** {conv['user'][:200]}...")
                    st.markdown(f"**🤖 Агент:** {conv['agent'][:200]}...")
                    if conv.get('feedback'):
                        st.markdown(f"**📝 Оценка:** {conv['feedback']}")
        else:
            st.info("Пока нет диалогов")

# ============================================================================ 
# ВКЛАДКА 5: WORKFLOW (РАСШИРЕННЫЙ)
# ============================================================================

with tabs[4]:
    st.subheader("🤖 Интеграция ИИ агентов в workflow")
    
    st.markdown("""
    <div class="info-box">
    <h4>🎯 Используйте обученных агентов в автоматизациях!</h4>
    <p>Агенты могут анализировать данные, принимать решения и выполнять действия в ваших workflow.</p>
    <p><strong>✨ Новые блоки:</strong> Email/Outlook, Google Sheets (чтение/запись), Голосовой ввод</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 Добавить блок в workflow")
        
        # Блоки для workflow (расширенные)
        block_types = [
            ("📖 Google Sheets (чтение)", "google_sheets_read"),
            ("✍️ Google Sheets (запись)", "google_sheets_write"),
            ("🧠 DeepSeek AI", "deepseek"),
            ("🔀 Условие (русское)", "condition"),
            ("📧 Email (SMTP)", "email_send"),
            ("📱 Outlook", "outlook_send"),
            ("🎤 Голосовой ввод", "voice_input"),
            ("🔄 Цикл", "loop"),
            ("📡 HTTP GET", "http_get"),
            ("📤 HTTP POST", "http_post"),
            ("📧 Email (демо)", "email"),
            ("📱 Telegram", "telegram"),
        ]
        
        for name, btype in block_types:
            if st.button(f"{name}", key=f"add_block_{btype}", use_container_width=True):
                st.session_state.workflow.append({
                    "id": len(st.session_state.workflow),
                    "name": name,
                    "icon": name[0],
                    "type": btype,
                    "config": {},
                    "status": "pending"
                })
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🧠 Агенты в workflow")
        for agent in agent_manager.agents.values():
            if st.button(f"🧠 {agent.name}", key=f"workflow_agent_{agent.id}"):
                st.session_state.workflow.append({
                    "id": len(st.session_state.workflow),
                    "name": f"Агент {agent.name}",
                    "icon": "🧠",
                    "type": "ai_agent",
                    "agent_id": agent.id,
                    "config": {"question": "Проанализируй данные", "use_training": True},
                    "status": "pending"
                })
                st.rerun()
    
    with col2:
        st.markdown("### 📋 Текущий workflow")
        if st.session_state.workflow:
            for i, block in enumerate(st.session_state.workflow):
                # Определяем стиль
                status_class = ""
                if block.get('status') == 'success':
                    status_class = "workflow-node-success"
                elif block.get('status') == 'error':
                    status_class = "workflow-node-error"
                
                st.markdown(f"""
                <div class="workflow-node {status_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.2rem;">{block.get('icon', '•')}</span>
                            <span style="font-weight: bold;"> {block.get('name', 'Block')}</span>
                            <span style="font-size: 0.8rem;"> Шаг {i+1}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if i < len(st.session_state.workflow) - 1:
                    st.markdown('<div style="text-align: center; font-size: 1.2rem;">▼</div>', unsafe_allow_html=True)
                
                with st.expander(f"⚙️ Настроить {block.get('name', 'Block')}"):
                    block_type = block.get('type', '')
                    config = block.get('config', {})
                    
                    if block_type == 'google_sheets_read':
                        config['sheet_url'] = st.text_input("URL Google Таблицы", config.get('sheet_url', ''), key=f"url_{i}")
                        config['worksheet_name'] = st.text_input("Название листа (опционально)", config.get('worksheet_name', ''), key=f"ws_{i}")
                        config['credentials_json'] = credentials_json
                        st.caption("💡 Пример: https://docs.google.com/spreadsheets/d/ВАШ_ID_ТАБЛИЦЫ/edit")
                    
                    elif block_type == 'google_sheets_write':
                        config['sheet_url'] = st.text_input("URL Google Таблицы", config.get('sheet_url', ''), key=f"write_url_{i}")
                        config['worksheet_name'] = st.text_input("Название листа", config.get('worksheet_name', ''), key=f"write_ws_{i}")
                        config['credentials_json'] = credentials_json
                        
                        st.markdown("**Маппинг колонок (формат: A: значение или A: {{переменная}}):**")
                        mapping_text = st.text_area("Маппинг", config.get('mapping_text', ''), height=100, key=f"map_{i}",
                                                    placeholder="A: Имя\nB: {{email}}\nC: {{сообщение}}")
                        if mapping_text:
                            mapping = {}
                            for line in mapping_text.strip().split('\n'):
                                if ':' in line:
                                    col, val = line.split(':', 1)
                                    mapping[col.strip()] = val.strip()
                            config['column_mapping'] = mapping
                            config['mapping_text'] = mapping_text
                        st.caption("💡 Используйте {{переменная}} для подстановки из контекста")
                    
                    elif block_type == 'deepseek':
                        config['system_prompt'] = st.text_area("Инструкция для ИИ", 
                            config.get('system_prompt', 'Ты полезный ассистент'), 
                            height=80, key=f"sys_{i}")
                        config['user_prompt'] = st.text_area("Запрос к ИИ", 
                            config.get('user_prompt', ''), 
                            height=80, key=f"user_{i}")
                        config['temperature'] = st.slider("Креативность", 0.0, 1.0, 
                            float(config.get('temperature', 0.3)), key=f"temp_{i}")
                    
                    elif block_type == 'condition':
                        st.markdown("**Напишите условие на русском языке:**")
                        st.caption("Примеры: 'если цена больше 1000', 'если статус равно успех', 'если текст содержит срочно'")
                        config['condition'] = st.text_area("Условие", 
                            config.get('condition', 'если цена больше 1000'), 
                            height=80, key=f"cond_{i}")
                        
                        if config.get('condition'):
                            parsed = RussianConditionParser.parse(config['condition'])
                            if parsed.get('code'):
                                st.info(f"🔍 Преобразовано в: `{parsed['code']}`")
                    
                    elif block_type == 'ai_agent':
                        agent = agent_manager.agents.get(block.get('agent_id'))
                        if agent:
                            st.info(f"🧠 Агент: {agent.name} | Роль: {agent.role}")
                            config['question'] = st.text_area("Вопрос к агенту:", 
                                config.get('question', 'Проанализируй данные'), 
                                height=80, key=f"q_{i}")
                            config['use_training'] = st.checkbox("Использовать обучение", 
                                config.get('use_training', True), key=f"train_{i}")
                    
                    elif block_type in ['email_send', 'outlook_send']:
                        config['to'] = st.text_input("Кому", config.get('to', ''), key=f"to_{i}")
                        config['subject'] = st.text_input("Тема", config.get('subject', 'Уведомление'), key=f"subj_{i}")
                        config['body'] = st.text_area("Сообщение", config.get('body', ''), height=80, key=f"body_{i}")
                        config['sender_email'] = st.text_input("Email отправителя", config.get('sender_email', sender_email), key=f"from_{i}")
                        config['sender_password'] = st.text_input("Пароль", config.get('sender_password', sender_password), type="password", key=f"pass_{i}")
                        st.caption("💡 Используйте {{переменная}} для подстановки из контекста")
                    
                    elif block_type == 'voice_input':
                        st.info("🎤 При выполнении этого блока будет активирован микрофон для голосового ввода")
                    
                    elif block_type == 'email':
                        config['to'] = st.text_input("Кому", config.get('to', ''), key=f"to_demo_{i}")
                        config['subject'] = st.text_input("Тема", config.get('subject', 'Уведомление'), key=f"subj_demo_{i}")
                        config['body'] = st.text_area("Сообщение", config.get('body', ''), height=80, key=f"body_demo_{i}")
                    
                    elif block_type == 'telegram':
                        config['chat_id'] = st.text_input("Chat ID", config.get('chat_id', ''), key=f"chat_{i}")
                        config['message'] = st.text_area("Сообщение", config.get('message', ''), height=80, key=f"msg_{i}")
                    
                    elif block_type == 'loop':
                        config['items'] = st.text_area("Элементы (JSON массив)", 
                            config.get('items', '[1, 2, 3, 4, 5]'), 
                            height=80, key=f"items_{i}")
                        config['batch_size'] = st.number_input("Размер пачки", 1, 100, 
                            int(config.get('batch_size', 10)), key=f"batch_{i}")
                    
                    elif block_type in ['http_get', 'http_post']:
                        config['url'] = st.text_input("URL", config.get('url', ''), key=f"url_http_{i}")
                        config['headers'] = st.text_area("Заголовки (JSON)", 
                            config.get('headers', '{}'), key=f"headers_{i}")
                        if block_type == 'http_post':
                            config['body'] = st.text_area("Тело запроса (JSON)", 
                                config.get('body', '{}'), key=f"body_http_{i}")
                    
                    block['config'] = config
                
                if st.button(f"🗑️ Удалить блок {i+1}", key=f"del_{i}"):
                    st.session_state.workflow.pop(i)
                    st.rerun()
            
            st.markdown("---")
            
            # Кнопка запуска workflow
            if st.button("🚀 ЗАПУСТИТЬ WORKFLOW", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(idx, node):
                    progress_bar.progress((idx + 1) / len(st.session_state.workflow))
                    status_text.text(f"🔄 Выполняется: {node.get('name', 'Block')}")
                
                # Передаем учетные данные в executor
                for block in st.session_state.workflow:
                    if block.get('type') in ['google_sheets_read', 'google_sheets_write']:
                        block['config']['credentials_json'] = credentials_json
                    elif block.get('type') in ['email_send', 'outlook_send']:
                        if not block['config'].get('sender_email'):
                            block['config']['sender_email'] = sender_email
                        if not block['config'].get('sender_password'):
                            block['config']['sender_password'] = sender_password
                
                executor = WorkflowExecutor(st.session_state.workflow, api_key, agent_manager)
                result = executor.execute(update_progress)
                
                progress_bar.progress(1.0)
                
                if result['success']:
                    st.balloons()
                    st.success(f"✅ Workflow выполнен успешно за {result['execution_time']:.1f} секунд!")
                    
                    st.session_state.analytics['total_executions'] += 1
                    st.session_state.analytics['successful_executions'] += 1
                    
                    with st.expander("📋 Результаты выполнения", expanded=True):
                        for res in result['results']:
                            st.markdown(f"**📌 {res['node']}**")
                            st.json(res['result'])
                            st.markdown("---")
                else:
                    st.session_state.analytics['total_executions'] += 1
                    st.session_state.analytics['failed_executions'] += 1
                    st.error(f"❌ Ошибка: {result['error']}")
        else:
            st.info("💡 Добавьте блоки из левой колонки для создания workflow")

# ============================================================================ 
# ВКЛАДКА 6: РУССКИЕ УСЛОВИЯ
# ============================================================================

with tabs[5]:
    st.subheader("🔀 Русские условия для workflow")
    
    st.markdown("""
    <div class="info-box">
    <h4>🎯 Как писать условия на русском?</h4>
    <p>Просто напишите условие так, как вы бы сказали человеку. ИИ сам преобразует его в исполняемый код!</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Примеры условий")
        examples = [
            "если цена больше 1000 то отправить уведомление",
            "если статус равно 'успех' иначе отправить ошибку",
            "если количество меньше 5 то пополнить склад",
            "если текст содержит 'срочно' то отметить как важное",
            "если поле пусто то заполнить значением по умолчанию",
            "если сумма между 1000 и 5000 то одобрить"
        ]
        for ex in examples:
            st.code(f"📌 {ex}")
    
    with col2:
        st.markdown("### 🔧 Проверьте своё условие")
        test_condition = st.text_area("Напишите условие:", 
                                       height=150,
                                       placeholder="например: если температура больше 30 то включить кондиционер")
        
        if test_condition:
            parsed = RussianConditionParser.parse(test_condition)
            
            st.markdown("### 📊 Результат анализа:")
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric("Тип условия", parsed.get('type', 'unknown'))
            with col_res2:
                st.metric("Оригинал", parsed.get('original', '')[:50])
            
            if parsed.get('code'):
                st.success(f"💻 Сгенерированный код: `{parsed['code']}`")
            else:
                st.warning("⚠️ Не удалось распознать условие. Попробуйте переформулировать.")
    
    st.markdown("---")
    
    st.markdown("### 💡 Доступные операторы")
    st.markdown("""
    | Что написать | Как понять | Пример |
    |--------------|------------|--------|
    | `больше`, `выше`, `>` | Больше чем | `цена больше 1000` |
    | `меньше`, `ниже`, `<` | Меньше чем | `количество меньше 5` |
    | `равно`, `равняется`, `=` | Равно | `статус равно успех` |
    | `содержит`, `включает` | Содержит подстроку | `текст содержит срочно` |
    | `пусто`, `не заполнено` | Пустое значение | `поле пусто` |
    | `между ... и ...` | В диапазоне | `сумма между 1000 и 5000` |
    """)

# ============================================================================ 
# ВКЛАДКА 7: EMAIL/GOOGLE SHEETS
# ============================================================================

with tabs[6]:
    st.subheader("📧 Email и Google Sheets")
    
    tab_email, tab_gsheets = st.tabs(["📧 Отправка Email", "📊 Google Sheets"])
    
    with tab_email:
        st.markdown("### Отправка email через SMTP")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Gmail")
            Gmail_to = st.text_input("Кому", key="gmail_to")
            Gmail_subject = st.text_input("Тема", key="gmail_subject", value="Тестовое письмо")
            Gmail_body = st.text_area("Сообщение", key="gmail_body", height=150, value="Привет! Это тестовое письмо из Workflow Builder.")
            
            if st.button("📧 Отправить через Gmail", type="primary"):
                if sender_email and sender_password and Gmail_to:
                    with st.spinner("Отправка..."):
                        result = EmailSender.send_email(Gmail_to, Gmail_subject, Gmail_body, sender_email=sender_email, sender_password=sender_password)
                        if result['success']:
                            st.success("✅ Письмо отправлено!")
                        else:
                            st.error(f"❌ Ошибка: {result['error']}")
                else:
                    st.warning("Заполните email отправителя и пароль в боковой панели")
        
        with col2:
            st.markdown("#### Outlook")
            outlook_to = st.text_input("Кому", key="outlook_to")
            outlook_subject = st.text_input("Тема", key="outlook_subject", value="Тестовое письмо")
            outlook_body = st.text_area("Сообщение", key="outlook_body", height=150, value="Привет! Это тестовое письмо из Workflow Builder.")
            
            if st.button("📧 Отправить через Outlook", type="primary"):
                if sender_email and sender_password and outlook_to:
                    with st.spinner("Отправка..."):
                        result = EmailSender.send_outlook(outlook_to, outlook_subject, outlook_body, sender_email, sender_password)
                        if result['success']:
                            st.success("✅ Письмо отправлено!")
                        else:
                            st.error(f"❌ Ошибка: {result['error']}")
                else:
                    st.warning("Заполните email отправителя и пароль в боковой панели")
        
        st.markdown("---")
        st.markdown("### 💡 Условия для отправки в workflow")
        st.markdown("""
        В workflow можно задать условия на русском языке:
        - `если статус равно успех то отправить письмо`
        - `если цена больше 1000 отправить уведомление`
        - `если данные содержат ошибка то отправить в Outlook`
        """)
    
    with tab_gsheets:
        st.markdown("### Работа с Google Sheets")
        
        if not credentials_json:
            st.warning("⚠️ Для работы с Google Sheets необходим JSON ключ сервисного аккаунта. Добавьте его в боковой панели.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📖 Чтение данных")
            read_sheet_url = st.text_input("URL таблицы", key="read_sheet_url", placeholder="https://docs.google.com/spreadsheets/d/...")
            read_worksheet = st.text_input("Название листа (опционально)", key="read_worksheet")
            
            if st.button("📖 Прочитать таблицу", type="primary"):
                if credentials_json and read_sheet_url:
                    with st.spinner("Чтение..."):
                        gs = GoogleSheetsManager(credentials_json)
                        if gs.open_sheet(read_sheet_url, read_worksheet):
                            data = gs.get_all_data()
                            if data:
                                df = pd.DataFrame(data)
                                st.dataframe(df, use_container_width=True)
                                st.success(f"✅ Прочитано {len(data)} строк, {len(data[0]) if data else 0} колонок")
                            else:
                                st.info("Таблица пуста")
                        else:
                            st.error("Не удалось открыть таблицу")
                else:
                    st.warning("Укажите URL таблицы и JSON ключ")
        
        with col2:
            st.markdown("#### ✍️ Запись данных")
            write_sheet_url = st.text_input("URL таблицы", key="write_sheet_url", placeholder="https://docs.google.com/spreadsheets/d/...")
            write_worksheet = st.text_input("Название листа", key="write_worksheet")
            
            st.markdown("**Данные для записи (формат: столбец:значение):**")
            write_data = st.text_area("Данные", height=150, placeholder="A: Иван\nB: ivan@mail.ru\nC: Привет\nD: {{переменная}}")
            
            if st.button("✍️ Записать в таблицу", type="primary"):
                if credentials_json and write_sheet_url and write_data:
                    with st.spinner("Запись..."):
                        gs = GoogleSheetsManager(credentials_json)
                        if gs.open_sheet(write_sheet_url, write_worksheet):
                            row_data = [''] * 26
                            for line in write_data.strip().split('\n'):
                                if ':' in line:
                                    col, val = line.split(':', 1)
                                    col_idx = ord(col.strip().upper()) - 65
                                    if 0 <= col_idx < 26:
                                        # Подстановка переменных
                                        if val.strip().startswith('{{') and val.strip().endswith('}}'):
                                            var_name = val.strip()[2:-2]
                                            row_data[col_idx] = str(st.session_state.agent_messages[-1].get('content', '') if var_name == 'текст' else '')
                                        else:
                                            row_data[col_idx] = val.strip()
                            
                            result = gs.append_row(row_data)
                            if result['success']:
                                st.success(f"✅ Данные записаны в строку {result['row_number']}")
                            else:
                                st.error(f"❌ Ошибка: {result['error']}")
                        else:
                            st.error("Не удалось открыть таблицу")
                else:
                    st.warning("Заполните все поля")
        
        st.markdown("---")
        st.markdown("### 💡 Использование в workflow")
        st.markdown("""
        **В workflow можно настроить запись в определенные столбцы:**
        
        1. Добавьте блок **"Google Sheets (запись)"** в workflow
        2. Настройте маппинг колонок:
            3. Переменные `{{имя}}`, `{{email}}`, `{{сообщение}}` будут подставлены из контекста выполнения
        4. Данные будут добавлены в конец таблицы
        """)

# ============================================================================ 
# ВКЛАДКА 8: ГОЛОСОВОЙ ВВОД
# ============================================================================

with tabs[7]:
    st.subheader("🎤 Голосовой ввод текста")

    st.markdown("""
    <div class="info-box">
    <h4>🎯 Алгоритм работы:</h4>
    <p>1️⃣ Нажмите кнопку "Начать запись"<br>
    2️⃣ Произнесите текст в микрофон<br>
    3️⃣ Система автоматически распознает речь<br>
    4️⃣ Результат появится в поле ниже</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🎤 НАЧАТЬ ЗАПИСЬ", type="primary", use_container_width=True):
            with st.spinner("🎤 Слушаю..."):
                recognized_text = VoiceInput.recognize_speech()
                st.session_state.recognized_text = recognized_text
                st.rerun()

        if st.button("🔊 Озвучить текст", use_container_width=True):
            if 'recognized_text' in st.session_state and st.session_state.recognized_text:
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.say(st.session_state.recognized_text)
                    engine.runAndWait()
                    st.success("🔊 Озвучивание завершено")
                except Exception as e:
                    st.info(f"Для озвучивания требуется установка pyttsx3: {e}")

    with col2:
        st.markdown("### 📝 Распознанный текст")
        if 'recognized_text' in st.session_state and st.session_state.recognized_text:
            st.text_area("Текст", st.session_state.recognized_text, height=200, key="voice_result")
        
        if st.button("📋 Копировать в чат", use_container_width=True):
            st.session_state.agent_messages.append({
                'role': 'user',
                'content': st.session_state.recognized_text,
                'timestamp': datetime.now().isoformat()
            })
            st.success("✅ Текст скопирован в чат!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Использование в workflow")
    st.markdown("""
    **Голосовой ввод можно использовать в workflow:**
    
    1. Добавьте блок **"Голосовой ввод"** в workflow
    2. При выполнении блока активируется микрофон
    3. Распознанный текст сохраняется в контекст как `{{text}}`
    4. Дальнейшие блоки могут использовать этот текст
    """)

# ============================================================================ 
# ВКЛАДКА 9: ИНСТРУКЦИЯ
# ============================================================================

with tabs[8]:
    st.subheader("📖 Полная инструкция для новичков")

    st.markdown("""
    ## 🧠 Что такое ИИ агенты с обучением?

    **ИИ агенты** - это персонализированные помощники, которые:
    - ✅ **Учатся на ваших примерах**
    - ✅ **Запоминают важную информацию**
    - ✅ **Адаптируются под ваш стиль**
    - ✅ **Совершенствуются с каждым диалогом**

    ---

    ## 📚 Как обучить агента?

    ### 1. Добавление примеров
    Перейдите на вкладку **"ОБУЧЕНИЕ"** и добавьте примеры правильных ответов.

    ### 2. Массовое обучение
    Можно добавить сразу много примеров в формате: `Вопрос -> Ответ`

    ### 3. Память агента
    Добавляйте факты, которые агент должен запомнить.

    ---

    ## 🤖 Как использовать workflow?

    ### Создание автоматизации
    1. Перейдите на вкладку **"WORKFLOW"**
    2. Добавляйте блоки из левой колонки
    3. Настраивайте каждый блок
    4. Нажмите **"ЗАПУСТИТЬ WORKFLOW"**

    ### Новые блоки в v7.0:
    - **Google Sheets (чтение/запись)** - работа с таблицами
    - **Email/Outlook** - отправка писем
    - **Голосовой ввод** - распознавание речи

    ---

    ## 🔀 Русские условия
    Вы можете писать логические условия на естественном русском языке. Примеры:
    - «если цена больше 1000 то отправить уведомление»
    - «если статус равно 'успех' иначе отметить ошибку»
    - «если текст содержит срочно то выделить красным»
    Система автоматически преобразует их в исполняемый код.

    ---

    ## 💡 Советы
    - Чем больше примеров обучения – тем точнее ответы агента.
    - Сохраняйте важную информацию в памяти агента.
    - Экспортируйте агентов для обмена с коллегами.
    - Используйте мобильную версию для быстрых ответов на ходу.
    """)

    st.markdown("---")
    st.success("🎉 Теперь вы полностью готовы к работе с Workflow Builder Pro v7.0!")
