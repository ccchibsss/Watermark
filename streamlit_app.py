"""
================================================================================
КОНСТРУКТОР WORKFLOW PRO v7.0 - ПОЛНАЯ ВЕРСИЯ (РАСШИРЕННАЯ)
Обучаемые ИИ агенты | Сохранение | Русские условия | Полный функционал
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
# ПРЕМИУМ СТИЛИ
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
        color: #ffffff;
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
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #fff, #ffd89b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .main-header p {
        font-size: 1rem;
        color: rgba(255,255,255,0.95);
        margin-top: 0.5rem;
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
        box-shadow: 0 5px 15px rgba(78,205,196,0.2);
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
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        animation: slideInRight 0.3s ease;
    }
    
    .chat-message-agent {
        background: linear-gradient(135deg, rgba(26,26,46,0.9), rgba(22,30,62,0.9));
        border-radius: 20px;
        padding: 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
        border-left: 4px solid #4ECDC4;
        animation: slideInLeft 0.3s ease;
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
        background: linear-gradient(135deg, #fff, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    .workflow-node-success {
        border-left-color: #00ff88;
        background: linear-gradient(135deg, rgba(10,46,31,0.9), rgba(10,26,16,0.9));
    }
    
    .workflow-node-error {
        border-left-color: #ff4444;
        background: linear-gradient(135deg, rgba(62,26,26,0.9), rgba(42,15,15,0.9));
    }
    
    .training-card-premium {
        background: linear-gradient(135deg, rgba(26,26,46,0.9), rgba(22,30,62,0.9));
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-left: 4px solid #FFD700;
        transition: all 0.3s ease;
    }
    
    .training-card-premium:hover {
        transform: translateX(5px);
    }
    
    .memory-box {
        background: rgba(30,30,46,0.9);
        backdrop-filter: blur(10px);
        padding: 0.8rem;
        border-radius: 10px;
        border-left: 4px solid #ffa500;
        margin: 0.5rem 0;
    }
    
    .info-box-premium {
        background: rgba(30,30,46,0.9);
        backdrop-filter: blur(10px);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
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
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        color: white;
        padding: 0.5rem;
    }
    
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #4ECDC4;
        box-shadow: 0 0 0 2px rgba(78,205,196,0.2);
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
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        background-size: 200% 100%;
        animation: gradientProgress 2s ease infinite;
    }
    
    @keyframes gradientProgress {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    .badge-premium {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    
    .save-indicator-premium {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #00ff88, #00bfff);
        color: #000;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        z-index: 999;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.9; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-weight: 700;
        background: linear-gradient(135deg, #fff, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
    <p>Обучаемые ИИ агенты | Сохранение контекста | Персональные помощники | Русские условия</p>
    <div style="display: flex; justify-content: center; gap: 0.5rem; margin-top: 0.5rem;">
        <span class="badge-premium">✨ ИИ Агенты</span>
        <span class="badge-premium">💾 Автосохранение</span>
        <span class="badge-premium">🎨 Премиум дизайн</span>
        <span class="badge-premium">🚀 Высокая производительность</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# ФУНКЦИИ ДЛЯ СОХРАНЕНИЯ
# ============================================================================

def save_agents_to_file(agents_dict, filepath='agents.json'):
    """Сохранение агентов в файл"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(agents_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

def load_agents_from_file(filepath='agents.json'):
    """Загрузка агентов из файла"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_workflows_to_file(workflows_dict, filepath='workflows.json'):
    """Сохранение workflows в файл"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflows_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения workflows: {e}")
        return False

def load_workflows_from_file(filepath='workflows.json'):
    """Загрузка workflows из файла"""
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
    """Преобразует условия на русском языке в исполняемый код"""
    
    @staticmethod
    def parse(condition_text: str) -> Dict:
        """Преобразует русское условие в структуру"""
        condition_text = condition_text.lower().strip()
        
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
        """Выполняет проверку условия"""
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
            
            elif 'содержит' in condition_text:
                match = re.search(r'(\w+)\s+содержит\s+(.+)', condition_text)
                if match:
                    var_name = match.group(1)
                    value = match.group(2).strip().strip("'\"")
                    context_value = str(context.get(var_name, ''))
                    return value in context_value
            
            return True
        except Exception:
            return False

