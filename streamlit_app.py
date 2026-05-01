"""
================================================================================
КОНСТРУКТОР WORKFLOW PRO v7.0 - ПОЛНАЯ ВЕРСИЯ (РАСШИРЕННАЯ)
Обучаемые ИИ агенты | Сохранение | Русские условия | Полный функционал
ДОБАВЛЕНО: Email | Outlook | Google Sheets API | Голосовой ввод
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
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import speech_recognition as sr

# ============================================================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================================

st.set_page_config(
    page_title="Workflow Builder Pro - Обучаемые ИИ Агенты v7.0",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ПРЕМИУМ СТИЛИ (С ИСПРАВЛЕННОЙ ВИДИМОСТЬЮ ТЕКСТА)
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
    }
    
    body, .stApp, div, p, span, label, .stMarkdown, .stText, .stCaption {
        color: #ffffff !important;
    }
    
    h1, h2, h3, h4, h5, h6, .stHeading {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-size: 200% 200%;
        animation: gradientShift 5s ease infinite;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .agent-card {
        background: linear-gradient(135deg, rgba(26,26,46,0.95), rgba(22,30,62,0.95));
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(78,205,196,0.3);
        transition: all 0.3s ease;
    }
    
    .agent-card:hover {
        transform: translateX(5px);
        border-color: #4ECDC4;
    }
    
    .agent-card-selected {
        border-left: 4px solid #00ff88;
        background: linear-gradient(135deg, rgba(10,46,31,0.95), rgba(10,26,16,0.95));
    }
    
    .chat-message-user {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 20px;
        padding: 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        animation: slideInRight 0.3s ease;
        color: #ffffff !important;
    }
    
    .chat-message-agent {
        background: linear-gradient(135deg, rgba(26,26,46,0.9), rgba(22,30,62,0.9));
        border-radius: 20px;
        padding: 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
        border-left: 4px solid #4ECDC4;
        animation: slideInLeft 0.3s ease;
        color: #ffffff !important;
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(50px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-50px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .stat-card-glass {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
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
        font-size: 2rem;
        font-weight: 800;
        color: #4ECDC4 !important;
    }
    
    .workflow-node {
        background: linear-gradient(135deg, rgba(26,26,46,0.9), rgba(22,30,62,0.9));
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4ECDC4;
        transition: all 0.3s ease;
    }
    
    .workflow-node:hover {
        transform: translateX(5px);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #ffffff !important;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102,126,234,0.3);
    }
    
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.15) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 10px;
        color: #ffffff !important;
        padding: 0.5rem;
    }
    
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.15) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: #ffffff !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(255,255,255,0.05);
        border-radius: 15px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        color: rgba(255,255,255,0.7) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #ffffff !important;
    }
    
    .save-indicator-premium {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #00ff88, #00bfff);
        color: #000000 !important;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        z-index: 999;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #4ECDC4, transparent);
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🧠 WORKFLOW BUILDER PRO v7.0</h1>
    <p>Обучаемые ИИ агенты | Email/Outlook | Google Sheets API | Голосовой ввод | Русские условия</p>
    <div style="display: flex; justify-content: center; gap: 0.5rem; margin-top: 0.5rem; flex-wrap: wrap;">
        <span class="badge-premium">✨ ИИ Агенты</span>
        <span class="badge-premium">📧 Email/Outlook</span>
        <span class="badge-premium">📊 Google Sheets</span>
        <span class="badge-premium">🎤 Голосовой ввод</span>
        <span class="badge-premium">💾 Автосохранение</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# НОВЫЕ ФУНКЦИИ: EMAIL, OUTLOOK, GOOGLE SHEETS
# ============================================================================

class EmailSender:
    """Класс для отправки email через SMTP"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, smtp_server: str = "smtp.gmail.com", 
                   smtp_port: int = 587, sender_email: str = None, sender_password: str = None) -> Dict:
        """Отправляет email через SMTP"""
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
            
            return {
                "success": True,
                "to": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_outlook(to_email: str, subject: str, body: str, sender_email: str = None, 
                     sender_password: str = None) -> Dict:
        """Отправляет email через Outlook SMTP"""
        return EmailSender.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            sender_email=sender_email,
            sender_password=sender_password
        )

