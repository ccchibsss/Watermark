"""
================================================================================
КОНСТРУКТОР WORKFLOW PRO v7.0 - ПОЛНЫЙ КОД
Обучаемые ИИ агенты | Сохранение | Русские условия
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
        return codes.get(pattern_type, f"if {pattern_type}:")
    
    @staticmethod
    def _get_examples() -> List[str]:
        return [
            "если цена больше 1000 то отправить уведомление",
            "если статус равно 'успех' иначе отправить ошибку",
            "если количество меньше 5 то пополнить склад",
            "если текст содержит 'срочно' то отметить как важное"
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
        if feedback == 'positive':
            prev = self.stats['success_rate'] * (self.stats['total_conversations'] - 1)
            self.stats['success_rate'] = (prev + 100) / self.stats['total_conversations']
        elif feedback == 'negative':
            prev = self.stats['success_rate'] * (self.stats['total_conversations'] - 1)
            self.stats['success_rate'] = (prev + 0) / self.stats['total_conversations']
    
    def get_context_summary(self) -> str:
        """Возвращает краткую сводку контекста агента"""
        return f"Роль: {self.role}\nПамять: {len(self.memory)} фактов\nОбучен на: {len(self.training_examples)} примерах"
    
    def generate_response(self, user_input: str, api_key: str, use_training: bool = True) -> str:
        """Генерирует ответ с учётом обучения и памяти"""
        if not api_key:
            return "❌ API ключ не указан"
        
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
                    training_context += f"Пользователь: {ex['user_input']}\nПравильный ответ: {ex['expected_output']}\n\n"
            
            history_context = ""
            if self.conversation_history:
                history_context = "\n\nИСТОРИЯ ДИАЛОГОВ:\n"
                for conv in self.conversation_history[-3:]:
                    history_context += f"Пользователь: {conv['user']}\nАгент: {conv['agent']}\n\n"
            
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
        
        for agent_id, agent_dict in st.session_state.agents.items():
            if agent_id not in self.agents:
                self.agents[agent_id] = AIAgent.from_dict(agent_dict)
        self.current_agent_id = st.session_state.get('current_agent_id')
    
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
# КЛАСС ДЛЯ WORKFLOW
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
    
    def execute(self, progress_callback=None) -> Dict:
        """Запускает выполнение workflow"""
        start_time = time.time()
        
        while self.current_node_index < len(self.workflow):
            node = self.workflow[self.current_node_index]
            if progress_callback:
                progress_callback(self.current_node_index, node)
            
            try:
                result = self._execute_node(node)
                self.results.append({'node': node.get('name'), 'result': result, 'timestamp': datetime.now().isoformat()})
                if isinstance(result, dict):
                    self.context.update(result)
                node['status'] = 'success'
                self.current_node_index += 1
            except Exception as e:
                node['status'] = 'error'
                node['error'] = str(e)
                return {'success': False, 'error': str(e), 'results': self.results, 'execution_time': time.time() - start_time}
        
        return {'success': True, 'results': self.results, 'context': self.context, 'execution_time': time.time() - start_time}
    
    def _execute_node(self, node: Dict) -> Any:
        """Выполняет отдельный узел"""
        node_type = node.get('type')
        config = node.get('config', {})
        
        if node_type == 'google_sheets_read':
            return self._execute_google_sheets(config)
        elif node_type == 'deepseek':
            return self._execute_deepseek(config)
        elif node_type == 'condition':
            return self._execute_condition(config)
        elif node_type == 'ai_agent':
            return self._execute_ai_agent(config)
        elif node_type == 'email':
            return {'status': 'ready', 'to': config.get('to', ''), 'subject': config.get('subject', '')}
        elif node_type == 'telegram':
            return {'status': 'ready', 'chat_id': config.get('chat_id', ''), 'message': config.get('message', '')}
        elif node_type in ['http_get', 'http_post']:
            return self._execute_http(config, node_type)
        else:
            return {'status': 'executed'}
    
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
            return {'data': df.to_dict('records'), 'rows': len(df), 'columns': list(df.columns)}
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
            return {'response': response.choices[0].message.content}
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_condition(self, config: Dict) -> Dict:
        condition_text = config.get('condition', '')
        parsed = RussianConditionParser.parse(condition_text)
        result = self._evaluate_condition(condition_text)
        return {'condition': condition_text, 'result': result, 'parsed': parsed, 'code': parsed.get('code')}
    
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
        elif 'равно' in condition_text:
            match = re.search(r'(\w+)\s+равно\s+(.+)', condition_text)
            if match:
                var_name = match.group(1)
                value = match.group(2).strip().strip("'\"")
                context_value = self.context.get(var_name, '')
                return str(context_value) == value
        return True
    
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
        return {'agent': agent.name, 'response': response}
    
    def _execute_http(self, config: Dict, method: str) -> Dict:
        url = config.get('url', '')
        if not url:
            return {'error': 'URL не указан'}
        try:
            if method == 'http_get':
                response = requests.get(url, timeout=30)
            else:
                body = config.get('body', '{}')
                if isinstance(body, str):
                    body = json.loads(body)
                response = requests.post(url, json=body, timeout=30)
            return {'status': response.status_code, 'data': response.json() if response.status_code == 200 else None}
        except Exception as e:
            return {'error': str(e)}

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================================

if 'agent_manager' not in st.session_state:
    st.session_state.agent_manager = AgentManager()
if 'workflow' not in st.session_state:
    st.session_state.workflow = []
if 'agent_messages' not in st.session_state:
    st.session_state.agent_messages = []

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
    
    for agent in agent_manager.agents.values():
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
    
    with st.expander("➕ СОЗДАТЬ НОВОГО АГЕНТА", expanded=False):
        new_name = st.text_input("Имя агента", placeholder="Мой Помощник")
        new_role = st.text_input("Роль", placeholder="эксперт по маркетингу")
        new_prompt = st.text_area("Системный промпт", height=100, placeholder="Ты помощник, который...")
        if st.button("✨ Создать агента", use_container_width=True):
            if new_name and new_role and new_prompt:
                agent_manager.add_agent(new_name, new_role, new_prompt)
                st.success(f"✅ Агент {new_name} создан!")
                st.rerun()
    
    st.markdown("---")
    
    with st.expander("🔄 ЭКСПОРТ/ИМПОРТ", expanded=False):
        current = agent_manager.get_current_agent()
        if current:
            export_json = agent_manager.export_agent(current.id)
            st.download_button(label=f"📤 Экспорт {current.name}", data=export_json,
                              file_name=f"agent_{current.name}_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json")
        import_file = st.file_uploader("Импорт агента", type=['json'])
        if import_file:
            if agent_manager.import_agent(import_file.read().decode('utf-8')):
                st.success("✅ Агент импортирован!")
                st.rerun()
    
    st.markdown("---")
    st.metric("Всего агентов", len(agent_manager.agents))
    current_agent = agent_manager.get_current_agent()
    if current_agent:
        st.metric("Обучений", current_agent.stats['total_trainings'])
        st.metric("Диалогов", current_agent.stats['total_conversations'])

# ============================================================================
# ОСНОВНЫЕ ВКЛАДКИ
# ============================================================================

tabs = st.tabs(["💬 ДИАЛОГ С АГЕНТОМ", "📚 ОБУЧЕНИЕ", "🧠 ПАМЯТЬ", "📊 АНАЛИТИКА", "🤖 WORKFLOW", "🔀 УСЛОВИЯ", "📖 ИНСТРУКЦИЯ"])

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
        
        for msg in st.session_state.agent_messages:
            if msg['role'] == 'user':
                st.markdown(f"**👤 Вы:** {msg['content']}")
            else:
                st.markdown(f"**🤖 {current_agent.name}:** {msg['content']}")
                if msg.get('feedback_shown'):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"👍 Полезно", key=f"good_{msg.get('id', '')}"):
                            current_agent.add_conversation(
                                st.session_state.agent_messages[msg.get('idx', 0)-1]['content'] if msg.get('idx', 0) > 0 else "",
                                msg['content'], 'positive')
                            agent_manager.save_agents()
                            st.success("Спасибо за отзыв!")
                    with col2:
                        if st.button(f"👎 Не полезно", key=f"bad_{msg.get('id', '')}"):
                            current_agent.add_conversation(
                                st.session_state.agent_messages[msg.get('idx', 0)-1]['content'] if msg.get('idx', 0) > 0 else "",
                                msg['content'], 'negative')
                            agent_manager.save_agents()
                            st.success("Спасибо, учтём!")
            st.markdown("---")
        
        user_input = st.text_area("✏️ Ваше сообщение:", height=100, key="agent_input")
        col1, col2 = st.columns([1, 4])
        with col1:
            use_training = st.checkbox("Использовать обучение", value=True)
        with col2:
            if st.button("🚀 Отправить", type="primary", use_container_width=True):
                if user_input:
                    st.session_state.agent_messages.append({'role': 'user', 'content': user_input, 'timestamp': datetime.now().isoformat()})
                    with st.spinner(f"{current_agent.name} думает..."):
                        response = current_agent.generate_response(user_input, api_key, use_training)
                    msg_id = len(st.session_state.agent_messages)
                    st.session_state.agent_messages.append({'role': 'agent', 'content': response, 'id': msg_id, 'idx': msg_id, 'feedback_shown': True})
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
        
        st.subheader(f"📚 Примеры обучения ({len(current_agent.training_examples)})")
        if current_agent.training_examples:
            for i, example in enumerate(reversed(current_agent.training_examples[-10:])):
                st.markdown(f"""
                <div class="training-example">
                    <strong>📝 Пример {i+1}:</strong><br>
                    <strong>Вопрос:</strong> {example['user_input']}<br>
                    <strong>Ответ:</strong> {example['expected_output']}<br>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🗑️ Удалить", key=f"del_example_{i}"):
                    current_agent.training_examples.remove(example)
                    agent_manager.save_agents()
                    st.rerun()
        else:
            st.info("Пока нет примеров обучения.")