# ============================================================================
# КЛАСС ДЛЯ ХРАНЕНИЯ И ОБУЧЕНИЯ ИИ АГЕНТОВ
# ============================================================================

class AIAgent:
    """Класс для создания и обучения ИИ агентов"""
    
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
        """Добавляет пример для обучения"""
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
        """Сохраняет в долговременную память агента"""
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
        """Получает из памяти агента"""
        for mem in self.memory:
            if mem['key'] == key:
                mem['access_count'] += 1
                return mem['value']
        return None
    
    def add_conversation(self, user_message: str, agent_response: str, feedback: str = None):
        """Сохраняет диалог для дальнейшего обучения"""
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
        """Возвращает краткую сводку контекста агента"""
        summary = f"Роль: {self.role}\n"
        summary += f"Память: {len(self.memory)} фактов\n"
        summary += f"Обучен на: {len(self.training_examples)} примерах\n"
        return summary
    
    def find_similar_examples(self, user_input: str, limit: int = 3) -> List[Dict]:
        """Находит похожие примеры обучения"""
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
        """Генерирует ответ с учётом обучения и памяти"""
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
        """Экспортирует агента в словарь для сохранения"""
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
        """Создаёт агента из словаря"""
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
# КЛАСС ДЛЯ ВЫПОЛНЕНИЯ WORKFLOW
# ============================================================================

class WorkflowExecutor:
    """Выполняет workflow с поддержкой условий на русском"""
    
    def __init__(self, workflow: List[Dict], api_key: str = None, agent_manager: 'AgentManager' = None):
        self.workflow = workflow
        self.api_key = api_key
        self.agent_manager = agent_manager
        self.context = {}
        self.results = []
        self.current_node_index = 0
    
    def execute(self, progress_callback=None) -> Dict:
        """Запускает выполнение workflow"""
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
        """Выполняет отдельный узел"""
        node_type = node.get('type')
        config = node.get('config', {})
        
        if node_type == 'google_sheets_read':
            return self._execute_google_sheets(config)
        elif node_type == 'deepseek':
            return self._execute_deepseek(config)
        elif node_type == 'http_get':
            return self._execute_http_get(config)
        elif node_type == 'http_post':
            return self._execute_http_post(config)
        elif node_type == 'condition':
            return self._execute_condition(config)
        elif node_type == 'loop':
            return self._execute_loop(config)
        elif node_type == 'email':
            return self._execute_email(config)
        elif node_type == 'telegram':
            return self._execute_telegram(config)
        elif node_type == 'ai_agent':
            return self._execute_ai_agent(config)
        else:
            return {'status': 'unknown_type', 'type': node_type}
    
    def _execute_google_sheets(self, config: Dict) -> Dict:
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
# МЕНЕДЖЕР АГЕНТОВ
# ============================================================================

