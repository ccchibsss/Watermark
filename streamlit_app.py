"""
================================================================================
КОНСТРУКТОР WORKFLOW PRO v7.0 - ПОЛНАЯ ВЕРСИЯ
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
from openai import OpenAI
from pathlib import Path

# ============================================================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================================

st.set_page_config(
    page_title="Workflow Builder Pro - Обучаемые ИИ Агенты",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        animation: fadeIn 1s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4ECDC4;
        transition: all 0.3s;
        cursor: pointer;
    }
    .agent-card:hover {
        transform: translateX(5px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
    }
    .agent-card-selected {
        border-left-color: #00ff88;
        background: linear-gradient(135deg, #0a2e1f 0%, #0a1a10 100%);
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        transition: transform 0.3s;
    }
    .stat-card:hover {
        transform: translateY(-5px);
    }
    .memory-box {
        background: #1e1e2e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffa500;
        margin: 0.5rem 0;
    }
    .training-example {
        background: #2a2a3e;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
    .workflow-node {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: white;
        border-left: 4px solid #4ECDC4;
        transition: all 0.3s;
    }
    .workflow-node:hover {
        transform: translateX(5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .workflow-node-success {
        border-left-color: #00ff88;
        background: linear-gradient(135deg, #0a2e1f 0%, #0a1a10 100%);
    }
    .workflow-node-error {
        border-left-color: #ff4444;
        background: linear-gradient(135deg, #3e1a1a 0%, #2a0f0f 100%);
    }
    .info-box {
        background: #1e1e2e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 1rem 0;
    }
    .condition-box {
        background: #1e1e2e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffa500;
        margin: 0.5rem 0;
        font-family: monospace;
    }
    .stButton button {
        border-radius: 10px !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .stTextArea textarea {
        border-radius: 10px;
    }
    .stTextInput input {
        border-radius: 10px;
    }
    div[data-testid="stExpander"] details {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        border: none;
    }
    div[data-testid="stExpander"] summary {
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🧠 WORKFLOW BUILDER PRO v7.0</h1>
    <p>Обучаемые ИИ агенты | Сохранение контекста | Персональные помощники | Русские условия</p>
    <p style="font-size: 0.9rem;">⭐ Создавайте и обучайте своих ИИ агентов | 💾 Сохраняйте навсегда | 🔄 Обменивайтесь агентами</p>
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
        
        # Шаблоны для распознавания
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
        
        # Проверка на "если ... то ..."
        if 'если' in condition_text and 'то' in condition_text:
            match = re.search(r'если\s+(.+?)\s+то', condition_text)
            if match:
                condition_part = match.group(1)
                result['type'] = 'if_then'
                result['condition'] = condition_part
                result['code'] = f"if {RussianConditionParser._to_code(condition_part)}:"
        
        # Проверка на "иначе"
        elif 'иначе' in condition_text:
            parts = condition_text.split('иначе')
            if len(parts) == 2:
                result['type'] = 'if_else'
                result['true_branch'] = parts[0].replace('если', '').strip()
                result['false_branch'] = parts[1].strip()
                result['code'] = f"if {RussianConditionParser._to_code(result['true_branch'])}:\n    # действие\nelse:\n    # другое действие"
        
        # Простые сравнения
        else:
            for pattern_type, pattern in patterns.items():
                match = re.search(pattern, condition_text)
                if match:
                    result['type'] = pattern_type
                    result['matches'] = match.groups()
                    result['code'] = RussianConditionParser._generate_code(pattern_type, match.groups())
                    break
        
        # Примеры для обучения
        result['examples'] = RussianConditionParser._get_examples()
        
        return result
    
    @staticmethod
    def _to_code(condition: str) -> str:
        """Преобразует часть условия в Python код"""
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
        """Генерирует Python код из распознанного шаблона"""
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
        # Обновляем или добавляем
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
        
        # Обновляем успешность на основе фидбека
        if feedback == 'positive':
            self.stats['success_rate'] = (self.stats['success_rate'] * (self.stats['total_conversations'] - 1) + 100) / self.stats['total_conversations']
        elif feedback == 'negative':
            self.stats['success_rate'] = (self.stats['success_rate'] * (self.stats['total_conversations'] - 1) + 0) / self.stats['total_conversations']
    
    def get_context_summary(self) -> str:
        """Возвращает краткую сводку контекста агента"""
        summary = f"Роль: {self.role}\n"
        summary += f"Память: {len(self.memory)} фактов\n"
        summary += f"Обучен на: {len(self.training_examples)} примерах\n"
        return summary
    
    def generate_response(self, user_input: str, api_key: str, use_training: bool = True) -> str:
        """Генерирует ответ с учётом обучения и памяти"""
        if not api_key:
            return "❌ API ключ не указан. Получите бесплатно на platform.deepseek.com"
        
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            
            # Собираем контекст из памяти
            memory_context = ""
            if self.memory:
                memory_context = "\n\nЗНАНИЯ АГЕНТА (из памяти):\n"
                for mem in self.memory[-5:]:
                    memory_context += f"- {mem['key']}: {mem['value']}\n"
            
            # Собираем примеры обучения
            training_context = ""
            if use_training and self.training_examples:
                training_context = "\n\nПРИМЕРЫ ОБУЧЕНИЯ:\n"
                for ex in self.training_examples[-3:]:
                    training_context += f"Пользователь: {ex['user_input']}\n"
                    training_context += f"Правильный ответ: {ex['expected_output']}\n\n"
            
            # Собираем историю диалогов
            history_context = ""
            if self.conversation_history:
                history_context = "\n\nИСТОРИЯ ДИАЛОГОВ:\n"
                for conv in self.conversation_history[-3:]:
                    history_context += f"Пользователь: {conv['user']}\n"
                    history_context += f"Агент: {conv['agent']}\n\n"
            
            full_prompt = f"""