# ============================================================================
# ВКЛАДКА 3: ПАМЯТЬ
# ============================================================================

with tabs[2]:
    current_agent = agent_manager.get_current_agent()
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента в боковой панели")
    else:
        st.subheader(f"🧠 Память агента: {current_agent.name}")
        
        with st.expander("➕ ДОБАВИТЬ В ПАМЯТЬ", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                memory_key = st.text_input("📌 Ключ:", placeholder="любимый_язык")
            with col2:
                memory_value = st.text_input("💾 Значение:", placeholder="Python")
            if st.button("💾 Сохранить в память"):
                if memory_key and memory_value:
                    current_agent.add_to_memory(memory_key, memory_value)
                    agent_manager.save_agents()
                    st.success(f"✅ Запомнено!")
                    st.rerun()
        
        if current_agent.memory:
            for mem in current_agent.memory:
                st.markdown(f"""
                <div class="memory-box">
                    <strong>{mem['key']}</strong> = {mem['value']}<br>
                    <small>📅 {mem['timestamp'][:10]} | Просмотров: {mem['access_count']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Память пуста.")

# ============================================================================
# ВКЛАДКА 4: АНАЛИТИКА
# ============================================================================

with tabs[3]:
    current_agent = agent_manager.get_current_agent()
    if not current_agent:
        st.warning("⚠️ Сначала выберите агента в боковой панели")
    else:
        st.subheader(f"📊 Аналитика агента: {current_agent.name}")
        
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

# ============================================================================
# ВКЛАДКА 5: WORKFLOW
# ============================================================================

with tabs[4]:
    st.subheader("🤖 Интеграция ИИ агентов в workflow")
    
    col1, col2 = st.columns(2)
    with col1:
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
        if st.session_state.workflow:
            for i, block in enumerate(st.session_state.workflow):
                st.markdown(f"{i+1}. {block.get('icon', '•')} {block.get('name', 'Block')}")
                with st.expander(f"Настроить {block.get('name', 'Block')}"):
                    if block.get('type') == 'ai_agent':
                        agent = agent_manager.agents.get(block.get('agent_id'))
                        if agent:
                            st.info(f"Агент: {agent.name}")
                            block['config']['question'] = st.text_area("Вопрос:", block['config'].get('question', ''))
                            block['config']['use_training'] = st.checkbox("Использовать обучение", block['config'].get('use_training', True))
            if st.button("🗑️ Очистить workflow"):
                st.session_state.workflow = []
                st.rerun()
        
        if st.button("🚀 ЗАПУСТИТЬ WORKFLOW", type="primary"):
            executor = WorkflowExecutor(st.session_state.workflow, api_key, agent_manager)
            result = executor.execute()
            if result['success']:
                st.success(f"✅ Workflow выполнен за {result['execution_time']:.1f}с")
                for res in result['results']:
                    st.json(res)
            else:
                st.error(f"❌ Ошибка: {result['error']}")

# ============================================================================
# ВКЛАДКА 6: УСЛОВИЯ
# ============================================================================

with tabs[5]:
    st.subheader("🔀 Условия на русском языке")
    
    st.markdown("""
    <div class="info-box">
    <h4>🎯 Как это работает?</h4>
    <p>Просто напишите условие так, как вы бы сказали человеку. ИИ сам преобразует его в код!</p>
    </div>
    """, unsafe_allow_html=True)
    
    test_condition = st.text_area("Напишите ваше условие:", placeholder="например: если цена больше 1000 то отправить уведомление")
    if test_condition:
        parsed = RussianConditionParser.parse(test_condition)
        st.markdown(f"""
        <div class="condition-box">
        <strong>🔍 Результат анализа:</strong><br>
        Тип: {parsed.get('type')}<br>
        Сгенерированный код: <code>{parsed.get('code')}</code>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# ВКЛАДКА 7: ИНСТРУКЦИЯ
# ============================================================================

with tabs[6]:
    st.subheader("📖 Полная инструкция")
    
    st.markdown("""
    ## 🧠 Что такое ИИ агенты с обучением?
    
    **ИИ агенты** - это персонализированные помощники, которые:
    - ✅ **Учатся на ваших примерах**
    - ✅ **Запоминают важную информацию**
    - ✅ **Адаптируются под ваш стиль**
    
    ## 📚 Как обучить агента?
    
    1. **Добавление примеров** - покажите агенту правильные ответы
    2. **Заполнение памяти** - добавьте факты, которые агент должен запомнить
    3. **Оценка ответов** - ставьте лайки/дизлайки
    
    ## 🔀 Русские условия
    
    Просто пишите:
    - `если цена больше 1000 то отправить уведомление`
    - `если статус равно 'успех' иначе ошибка`
    
    ## 🚀 Запуск
    
    ```bash
    pip install streamlit openai pandas openpyxl requests plotly
    streamlit run app.py