class AgentManager:
    """Управляет всеми ИИ агентами"""
    
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.current_agent_id: Optional[str] = None
        self.load_agents()
    
    def load_agents(self):
        """Загружает агентов из хранилища"""
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
        """Создаёт агентов по умолчанию"""
        agents = []
        
        analyst = AIAgent(
            name="Аналитик Данных",
            role="эксперт по анализу данных и бизнес-метрикам",
            system_prompt="""Ты профессиональный аналитик данных. Твоя задача:
- Анализировать цифры и метрики
- Находить закономерности и тренды
- Давать практические рекомендации
- Объяснять сложные вещи простым языком""",
            avatar_emoji="📊"
        )
        agents.append(analyst)
        
        automation = AIAgent(
            name="Автоматизатор",
            role="специалист по автоматизации бизнес-процессов",
            system_prompt="""Ты эксперт по автоматизации. Твоя задача:
- Предлагать решения для автоматизации
- Оптимизировать рабочие процессы
- Указывать на узкие места
- Давать пошаговые инструкции""",
            avatar_emoji="⚙️"
        )
        agents.append(automation)
        
        manager = AIAgent(
            name="Менеджер Задач",
            role="помощник по управлению задачами и проектами",
            system_prompt="""Ты менеджер проектов. Твоя задача:
- Помогать планировать задачи
- Приоритезировать дела
- Напоминать о важных вещах
- Отслеживать прогресс""",
            avatar_emoji="📋"
        )
        agents.append(manager)
        
        return agents
    
    def save_agents(self):
        """Сохраняет агентов в файл"""
        agents_dict = {agent_id: agent.to_dict() for agent_id, agent in self.agents.items()}
        save_agents_to_file(agents_dict)
    
    def add_agent(self, name: str, role: str, system_prompt: str, avatar_emoji: str = "🧠") -> AIAgent:
        """Добавляет нового агента"""
        agent = AIAgent(name, role, system_prompt, avatar_emoji=avatar_emoji)
        self.agents[agent.id] = agent
        self.save_agents()
        return agent
    
    def delete_agent(self, agent_id: str):
        """Удаляет агента"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            if self.current_agent_id == agent_id:
                self.current_agent_id = next(iter(self.agents.keys())) if self.agents else None
            self.save_agents()
    
    def get_current_agent(self) -> Optional[AIAgent]:
        """Возвращает текущего агента"""
        if self.current_agent_id and self.current_agent_id in self.agents:
            return self.agents[self.current_agent_id]
        return None
    
    def set_current_agent(self, agent_id: str):
        """Устанавливает текущего агента"""
        if agent_id in self.agents:
            self.current_agent_id = agent_id
            self.save_agents()
    
    def export_agent(self, agent_id: str) -> str:
        """Экспортирует агента в JSON строку"""
        if agent_id in self.agents:
            return json.dumps(self.agents[agent_id].to_dict(), ensure_ascii=False, indent=2)
        return ""
    
    def import_agent(self, agent_json: str) -> bool:
        """Импортирует агента из JSON строки"""
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

# Показываем статус загрузки
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
    st.markdown("## 💾 УПРАВЛЕНИЕ ДАННЫМИ")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Сохранить всё", use_container_width=True):
            agent_manager.save_agents()
            save_workflows_to_file(st.session_state.workflows)
            st.success("✅ Все данные сохранены!")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("🔄 Перезагрузить", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Статус сохранения
    if os.path.exists('agents.json'):
        mod_time = os.path.getmtime('agents.json')
        last_save = datetime.fromtimestamp(mod_time).strftime("%H:%M:%S")
        file_size = os.path.getsize('agents.json')
        st.caption(f"📁 agents.json: {file_size} байт")
        st.caption(f"💾 Последнее сохранение: {last_save}")
    
    st.markdown("---")
    st.markdown("## 🧠 МОИ ИИ АГЕНТЫ")
    
    # Список агентов
    agents_list = agent_manager.get_agents_list()
    
    if agents_list:
        for agent in agents_list:
            is_selected = agent_manager.current_agent_id == agent['id']
            selected_class = " agent-card-selected" if is_selected else ""
            
            st.markdown(f"""
            <div class="agent-card{selected_class}">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">{agent['avatar']}</span>
                    <div style="flex: 1;">
                        <strong>{agent['name']}</strong>
                        <div style="font-size: 0.7rem; opacity: 0.7;">{agent['role'][:30]}</div>
                    </div>
                    <div style="font-size: 0.7rem;">🎓 {agent['trainings']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"📋 Выбрать", key=f"select_{agent['id']}", use_container_width=True):
                    agent_manager.set_current_agent(agent['id'])
                    st.rerun()
            with col2:
                if st.button(f"🗑️", key=f"del_{agent['id']}"):
                    agent_manager.delete_agent(agent['id'])
                    st.rerun()
    else:
        st.info("Нет созданных агентов")
    
    st.markdown("---")
    st.markdown("## ➕ СОЗДАТЬ АГЕНТА")
    
    avatars = ["🧠", "🤖", "📊", "⚙️", "📋", "🎯", "💡", "🌟", "🔥", "💎"]
    selected_avatar = st.selectbox("Выберите аватар", avatars, index=0)
    
    new_name = st.text_input("Имя агента", placeholder="Мой Помощник")
    new_role = st.text_input("Роль", placeholder="эксперт по данным")
    new_prompt = st.text_area("Системный промпт", height=100, 
                               placeholder="Ты помощник, который...")
    
    if st.button("✨ Создать агента", use_container_width=True):
        if new_name and new_role and new_prompt:
            agent_manager.add_agent(new_name, new_role, new_prompt, selected_avatar)
            st.success(f"✅ Агент {new_name} создан!")
            st.rerun()
        else:
            st.warning("Заполните все поля")
    
    st.markdown("---")
    st.markdown("## 📤 ЭКСПОРТ/ИМПОРТ")
    
    current_agent = agent_manager.get_current_agent()
    if current_agent:
        export_json = agent_manager.export_agent(current_agent.id)
        if export_json:
            st.download_button(
                label=f"📥 Экспорт {current_agent.name}",
                data=export_json,
                file_name=f"agent_{current_agent.name}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    import_file = st.file_uploader("📂 Импорт агента", type=['json'])
    if import_file:
        content = import_file.read().decode('utf-8')
        if agent_manager.import_agent(content):
            st.success("✅ Агент импортирован!")
            st.rerun()
    
    st.markdown("---")
    st.markdown("## 📊 СТАТИСТИКА")
    st.metric("Всего агентов", len(agent_manager.agents))
    if current_agent:
        st.metric("Обучений", current_agent.stats['total_trainings'])
        st.metric("Диалогов", current_agent.stats['total_conversations'])
    
    st.markdown("---")
    if st.button("🗑️ Очистить workflow", use_container_width=True):
        st.session_state.workflow = []
        st.rerun()

# ============================================================================
# ОСНОВНЫЕ ВКЛАДКИ
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💬 ДИАЛОГ С АГЕНТОМ",
    "📚 ОБУЧЕНИЕ",
    "🧠 ПАМЯТЬ",
    "📊 АНАЛИТИКА",
    "🤖 WORKFLOW",
    "🔀 РУССКИЕ УСЛОВИЯ",
    "📖 ИНСТРУКЦИЯ"
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
                <h2 style="margin: 0;">{current_agent.name}</h2>
                <p style="margin: 0; opacity: 0.8;">{current_agent.role}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # История диалога
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
        
        # Ввод сообщения
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_area("✏️ Ваше сообщение:", height=80, key="agent_input", 
                                      label_visibility="collapsed", placeholder="Напишите сообщение...")
        with col2:
            use_training = st.checkbox("Использовать обучение", value=True)
        
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
                <p style="margin: 0; opacity: 0.8;">Обучите агента правильным ответам на ваши вопросы</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box-premium">
            <h4>🎯 Как обучать агента?</h4>
            <p>Добавляйте примеры правильных ответов. Агент будет учиться на них и давать более точные ответы!</p>
        </div>
        """, unsafe_allow_html=True)
        
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
        
        st.subheader(f"📚 Примеры обучения ({len(current_agent.training_examples)})")
        
        if current_agent.training_examples:
            for i, example in enumerate(reversed(current_agent.training_examples[-10:])):
                st.markdown(f"""
                <div class="training-card-premium">
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

# ============================================================================
# ВКЛАДКА 3: ПАМЯТЬ
# ============================================================================

with tab3:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента в боковой панели")
    else:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">🧠</div>
            <div>
                <h2 style="margin: 0;">Память {current_agent.name}</h2>
                <p style="margin: 0; opacity: 0.8;">Агент запоминает важную информацию</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box-premium">
            <h4>💾 Что такое память агента?</h4>
            <p>Агент запоминает важные факты о вас, ваших предпочтениях и контексте.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("➕ ДОБАВИТЬ В ПАМЯТЬ", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                memory_key = st.text_input("📌 Ключ (что запомнить):", placeholder="любимый_язык")
            with col2:
                memory_value = st.text_input("💾 Значение:", placeholder="Python")
            
            importance = st.selectbox("Важность:", ["low", "normal", "high"])
            
            if st.button("💾 Сохранить в память", type="primary"):
                if memory_key and memory_value:
                    current_agent.add_to_memory(memory_key, memory_value, importance)
                    agent_manager.save_agents()
                    st.success(f"✅ Запомнено: {memory_key} = {memory_value}")
                    st.rerun()
                else:
                    st.warning("Заполните ключ и значение")
        
        st.markdown("---")
        
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
        
        if st.button("🗑️ Очистить всю память", type="secondary"):
            current_agent.memory = []
            agent_manager.save_agents()
            st.success("Память очищена!")
            st.rerun()

# ============================================================================
# ВКЛАДКА 4: АНАЛИТИКА
# ============================================================================

with tab4:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента в боковой панели")
    else:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">📊</div>
            <div>
                <h2 style="margin: 0;">Аналитика {current_agent.name}</h2>
                <p style="margin: 0; opacity: 0.8;">Статистика и метрики производительности</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="stat-card-glass">
                <div class="stat-number">{current_agent.stats['total_trainings']}</div>
                <div>🎓 Обучений</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card-glass">
                <div class="stat-number">{current_agent.stats['total_conversations']}</div>
                <div>💬 Диалогов</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card-glass">
                <div class="stat-number">{current_agent.stats['success_rate']:.0f}%</div>
                <div>✅ Успешность</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            learned_from = len(current_agent.training_examples) + len(current_agent.memory)
            st.markdown(f"""
            <div class="stat-card-glass">
                <div class="stat-number">{learned_from}</div>
                <div>📚 Выучено фактов</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.subheader("💬 Последние диалоги")
        if current_agent.conversation_history:
            for conv in current_agent.conversation_history[-5:]:
                with st.expander(f"Диалог от {conv['timestamp'][:19]}"):
                    st.markdown(f"**👤 Пользователь:** {conv['user'][:200]}...")
                    st.markdown(f"**🤖 Агент:** {conv['agent'][:200]}...")
        else:
            st.info("Пока нет диалогов")
    
    st.markdown("---")
    st.subheader("📈 Общая статистика по всем агентам")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего агентов", len(agent_manager.agents))
    with col2:
        total_trainings = sum(a.stats.get('total_trainings', 0) for a in agent_manager.agents.values())
        st.metric("Всего обучений", total_trainings)
    with col3:
        total_conversations = sum(a.stats.get('total_conversations', 0) for a in agent_manager.agents.values())
        st.metric("Всего диалогов", total_conversations)
    with col4:
        total_memory = sum(len(a.memory) for a in agent_manager.agents.values())
        st.metric("Всего записей памяти", total_memory)

# ============================================================================
# ВКЛАДКА 5: WORKFLOW
# ============================================================================

with tab5:
    st.subheader("🤖 Интеграция ИИ агентов в workflow")
    
    st.markdown("""
    <div class="info-box-premium">
        <h4>🎯 Используйте обученных агентов в автоматизациях!</h4>
        <p>Агенты могут анализировать данные, принимать решения и выполнять действия в ваших workflow.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 Добавить блок в workflow")
        
        block_types = [
            ("📖 Google Таблицы", "google_sheets_read"),
            ("🧠 DeepSeek AI", "deepseek"),
            ("🔀 Условие (русское)", "condition"),
            ("📧 Email", "email"),
            ("📱 Telegram", "telegram"),
            ("🔄 Цикл", "loop"),
            ("📡 HTTP GET", "http_get"),
            ("📤 HTTP POST", "http_post"),
        ]
        
        for name, btype in block_types:
            if st.button(f"{name}", key=f"add_block_{btype}"):
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
            if st.button(f"{agent.avatar_emoji} {agent.name}", key=f"workflow_agent_{agent.id}"):
                st.session_state.workflow.append({
                    "id": len(st.session_state.workflow),
                    "name": f"Агент {agent.name}",
                    "icon": agent.avatar_emoji,
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
                        config['condition'] = st.text_area("Условие", 
                            config.get('condition', 'если цена больше 1000'), 
                            height=80, key=f"cond_{i}")
                    
                    elif block_type == 'ai_agent':
                        agent = agent_manager.agents.get(block.get('agent_id'))
                        if agent:
                            st.info(f"{agent.avatar_emoji} Агент: {agent.name}")
                            config['question'] = st.text_area("Вопрос к агенту:", 
                                config.get('question', 'Проанализируй данные'), 
                                height=80, key=f"q_{i}")
                            config['use_training'] = st.checkbox("Использовать обучение", 
                                config.get('use_training', True), key=f"train_{i}")
                    
                    elif block_type == 'email':
                        config['to'] = st.text_input("Кому", config.get('to', ''), key=f"to_{i}")
                        config['subject'] = st.text_input("Тема", config.get('subject', 'Уведомление'), key=f"subj_{i}")
                        config['body'] = st.text_area("Сообщение", config.get('body', ''), height=80, key=f"body_{i}")
                    
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
                        config['url'] = st.text_input("URL", config.get('url', ''), key=f"url_{i}")
                        config['headers'] = st.text_area("Заголовки (JSON)", 
                            config.get('headers', '{}'), key=f"headers_{i}")
                        if block_type == 'http_post':
                            config['body'] = st.text_area("Тело запроса (JSON)", 
                                config.get('body', '{}'), key=f"body_{i}")
                    
                    block['config'] = config
                
                if st.button(f"🗑️ Удалить блок {i+1}", key=f"del_{i}"):
                    st.session_state.workflow.pop(i)
                    st.rerun()
            
            st.markdown("---")
            
            # Сохранение workflow
            col_save1, col_save2 = st.columns(2)
            with col_save1:
                workflow_name = st.text_input("Название workflow для сохранения:", placeholder="Мой первый workflow")
                if st.button("💾 Сохранить workflow", use_container_width=True):
                    if workflow_name:
                        st.session_state.workflows[workflow_name] = st.session_state.workflow
                        save_workflows_to_file(st.session_state.workflows)
                        st.success(f"✅ Workflow '{workflow_name}' сохранен!")
                    else:
                        st.error("Введите название")
            
            with col_save2:
                if st.button("🗑️ Очистить workflow", use_container_width=True):
                    st.session_state.workflow = []
                    st.rerun()
            
            st.markdown("---")
            
            # Кнопка запуска workflow
            if st.button("🚀 ЗАПУСТИТЬ WORKFLOW", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(idx, node):
                    progress_bar.progress((idx + 1) / len(st.session_state.workflow))
                    status_text.text(f"🔄 Выполняется: {node.get('name', 'Block')}")
                
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
    
    # Загруженные workflows
    if st.session_state.workflows:
        st.markdown("---")
        st.subheader("📚 Сохраненные workflows")
        for name, workflow in st.session_state.workflows.items():
            with st.expander(f"📁 {name}"):
                st.json(workflow)
                col_load1, col_load2 = st.columns(2)
                with col_load1:
                    if st.button(f"📂 Загрузить {name}", key=f"load_{name}"):
                        st.session_state.workflow = workflow
                        st.success(f"Workflow '{name}' загружен!")
                        st.rerun()
                with col_load2:
                    if st.button(f"🗑️ Удалить {name}", key=f"delete_workflow_{name}"):
                        del st.session_state.workflows[name]
                        save_workflows_to_file(st.session_state.workflows)
                        st.rerun()

# ============================================================================
# ВКЛАДКА 6: РУССКИЕ УСЛОВИЯ
# ============================================================================

with tab6:
    st.subheader("🔀 Русские условия для workflow")
    
    st.markdown("""
    <div class="info-box-premium">
        <h4>🎯 Как писать условия на русском?</h4>
        <p>Просто напишите условие так, как вы бы сказали человеку.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Примеры условий")
        examples = [
            "если цена больше 1000 то отправить уведомление",
            "если статус равно успех иначе отправить ошибку",
            "если количество меньше 5 то пополнить склад",
            "если текст содержит срочно то отметить как важное"
        ]
        for ex in examples:
            st.code(f"📌 {ex}")
        
        st.markdown("### 💡 Доступные операторы")
        st.markdown("""
        | Что написать | Как понять |
        |--------------|------------|
        | больше, выше | Больше чем |
        | меньше, ниже | Меньше чем |
        | равно, равняется | Равно |
        | содержит, включает | Содержит подстроку |
        """)
    
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

# ============================================================================
# ВКЛАДКА 7: ИНСТРУКЦИЯ
# ============================================================================

with tab7:
    st.subheader("📖 Полная инструкция для новичков")
    
    st.markdown("""
    ## 🧠 Что такое ИИ агенты с обучением?
    
    **ИИ агенты** - это персонализированные помощники, которые:
    - Учатся на ваших примерах
    - Запоминают важную информацию
    - Адаптируются под ваш стиль
    
    ---
    
    ## 📚 Как обучить агента?
    
    ### 1. Добавление примеров
    Перейдите на вкладку **ОБУЧЕНИЕ** и добавьте примеры правильных ответов.
    
    ### 2. Память агента
    Добавляйте факты, которые агент должен запомнить.
    
    ---
    
    ## 🤖 Как использовать workflow?
    
    ### Создание автоматизации
    1. Перейдите на вкладку **WORKFLOW**
    2. Добавляйте блоки из левой колонки
    3. Настраивайте каждый блок
    4. Нажмите **ЗАПУСТИТЬ WORKFLOW**
    
    ---
    
    ## 🔀 Русские условия
    
    Условия пишутся естественным языком.
    
    ---
    
    ## 💾 Сохранение данных
    
    Все данные автоматически сохраняются в файлы JSON.
    
    ---
    
    ## 🚀 Быстрый старт
    
    1. Получите API ключ на platform.deepseek.com
    2. Вставьте ключ в боковую панель
    3. Создайте агента
    4. Начните диалог!
    
    ---
    
    ## ❓ Частые вопросы
    
    **Q: Нужно ли платить за DeepSeek API?**  
    A: Нет, DeepSeek предоставляет бесплатный API.
    
    **Q: Сохранятся ли мои агенты после закрытия?**  
    A: Да! Все данные автоматически сохраняются.
    
    **Q: Можно ли поделиться агентом?**  
    A: Да! Используйте кнопку "Экспорт" в боковой панели.
    """)

# ============================================================================
# ИНДИКАТОР АВТОСОХРАНЕНИЯ
# ============================================================================

st.markdown("""
<div class="save-indicator-premium">
    💾 Автосохранение активно
</div>
""", unsafe_allow_html=True)

# ============================================================================
# ПОДВАЛ
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #888">
    <div style="font-size: 1rem;">🧠 Workflow Builder PRO v7.0</div>
    <div style="font-size: 0.7rem;">Обучаемые ИИ агенты | Автосохранение | Премиум дизайн | Русские условия</div>
    <div style="font-size: 0.6rem; margin-top: 0.3rem;">
        📁 Файлы: agents.json | workflows.json | settings.json
    </div>
</div>
""", unsafe_allow_html=True)