class GoogleSheetsManager:
    """Класс для работы с Google Sheets API"""
    
    def __init__(self, credentials_json: str = None):
        self.client = None
        self.sheet = None
        if credentials_json:
            self.authenticate(credentials_json)
    
    def authenticate(self, credentials_json: str):
        """Аутентификация через сервисный аккаунт"""
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
        """Открывает Google таблицу"""
        try:
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
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
        """Добавляет строку в конец таблицы"""
        try:
            self.worksheet.append_row(row_data, value_input_option='USER_ENTERED')
            return {
                "success": True,
                "row": row_data,
                "timestamp": datetime.now().isoformat(),
                "row_number": len(self.worksheet.get_all_values()) + 1
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_cell(self, row: int, col: int, value: str) -> Dict:
        """Обновляет конкретную ячейку"""
        try:
            self.worksheet.update_cell(row, col, value)
            return {
                "success": True,
                "cell": f"{chr(64+col)}{row}",
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_data(self) -> List[List]:
        """Получает все данные из таблицы"""
        try:
            return self.worksheet.get_all_values()
        except Exception as e:
            st.error(f"Ошибка получения данных: {e}")
            return []
    
    def find_last_row(self, column: str = 'A') -> int:
        """Находит последнюю заполненную строку в столбце"""
        try:
            col_data = self.worksheet.col_values(ord(column) - 64)
            return len(col_data)
        except Exception as e:
            return 0

class VoiceInput:
    """Класс для голосового ввода"""
    
    @staticmethod
    def recognize_speech() -> str:
        """Распознает речь с микрофона"""
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("🎤 Слушаю... Говорите...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                st.info("🔄 Распознаю...")
                
            try:
                text = recognizer.recognize_google(audio, language='ru-RU')
                return text
            except sr.UnknownValueError:
                return "❌ Не удалось распознать речь"
            except sr.RequestError as e:
                return f"❌ Ошибка сервиса: {e}"
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    @staticmethod
    def text_to_speech(text: str):
        """Озвучивает текст (упрощенная версия)"""
        # Для простоты используем системный TTS
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return True
        except:
            return False

# ============================================================================
# ФУНКЦИИ ДЛЯ СОХРАНЕНИЯ
# ============================================================================

def save_agents_to_file(agents_dict, filepath='agents.json'):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(agents_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

def load_agents_from_file(filepath='agents.json'):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_workflows_to_file(workflows_dict, filepath='workflows.json'):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflows_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения workflows: {e}")
        return False

def load_workflows_from_file(filepath='workflows.json'):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

# ============================================================================
# КЛАСС ДЛЯ ПРЕОБРАЗОВАНИЯ РУССКИХ УСЛОВИЙ
# ============================================================================

class RussianConditionParser:
    @staticmethod
    def parse(condition_text: str) -> Dict:
        condition_text = condition_text.lower().strip()
        
        result = {
            'original': condition_text,
            'type': 'unknown',
            'condition': condition_text,
            'code': None
        }
        
        if 'если' in condition_text and 'то' in condition_text:
            match = re.search(r'если\s+(.+?)\s+то', condition_text)
            if match:
                condition_part = match.group(1)
                result['type'] = 'if_then'
                result['condition'] = condition_part
                result['code'] = f"if {condition_part}:"
        
        elif 'иначе' in condition_text:
            parts = condition_text.split('иначе')
            if len(parts) == 2:
                result['type'] = 'if_else'
                result['true_branch'] = parts[0].replace('если', '').strip()
                result['false_branch'] = parts[1].strip()
                result['code'] = f"if {result['true_branch']}:\n    # действие\nelse:\n    # другое действие"
        
        return result
    
    @staticmethod
    def evaluate(condition_text: str, context: Dict) -> bool:
        try:
            condition_text = condition_text.lower()
            
            if 'больше' in condition_text:
                match = re.search(r'(\w+)\s+больше\s+(\d+)', condition_text)
                if match:
                    var_name = match.group(1)
                    value = float(match.group(2))
                    context_value = context.get(var_name, 0)
                    return float(context_value) > value
            
            elif 'меньше' in condition_text:
                match = re.search(r'(\w+)\s+меньше\s+(\d+)', condition_text)
                if match:
                    var_name = match.group(1)
                    value = float(match.group(2))
                    context_value = context.get(var_name, 0)
                    return float(context_value) < value
            
            elif 'равно' in condition_text:
                match = re.search(r'(\w+)\s+равно\s+(.+)', condition_text)
                if match:
                    var_name = match.group(1)
                    value = match.group(2).strip().strip("'\"")
                    context_value = context.get(var_name, '')
                    return str(context_value) == value
            
            return True
        except Exception:
            return False

# ============================================================================
# КЛАСС ДЛЯ ХРАНЕНИЯ И ОБУЧЕНИЯ ИИ АГЕНТОВ
# ============================================================================

class AIAgent:
    def __init__(self, name: str, role: str, system_prompt: str, agent_id: str = None, avatar_emoji: str = "🧠"):
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
    
    def get_context_summary(self) -> str:
        summary = f"Роль: {self.role}\n"
        summary += f"Память: {len(self.memory)} фактов\n"
        summary += f"Обучен на: {len(self.training_examples)} примерах\n"
        return summary
    
    def find_similar_examples(self, user_input: str, limit: int = 3) -> List[Dict]:
        user_input_lower = user_input.lower()
        scored_examples = []
        
        for example in self.training_examples:
            score = 0
            words = user_input_lower.split()
            for word in words:
                if len(word) > 3 and word in example['user_input'].lower():
                    score += 1
            scored_examples.append((score, example))
        
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex for score, ex in scored_examples[:limit] if score > 0]
    
    def generate_response(self, user_input: str, api_key: str, use_training: bool = True) -> str:
        if not api_key:
            return "❌ API ключ не указан. Получите бесплатно на platform.deepseek.com"
        
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            
            similar_examples = []
            if use_training:
                similar_examples = self.find_similar_examples(user_input)
            
            memory_context = ""
            if self.memory:
                memory_context = "\n\nЗНАНИЯ АГЕНТА (из памяти):\n"
                for mem in self.memory[-5:]:
                    memory_context += f"- {mem['key']}: {mem['value']}\n"
            
            training_context = ""
            if similar_examples:
                training_context = "\n\nПРИМЕРЫ ОБУЧЕНИЯ:\n"
                for ex in similar_examples[:3]:
                    training_context += f"Пользователь: {ex['user_input']}\n"
                    training_context += f"Правильный ответ: {ex['expected_output']}\n\n"
            
            full_prompt = f"""
Ты - ИИ агент с именем "{self.name}" и ролью "{self.role}".

{self.system_prompt}

{memory_context}

{training_context}

Текущий запрос пользователя: "{user_input}"

Ответь, используя полученные знания, примеры обучения и память.
Будь полезным, точным и дружелюбным. Отвечай на русском языке.
"""
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            answer = response.choices[0].message.content
            self.add_conversation(user_input, answer)
            return answer
            
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'system_prompt': self.system_prompt,
            'avatar_emoji': self.avatar_emoji,
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
            agent_id=data['id'],
            avatar_emoji=data.get('avatar_emoji', '🧠')
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
# КЛАСС ДЛЯ ВЫПОЛНЕНИЯ WORKFLOW (С НОВЫМИ БЛОКАМИ)
# ============================================================================

class WorkflowExecutor:
    def __init__(self, workflow: List[Dict], api_key: str = None, agent_manager: 'AgentManager' = None):
        self.workflow = workflow
        self.api_key = api_key
        self.agent_manager = agent_manager
        self.context = {}
        self.results = []
        self.current_node_index = 0
        self.email_sender = None
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
        elif node_type == 'http_get':
            return self._execute_http_get(config)
        elif node_type == 'http_post':
            return self._execute_http_post(config)
        else:
            return {'status': 'unknown_type', 'type': node_type}
    
    def _execute_google_sheets_read(self, config: Dict) -> Dict:
        sheet_url = config.get('sheet_url', '')
        if not sheet_url:
            return {'error': 'URL не указан'}
        
        try:
            if '/d/' in sheet_url:
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url
            
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            df = pd.read_csv(csv_url)
            return {
                'data': df.to_dict('records'),
                'rows': len(df),
                'columns': list(df.columns)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_google_sheets_write(self, config: Dict) -> Dict:
        """Запись данных в Google Sheets"""
        sheet_url = config.get('sheet_url', '')
        credentials_json = config.get('credentials_json', '')
        column_mapping = config.get('column_mapping', {})
        text_to_write = config.get('text_to_write', '')
        
        if not sheet_url:
            return {'error': 'URL таблицы не указан'}
        
        if not credentials_json:
            return {'error': 'Не указаны учетные данные Google Sheets'}
        
        try:
            # Инициализируем менеджер
            self.gs_manager = GoogleSheetsManager(credentials_json)
            
            # Открываем таблицу
            worksheet_name = config.get('worksheet_name', None)
            if not self.gs_manager.open_sheet(sheet_url, worksheet_name):
                return {'error': 'Не удалось открыть таблицу'}
            
            # Получаем данные из контекста или из текста
            data_to_write = {}
            
            # Если есть маппинг колонок, используем его
            if column_mapping:
                for col_name, source in column_mapping.items():
                    if source.startswith('{{') and source.endswith('}}'):
                        var_name = source[2:-2]
                        data_to_write[col_name] = self.context.get(var_name, '')
                    else:
                        data_to_write[col_name] = source
            elif text_to_write:
                # Парсим текст для вставки в определенные столбцы
                lines = text_to_write.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        col, val = line.split(':', 1)
                        data_to_write[col.strip()] = val.strip()
            
            # Находим последнюю строку
            last_row = self.gs_manager.find_last_row('A')
            new_row_number = last_row + 1
            
            # Создаем массив для строки
            max_col = 26  # до Z
            row_data = [''] * max_col
            
            for col_name, value in data_to_write.items():
                col_index = ord(col_name.upper()) - 65 if col_name else 0
                if 0 <= col_index < max_col:
                    row_data[col_index] = str(value)
            
            # Добавляем строку
            result = self.gs_manager.append_row(row_data)
            
            if result['success']:
                return {
                    'success': True,
                    'row_added': new_row_number,
                    'data': data_to_write,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_email_send(self, config: Dict) -> Dict:
        """Отправка email через SMTP"""
        to_email = config.get('to', '')
        subject = config.get('subject', 'Уведомление от Workflow Builder')
        body = config.get('body', '')
        sender_email = config.get('sender_email', '')
        sender_password = config.get('sender_password', '')
        
        # Подставляем переменные из контекста
        for key, value in self.context.items():
            if isinstance(value, str):
                body = body.replace(f"{{{{{key}}}}}", value)
                subject = subject.replace(f"{{{{{key}}}}}", value)
        
        result = EmailSender.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            sender_email=sender_email,
            sender_password=sender_password
        )
        
        return result
    
    def _execute_outlook_send(self, config: Dict) -> Dict:
        """Отправка email через Outlook"""
        to_email = config.get('to', '')
        subject = config.get('subject', 'Уведомление от Workflow Builder')
        body = config.get('body', '')
        sender_email = config.get('sender_email', '')
        sender_password = config.get('sender_password', '')
        
        # Подставляем переменные из контекста
        for key, value in self.context.items():
            if isinstance(value, str):
                body = body.replace(f"{{{{{key}}}}}", value)
                subject = subject.replace(f"{{{{{key}}}}}", value)
        
        result = EmailSender.send_outlook(
            to_email=to_email,
            subject=subject,
            body=body,
            sender_email=sender_email,
            sender_password=sender_password
        )
        
        return result
    
    def _execute_voice_input(self, config: Dict) -> Dict:
        """Голосовой ввод текста"""
        try:
            text = VoiceInput.recognize_speech()
            return {
                'success': True,
                'text': text,
                'timestamp': datetime.now().isoformat()
            }
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
        result = RussianConditionParser.evaluate(condition_text, self.context)
        
        return {
            'condition': condition_text,
            'result': result
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

# ============================================================================
# МЕНЕДЖЕР АГЕНТОВ
# ============================================================================

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.current_agent_id: Optional[str] = None
        self.load_agents()
    
    def load_agents(self):
        agents_data = load_agents_from_file()
        
        if not agents_data:
            default_agents = self._create_default_agents()
            for agent in default_agents:
                self.agents[agent.id] = agent
            self.save_agents()
        else:
            for agent_id, agent_dict in agents_data.items():
                self.agents[agent_id] = AIAgent.from_dict(agent_dict)
        
        if self.agents and not self.current_agent_id:
            self.current_agent_id = list(self.agents.keys())[0]
    
    def _create_default_agents(self) -> List[AIAgent]:
        agents = []
        
        analyst = AIAgent(
            name="Аналитик Данных",
            role="эксперт по анализу данных и бизнес-метрикам",
            system_prompt="Ты профессиональный аналитик данных. Анализируй цифры и давай рекомендации.",
            avatar_emoji="📊"
        )
        agents.append(analyst)
        
        automation = AIAgent(
            name="Автоматизатор",
            role="специалист по автоматизации бизнес-процессов",
            system_prompt="Ты эксперт по автоматизации. Предлагай решения для оптимизации процессов.",
            avatar_emoji="⚙️"
        )
        agents.append(automation)
        
        return agents
    
    def save_agents(self):
        agents_dict = {agent_id: agent.to_dict() for agent_id, agent in self.agents.items()}
        save_agents_to_file(agents_dict)
    
    def add_agent(self, name: str, role: str, system_prompt: str, avatar_emoji: str = "🧠") -> AIAgent:
        agent = AIAgent(name, role, system_prompt, avatar_emoji=avatar_emoji)
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
    
    def get_agents_list(self) -> List[Dict]:
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

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ СЕССИИ
# ============================================================================

if 'agent_manager' not in st.session_state:
    st.session_state.agent_manager = AgentManager()
if 'workflow' not in st.session_state:
    st.session_state.workflow = []
if 'agent_messages' not in st.session_state:
    st.session_state.agent_messages = []
if 'workflows' not in st.session_state:
    st.session_state.workflows = load_workflows_from_file()
if 'analytics' not in st.session_state:
    st.session_state.analytics = {
        'total_executions': 0,
        'successful_executions': 0,
        'failed_executions': 0
    }

agent_manager = st.session_state.agent_manager

if agent_manager.agents:
    st.success(f"✅ Загружено {len(agent_manager.agents)} агентов из файла")
else:
    st.info("📁 Создайте первого агента - он автоматически сохранится")

# ============================================================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================================================

with st.sidebar:
    st.markdown("## 🔑 API НАСТРОЙКИ")
    
    api_key = st.text_input(
        "DeepSeek API Ключ",
        type="password",
        help="Нужен для работы ИИ агентов. Бесплатно на platform.deepseek.com",
        key="api_key_main"
    )
    
    st.markdown("---")
    st.markdown("## 📧 EMAIL НАСТРОЙКИ")
    
    smtp_server = st.selectbox("SMTP сервер", ["smtp.gmail.com", "smtp-mail.outlook.com", "smtp.yandex.ru", "smtp.mail.ru"], key="smtp_server")
    sender_email = st.text_input("Email отправителя", key="sender_email", placeholder="your@email.com")
    sender_password = st.text_input("Пароль приложения", type="password", key="sender_password", help="Используйте пароль приложения, не основной пароль")
    
    st.markdown("---")
    st.markdown("## 📊 GOOGLE SHEETS НАСТРОЙКИ")
    
    credentials_json = st.text_area("JSON ключ сервисного аккаунта", height=150, 
                                     placeholder='{"type": "service_account", "project_id": "...", ...}',
                                     help="Получите в Google Cloud Console")
    
    st.markdown("---")
    st.markdown("## 💾 УПРАВЛЕНИЕ")
    
    if st.button("💾 Сохранить всё", use_container_width=True):
        agent_manager.save_agents()
        save_workflows_to_file(st.session_state.workflows)
        st.success("✅ Все данные сохранены!")
        time.sleep(1)
        st.rerun()
    
    if st.button("🗑️ Очистить workflow", use_container_width=True):
        st.session_state.workflow = []
        st.rerun()

# ============================================================================
# ОСНОВНЫЕ ВКЛАДКИ
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "💬 ДИАЛОГ С АГЕНТОМ",
    "📚 ОБУЧЕНИЕ",
    "🧠 ПАМЯТЬ",
    "📊 АНАЛИТИКА",
    "🤖 WORKFLOW",
    "📧 EMAIL/OUTLOOK",
    "📊 GOOGLE SHEETS",
    "🎤 ГОЛОСОВОЙ ВВОД"
])

# ============================================================================
# ВКЛАДКА 1: ДИАЛОГ С АГЕНТОМ
# ============================================================================

with tab1:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Нет выбранного агента. Создайте или выберите агента в боковой панели")
    else:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <div style="font-size: 3rem;">{current_agent.avatar_emoji}</div>
            <div>
                <h2 style="margin: 0; color: #ffffff;">{current_agent.name}</h2>
                <p style="margin: 0; color: #cccccc;">{current_agent.role}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for msg in st.session_state.agent_messages:
            if msg['role'] == 'user':
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
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            user_input = st.text_area("✏️ Ваше сообщение:", height=80, key="agent_input", 
                                      label_visibility="collapsed", placeholder="Напишите сообщение...")
        with col2:
            use_training = st.checkbox("Использовать обучение", value=True)
        with col3:
            if st.button("🎤 Голосовой ввод", use_container_width=True):
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
        
        if st.button("🗑️ Очистить историю диалога", use_container_width=True):
            st.session_state.agent_messages = []
            st.rerun()

# ============================================================================
# ВКЛАДКА 2: ОБУЧЕНИЕ
# ============================================================================

with tab2:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента в боковой панели")
    else:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">{current_agent.avatar_emoji}</div>
            <div>
                <h2 style="margin: 0;">Обучение {current_agent.name}</h2>
                <p>Обучите агента правильным ответам на ваши вопросы</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("➕ ДОБАВИТЬ ПРИМЕР ДЛЯ ОБУЧЕНИЯ", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                example_input = st.text_area("📝 Вопрос/Запрос пользователя:", height=100, key="train_input")
            with col2:
                example_output = st.text_area("✅ Ожидаемый ответ агента:", height=100, key="train_output")
            
            if st.button("✨ Добавить пример обучения", type="primary"):
                if example_input and example_output:
                    current_agent.add_training_example(example_input, example_output)
                    agent_manager.save_agents()
                    st.success("✅ Пример добавлен!")
                    st.rerun()
                else:
                    st.warning("Заполните вопрос и ответ")
        
        st.markdown("---")
        st.subheader(f"📚 Примеры обучения ({len(current_agent.training_examples)})")
        
        if current_agent.training_examples:
            for i, example in enumerate(reversed(current_agent.training_examples[-10:])):
                with st.expander(f"Пример {i+1}: {example['user_input'][:50]}..."):
                    st.markdown(f"**Вопрос:** {example['user_input']}")
                    st.markdown(f"**Ответ:** {example['expected_output']}")
                    if st.button(f"🗑️ Удалить", key=f"del_example_{i}"):
                        current_agent.training_examples.remove(example)
                        agent_manager.save_agents()
                        st.rerun()
        else:
            st.info("Пока нет примеров обучения.")

# ============================================================================
# ВКЛАДКА 3: ПАМЯТЬ
# ============================================================================

with tab3:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента")
    else:
        st.subheader(f"🧠 Память {current_agent.name}")
        
        with st.expander("➕ ДОБАВИТЬ В ПАМЯТЬ", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                memory_key = st.text_input("📌 Ключ:", placeholder="любимый_цвет")
            with col2:
                memory_value = st.text_input("💾 Значение:", placeholder="синий")
            
            if st.button("💾 Сохранить в память", type="primary"):
                if memory_key and memory_value:
                    current_agent.add_to_memory(memory_key, memory_value)
                    agent_manager.save_agents()
                    st.success(f"✅ Запомнено: {memory_key} = {memory_value}")
                    st.rerun()
        
        st.markdown("---")
        st.subheader(f"📚 Память ({len(current_agent.memory)})")
        
        if current_agent.memory:
            for mem in current_agent.memory:
                st.markdown(f"**🔑 {mem['key']}:** {mem['value']}")
                if st.button(f"🗑️ Удалить", key=f"del_mem_{mem['key']}"):
                    current_agent.memory.remove(mem)
                    agent_manager.save_agents()
                    st.rerun()
        else:
            st.info("Память пуста.")

# ============================================================================
# ВКЛАДКА 4: АНАЛИТИКА
# ============================================================================

with tab4:
    current_agent = agent_manager.get_current_agent()
    
    if current_agent:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎓 Обучений", current_agent.stats['total_trainings'])
        with col2:
            st.metric("💬 Диалогов", current_agent.stats['total_conversations'])
        with col3:
            st.metric("✅ Успешность", f"{current_agent.stats['success_rate']:.0f}%")
        with col4:
            st.metric("🧠 Память", len(current_agent.memory))
    
    st.markdown("---")
    st.subheader("📈 Общая статистика")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего агентов", len(agent_manager.agents))
    with col2:
        st.metric("Workflow выполнено", st.session_state.analytics['total_executions'])
    with col3:
        st.metric("Успешных запусков", st.session_state.analytics['successful_executions'])

# ============================================================================
# ВКЛАДКА 5: WORKFLOW
# ============================================================================

with tab5:
    st.subheader("🤖 Конструктор workflow")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📦 Блоки")
        
        block_types = [
            ("📖 Google Sheets (чтение)", "google_sheets_read"),
            ("✍️ Google Sheets (запись)", "google_sheets_write"),
            ("📧 Email (SMTP)", "email_send"),
            ("📱 Outlook", "outlook_send"),
            ("🎤 Голосовой ввод", "voice_input"),
            ("🧠 DeepSeek AI", "deepseek"),
            ("🔀 Условие", "condition"),
            ("📡 HTTP GET", "http_get"),
            ("📤 HTTP POST", "http_post"),
        ]
        
        for name, btype in block_types:
            if st.button(f"{name}", key=f"add_{btype}", use_container_width=True):
                st.session_state.workflow.append({
                    "id": len(st.session_state.workflow),
                    "name": name,
                    "type": btype,
                    "config": {},
                    "status": "pending"
                })
                st.rerun()
    
    with col2:
        st.markdown("### 📋 Текущий workflow")
        
        if st.session_state.workflow:
            for i, block in enumerate(st.session_state.workflow):
                st.markdown(f"""
                <div class="workflow-node">
                    <b>Шаг {i+1}: {block['name']}</b>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"⚙️ Настроить {block['name']}"):
                    block_type = block['type']
                    config = block.get('config', {})
                    
                    if block_type == 'google_sheets_read':
                        config['sheet_url'] = st.text_input("URL таблицы", config.get('sheet_url', ''), key=f"gs_url_{i}")
                    
                    elif block_type == 'google_sheets_write':
                        config['sheet_url'] = st.text_input("URL таблицы", config.get('sheet_url', ''), key=f"gs_write_url_{i}")
                        config['worksheet_name'] = st.text_input("Название листа", config.get('worksheet_name', ''), key=f"gs_sheet_{i}")
                        st.markdown("**Маппинг колонок (формат: A:{{переменная}} или B:текст):**")
                        mapping_text = st.text_area("Колонки", config.get('column_mapping_text', ''), height=100, key=f"gs_mapping_{i}")
                        if mapping_text:
                            mapping = {}
                            for line in mapping_text.strip().split('\n'):
                                if ':' in line:
                                    col, val = line.split(':', 1)
                                    mapping[col.strip()] = val.strip()
                            config['column_mapping'] = mapping
                            config['column_mapping_text'] = mapping_text
                    
                    elif block_type in ['email_send', 'outlook_send']:
                        config['to'] = st.text_input("Кому", config.get('to', ''), key=f"email_to_{i}")
                        config['subject'] = st.text_input("Тема", config.get('subject', 'Уведомление'), key=f"email_subj_{i}")
                        config['body'] = st.text_area("Сообщение", config.get('body', ''), height=100, key=f"email_body_{i}")
                        config['sender_email'] = st.text_input("Email отправителя", config.get('sender_email', sender_email), key=f"email_from_{i}")
                        config['sender_password'] = st.text_input("Пароль", type="password", config.get('sender_password', sender_password), key=f"email_pass_{i}")
                    
                    elif block_type == 'voice_input':
                        st.info("🎤 При выполнении этого блока будет активирован микрофон")
                    
                    elif block_type == 'deepseek':
                        config['system_prompt'] = st.text_area("System prompt", config.get('system_prompt', 'Ты полезный ассистент'), height=80, key=f"ds_sys_{i}")
                        config['user_prompt'] = st.text_area("User prompt", config.get('user_prompt', ''), height=80, key=f"ds_user_{i}")
                        config['temperature'] = st.slider("Температура", 0.0, 1.0, float(config.get('temperature', 0.3)), key=f"ds_temp_{i}")
                    
                    elif block_type == 'condition':
                        config['condition'] = st.text_area("Условие на русском", config.get('condition', 'если значение больше 100'), height=80, key=f"cond_{i}")
                    
                    elif block_type in ['http_get', 'http_post']:
                        config['url'] = st.text_input("URL", config.get('url', ''), key=f"http_url_{i}")
                        if block_type == 'http_post':
                            config['body'] = st.text_area("Body (JSON)", config.get('body', '{}'), height=80, key=f"http_body_{i}")
                    
                    block['config'] = config
                
                if st.button(f"🗑️ Удалить блок {i+1}", key=f"del_{i}"):
                    st.session_state.workflow.pop(i)
                    st.rerun()
            
            st.markdown("---")
            
            if st.button("🚀 ЗАПУСТИТЬ WORKFLOW", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                credentials_json_str = credentials_json if credentials_json else ""
                
                def update_progress(idx, node):
                    progress_bar.progress((idx + 1) / len(st.session_state.workflow))
                    status_text.text(f"🔄 Выполняется: {node.get('name', 'Block')}")
                
                executor = WorkflowExecutor(st.session_state.workflow, api_key, agent_manager)
                result = executor.execute(update_progress)
                
                progress_bar.progress(1.0)
                
                if result['success']:
                    st.balloons()
                    st.success(f"✅ Workflow выполнен за {result['execution_time']:.1f} сек!")
                    st.session_state.analytics['total_executions'] += 1
                    st.session_state.analytics['successful_executions'] += 1
                    
                    with st.expander("📋 Результаты", expanded=True):
                        for res in result['results']:
                            st.markdown(f"**📌 {res['node']}**")
                            st.json(res['result'])
                else:
                    st.session_state.analytics['total_executions'] += 1
                    st.session_state.analytics['failed_executions'] += 1
                    st.error(f"❌ Ошибка: {result['error']}")
        else:
            st.info("💡 Добавьте блоки из левой колонки")

# ============================================================================
# ВКЛАДКА 6: EMAIL/OUTLOOK
# ============================================================================

with tab6:
    st.subheader("📧 Отправка email через SMTP")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Gmail")
        gmail_to = st.text_input("Кому", key="gmail_to")
        gmail_subject = st.text_input("Тема", key="gmail_subject", value="Тестовое письмо")
        gmail_body = st.text_area("Сообщение", key="gmail_body", height=150, value="Привет! Это тестовое письмо из Workflow Builder.")
        
        if st.button("📧 Отправить через Gmail", type="primary"):
            if sender_email and sender_password and gmail_to:
                with st.spinner("Отправка..."):
                    result = EmailSender.send_email(
                        to_email=gmail_to,
                        subject=gmail_subject,
                        body=gmail_body,
                        sender_email=sender_email,
                        sender_password=sender_password
                    )
                    if result['success']:
                        st.success("✅ Письмо отправлено!")
                    else:
                        st.error(f"❌ Ошибка: {result['error']}")
            else:
                st.warning("Заполните email отправителя и пароль в боковой панели")
    
    with col2:
        st.markdown("### Outlook")
        outlook_to = st.text_input("Кому", key="outlook_to")
        outlook_subject = st.text_input("Тема", key="outlook_subject", value="Тестовое письмо")
        outlook_body = st.text_area("Сообщение", key="outlook_body", height=150, value="Привет! Это тестовое письмо из Workflow Builder.")
        
        if st.button("📧 Отправить через Outlook", type="primary"):
            if sender_email and sender_password and outlook_to:
                with st.spinner("Отправка..."):
                    result = EmailSender.send_outlook(
                        to_email=outlook_to,
                        subject=outlook_subject,
                        body=outlook_body,
                        sender_email=sender_email,
                        sender_password=sender_password
                    )
                    if result['success']:
                        st.success("✅ Письмо отправлено!")
                    else:
                        st.error(f"❌ Ошибка: {result['error']}")
            else:
                st.warning("Заполните email отправителя и пароль в боковой панели")
    
    st.markdown("---")
    st.markdown("### 💡 Условия для отправки")
    st.markdown("""
    В workflow можно задать условия на русском языке:
    - `если статус равно успех то отправить письмо`
    - `если цена больше 1000 отправить уведомление`
    - `если данные содержат ошибка то отправить в Outlook`
    """)

# ============================================================================
# ВКЛАДКА 7: GOOGLE SHEETS
# ============================================================================

with tab7:
    st.subheader("📊 Работа с Google Sheets")
    
    if not credentials_json:
        st.warning("⚠️ Для работы с Google Sheets необходим JSON ключ сервисного аккаунта. Добавьте его в боковой панели.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📖 Чтение данных")
        read_sheet_url = st.text_input("URL таблицы", key="read_sheet_url", placeholder="https://docs.google.com/spreadsheets/d/...")
        
        if st.button("📖 Прочитать таблицу", type="primary"):
            if credentials_json and read_sheet_url:
                with st.spinner("Чтение..."):
                    gs = GoogleSheetsManager(credentials_json)
                    if gs.open_sheet(read_sheet_url):
                        data = gs.get_all_data()
                        if data:
                            df = pd.DataFrame(data)
                            st.dataframe(df, use_container_width=True)
                            st.success(f"✅ Прочитано {len(data)} строк")
                        else:
                            st.info("Таблица пуста")
                    else:
                        st.error("Не удалось открыть таблицу")
            else:
                st.warning("Укажите URL таблицы и JSON ключ")
    
    with col2:
        st.markdown("### ✍️ Запись данных")
        write_sheet_url = st.text_input("URL таблицы", key="write_sheet_url", placeholder="https://docs.google.com/spreadsheets/d/...")
        
        st.markdown("**Данные для записи (формат: столбец:значение):**")
        write_data = st.text_area("Данные", height=150, placeholder="A: Значение 1\nB: Значение 2\nC: Значение 3")
        
        if st.button("✍️ Записать в таблицу", type="primary"):
            if credentials_json and write_sheet_url and write_data:
                with st.spinner("Запись..."):
                    gs = GoogleSheetsManager(credentials_json)
                    if gs.open_sheet(write_sheet_url):
                        row_data = [''] * 26
                        for line in write_data.strip().split('\n'):
                            if ':' in line:
                                col, val = line.split(':', 1)
                                col_idx = ord(col.strip().upper()) - 65
                                if 0 <= col_idx < 26:
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
    st.markdown("### 💡 Примеры использования")
    st.markdown("""
    **В workflow можно настроить запись в определенные столбцы ниже записанных данных:**
    
    1. Добавьте блок **"Google Sheets (запись)"** в workflow
    2. Настройте маппинг колонок:
            3. Переменные `{{имя}}`, `{{email}}`, `{{сообщение}}` будут подставлены из контекста выполнения
4. Данные будут добавлены в конец таблицы
""")

# ============================================================================
# ВКЛАДКА 8: ГОЛОСОВОЙ ВВОД
# ============================================================================

with tab8:
st.subheader("🎤 Голосовой ввод текста")

st.markdown("""
<div class="info-box-premium">
 <h4>🎯 Как это работает?</h4>
 <p>Нажмите на кнопку ниже и произнесите текст. Система распознает речь и преобразует её в текст.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
 if st.button("🎤 НАЧАТЬ ЗАПИСЬ", type="primary", use_container_width=True):
     with st.spinner("🎤 Слушаю..."):
         recognized_text = VoiceInput.recognize_speech()
         st.session_state.recognized_text = recognized_text
         st.rerun()
 
 if st.button("🔊 Озвучить текст", use_container_width=True):
     if 'recognized_text' in st.session_state and st.session_state.recognized_text:
         VoiceInput.text_to_speech(st.session_state.recognized_text)

with col2:
 st.markdown("### 📝 Распознанный текст")
 if 'recognized_text' in st.session_state and st.session_state.recognized_text:
     st.text_area("Текст", st.session_state.recognized_text, height=200, key="voice_result")
     
     if st.button("📋 Скопировать текст"):
         st.write("✅ Текст скопирован в буфер обмена")
         st.session_state.voice_copy = st.session_state.recognized_text

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
# ПОДВАЛ
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem;">
<p>🧠 Workflow Builder PRO v7.0 | Email/Outlook | Google Sheets API | Голосовой ввод</p>
<p style="font-size: 0.7rem;">📁 Файлы: agents.json | workflows.json</p>
</div>
""", unsafe_allow_html=True)