Ты - ИИ агент с именем "{self.name}" и ролью "{self.role}".

{self.system_prompt}

{memory_context}

{training_context}

{history_context}

Текущий запрос пользователя: "{user_input}"

Ответь, используя полученные знания, примеры обучения и память.
Будь полезным, точным и дружелюбным.
"""
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def to_dict(self) -> Dict:
        """Экспортирует агента в словарь для сохранения"""
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
        """Создаёт агента из словаря"""
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
        """Генерирует workflow из описания"""
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
   - deepseek: AI анализ (config: system_prompt, user_prompt)
   - http_get: GET запрос к API (config: url)
   - http_post: POST запрос (config: url, body)
   - condition: условие (config: condition на русском)
   - loop: цикл (config: items)
   - email: отправка email (config: to, subject, body)
   - telegram: отправка в Telegram (config: chat_id, message)

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
            # Извлекаем JSON из ответа
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
        """Загружает агентов из хранилища"""
        if 'agents' not in st.session_state:
            default_agents = self._create_default_agents()
            st.session_state.agents = {agent.id: agent.to_dict() for agent in default_agents}
            st.session_state.current_agent_id = default_agents[0].id if default_agents else None
        
        # Восстанавливаем агентов из словарей
        for agent_id, agent_dict in st.session_state.agents.items():
            if agent_id not in self.agents:
                self.agents[agent_id] = AIAgent.from_dict(agent_dict)
        
        self.current_agent_id = st.session_state.get('current_agent_id')
    
    def _create_default_agents(self) -> List[AIAgent]:
        """Создаёт агентов по умолчанию"""
        agents = []
        
        # Агент аналитик данных
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
        
        # Агент помощник по автоматизации
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
        
        # Агент менеджер задач
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
        """Сохраняет агентов в сессию"""
        st.session_state.agents = {agent_id: agent.to_dict() for agent_id, agent in self.agents.items()}
        st.session_state.current_agent_id = self.current_agent_id
    
    def add_agent(self, name: str, role: str, system_prompt: str) -> AIAgent:
        """Добавляет нового агента"""
        agent = AIAgent(name, role, system_prompt)
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
            st.session_state.current_agent_id = agent_id
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

# ============================================================================
# КЛАСС ДЛЯ ВЫПОЛНЕНИЯ WORKFLOW (КАК В n8n)
# ============================================================================

class WorkflowExecutor:
    """Выполняет workflow с поддержкой условий на русском"""
    
    def __init__(self, workflow: List[Dict], api_key: str = None, agent_manager: AgentManager = None):
        self.workflow = workflow
        self.api_key = api_key
        self.agent_manager = agent_manager
        self.context = {}
        self.results = []
        self.current_node_index = 0
        self.branch_stack = []
    
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
                
                # Обновляем контекст
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
        """Выполняет чтение из Google Sheets"""
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
        """Выполняет запрос к DeepSeek AI"""
        if not self.api_key:
            return {'error': 'API ключ не указан'}
        
        try:
            client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
            
            # Подставляем переменные из контекста
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
        """Выполняет условие на русском языке"""
        condition_text = config.get('condition', '')
        
        # Парсим русское условие
        parsed = RussianConditionParser.parse(condition_text)
        
        # Вычисляем условие
        result = self._evaluate_condition(condition_text)
        
        return {
            'condition': condition_text,
            'result': result,
            'parsed': parsed,
            'code': parsed.get('code')
        }
    
    def _evaluate_condition(self, condition_text: str) -> bool:
        """Вычисляет значение условия"""
        condition_text = condition_text.lower()
        
        # Простые проверки
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
        
        return True  # По умолчанию условие истинно
    
    def _execute_loop(self, config: Dict) -> Dict:
        """Выполняет цикл по элементам"""
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
        """Выполняет HTTP GET запрос"""
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
        """Выполняет HTTP POST запрос"""
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
        """Подготавливает email (демо)"""
        return {
            'to': config.get('to', ''),
            'subject': config.get('subject', ''),
            'body': config.get('body', ''),
            'status': 'ready'
        }
    
    def _execute_telegram(self, config: Dict) -> Dict:
        """Подготавливает Telegram (демо)"""
        return {
            'chat_id': config.get('chat_id', ''),
            'message': config.get('message', ''),
            'status': 'ready'
        }
    
    def _execute_ai_agent(self, config: Dict) -> Dict:
        """Выполняет запрос к ИИ агенту"""
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
# БОКОВАЯ ПАНЕЛЬ - АГЕНТЫ
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
    
    st.markdown("---")
    
    # Управление workflow
    st.markdown("## 🛠️ УПРАВЛЕНИЕ")
    if st.button("🗑️ Очистить workflow", use_container_width=True):
        st.session_state.workflow = []
        st.rerun()

# ============================================================================
# ОСНОВНЫЕ ВКЛАДКИ
# ============================================================================

tabs = st.tabs(["💬 ДИАЛОГ С АГЕНТОМ", "📚 ОБУЧЕНИЕ", "🧠 ПАМЯТЬ", "📊 АНАЛИТИКА", "🤖 WORKFLOW", "🔀 РУССКИЕ УСЛОВИЯ", "📖 ИНСТРУКЦИЯ"])

# ============================================================================
# ВКЛАДКА 1: ДИАЛОГ С АГЕНТОМ
# ============================================================================

with tabs[0]:
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Нет выбранного агента. Создайте или выберите агента в боковой панели")
    else:
        st.subheader(f"💬 Диалог с агентом: {current_agent.name}")
        st.markdown(f"*Роль: {current_agent.role}*")
        
        # История диалога
        for idx, msg in enumerate(st.session_state.agent_messages):
            if msg['role'] == 'user':
                st.markdown(f"**👤 Вы:** {msg['content']}")
            else:
                st.markdown(f"**🤖 {current_agent.name}:** {msg['content']}")
            st.markdown("---")
        
        # Ввод сообщения
        user_input = st.text_area("✏️ Ваше сообщение:", height=100, key="agent_input")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            use_training = st.checkbox("Использовать обучение", value=True)
        with col2:
            if st.button("🚀 Отправить", type="primary", use_container_width=True):
                if user_input:
                    # Добавляем сообщение пользователя
                    st.session_state.agent_messages.append({
                        'role': 'user',
                        'content': user_input,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    with st.spinner(f"{current_agent.name} думает..."):
                        response = current_agent.generate_response(user_input, api_key, use_training)
                    
                    # Добавляем ответ агента
                    st.session_state.agent_messages.append({
                        'role': 'agent',
                        'content': response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Сохраняем диалог
                    current_agent.add_conversation(user_input, response)
                    agent_manager.save_agents()
                    
                    st.rerun()
        
        # Кнопка очистки истории
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
# ВКЛАДКА 5: WORKFLOW
# ============================================================================

with tabs[4]:
    st.subheader("🤖 Интеграция ИИ агентов в workflow")
    
    st.markdown("""
    <div class="info-box">
    <h4>🎯 Используйте обученных агентов в автоматизациях!</h4>
    <p>Агенты могут анализировать данные, принимать решения и выполнять действия в ваших workflow.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 Добавить блок в workflow")
        
        # Блоки для workflow
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
                        st.caption("💡 Пример: https://docs.google.com/spreadsheets/d/ВАШ_ID_ТАБЛИЦЫ/edit")
                    
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
                        
                        # Показываем преобразование
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
                    
                    # Обновляем аналитику
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
# ВКЛАДКА 7: ИНСТРУКЦИЯ
# ============================================================================

with tabs[6]:
    st.subheader("📖 Полная инструкция для новичков")
    
    st.markdown("""
    ## 🧠 Что такое ИИ агенты с обучением?
    
    #ИИ агенты# - это персонализированные помощники, которые:
    - ✅ **Учатся на ваших примерах**
    - ✅ **Запоминают важную информацию**
    - ✅ **Адаптируются под ваш стиль**
    - ✅ **Совершенствуются с каждым диалогом**
    
    ---
    
    ## 📚 Как обучить агента?
    
    ### 1. Добавление примеров
    Перейдите на вкладку **"ОБУЧЕНИЕ"** и добавьте примеры правильных ответов:
    
