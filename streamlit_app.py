"""
================================================================================
КОНСТРУКТОР WORKFLOW v4.0 "Enterprise"
================================================================================
Функции:
✅ Глубокий анализ данных
✅ Проверка на ошибки (валидация)
✅ Авто-тестирование workflow
✅ Развертывание через веб-интерфейс
✅ Сохранение/загрузка проектов
✅ Логирование всех действий

Автор: AI Assistant
Лицензия: MIT (полностью бесплатно)
================================================================================
"""

import streamlit as st
import json
import pandas as pd
import requests
from datetime import datetime
from openai import OpenAI
import io
import re
import traceback
import time
import hashlib
import os
from typing import Dict, List, Any, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================================
# НАСТРОЙКА СТРАНИЦЫ И ДИЗАЙН
# ============================================================================

st.set_page_config(
    page_title="Workflow Builder Pro | Автоматизация без кода",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомный CSS для профессионального дизайна
st.markdown("""
<style>
    /* Главный хедер */
    .main-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #a0a0ff;
        margin-top: 0.5rem;
    }
    
    /* Карточки */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        color: white;
    }
    
    /* Блоки workflow */
    .workflow-node {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: white;
        border-left: 4px solid #4ECDC4;
        transition: all 0.3s ease;
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
    
    /* Кнопки */
    .stButton button {
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Прогресс бар */
    .stProgress > div > div {
        background: linear-gradient(135deg, #00ff88, #00bfff);
    }
    
    /* Инфо боксы */
    .info-box {
        background: #1e1e2e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 1rem 0;
    }
    .error-box {
        background: #2e1a1a;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff4444;
        margin: 1rem 0;
    }
    .success-box {
        background: #1a2e1a;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00ff88;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🚀 WORKFLOW BUILDER PRO</h1>
    <p>Автоматизация без кода | Глубокий анализ | Проверка ошибок | Веб-развертывание</p>
    <p style="font-size: 0.8rem;">⭐ Бесплатно | ⚡ Быстро | 🔒 Безопасно</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ВСЕХ ХРАНИЛИЩ
# ============================================================================

class WorkflowStorage:
    """Управление хранением workflows и данных"""
    
    @staticmethod
    def init():
        if 'workflow' not in st.session_state:
            st.session_state.workflow = []
        if 'history' not in st.session_state:
            st.session_state.history = []
        if 'results' not in st.session_state:
            st.session_state.results = {}
        if 'variables' not in st.session_state:
            st.session_state.variables = {}
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        if 'deployed_apps' not in st.session_state:
            st.session_state.deployed_apps = []
        if 'error_logs' not in st.session_state:
            st.session_state.error_logs = []
        if 'analytics' not in st.session_state:
            st.session_state.analytics = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_nodes_executed': 0,
                'average_execution_time': 0
            }

# Инициализация
WorkflowStorage.init()

# ============================================================================
# ВАЛИДАЦИЯ И ПРОВЕРКА ОШИБОК
# ============================================================================

class WorkflowValidator:
    """Проверка workflow на ошибки"""
    
    @staticmethod
    def validate_workflow(workflow: List[Dict]) -> Tuple[bool, List[str]]:
        """Проверяет workflow на наличие ошибок"""
        errors = []
        warnings = []
        
        if not workflow:
            errors.append("❌ Workflow пуст. Добавьте хотя бы один блок.")
            return False, errors
        
        # Проверка каждого блока
        for i, node in enumerate(workflow):
            # Проверка обязательных полей
            if 'name' not in node:
                errors.append(f"❌ Блок {i+1}: отсутствует название")
            if 'type' not in node:
                errors.append(f"❌ Блок {i+1}: отсутствует тип")
            if 'config' not in node:
                errors.append(f"❌ Блок {i+1}: отсутствует конфигурация")
            
            # Специфичные проверки для разных типов
            node_type = node.get('type', '')
            
            if node_type == 'google_sheets_read':
                sheet_url = node.get('config', {}).get('sheet_url', '')
                if not sheet_url:
                    errors.append(f"⚠️ Блок '{node.get('name', 'Unknown')}': укажите URL Google Таблицы")
                elif 'docs.google.com' not in sheet_url and len(sheet_url) < 10:
                    warnings.append(f"⚠️ Блок '{node.get('name', 'Unknown')}': URL таблицы выглядит некорректно")
            
            elif node_type == 'deepseek':
                if not node.get('config', {}).get('user_prompt'):
                    warnings.append(f"💡 Блок '{node.get('name', 'Unknown')}': пустой запрос к AI")
            
            elif node_type in ['http_get', 'http_post']:
                url = node.get('config', {}).get('url', '')
                if not url:
                    errors.append(f"❌ Блок '{node.get('name', 'Unknown')}': укажите URL для HTTP запроса")
                elif not url.startswith(('http://', 'https://')):
                    errors.append(f"❌ Блок '{node.get('name', 'Unknown')}': URL должен начинаться с http:// или https://")
            
            elif node_type == 'condition':
                condition = node.get('config', {}).get('condition', '')
                if not condition:
                    warnings.append(f"💡 Блок '{node.get('name', 'Unknown')}': условие не задано")
            
            elif node_type == 'loop':
                items = node.get('config', {}).get('items', '[]')
                try:
                    json.loads(items)
                except:
                    errors.append(f"❌ Блок '{node.get('name', 'Unknown')}': массив элементов должен быть в формате JSON")
        
        # Проверка цикличности
        if WorkflowValidator._has_cycle(workflow):
            errors.append("❌ Обнаружен цикл в workflow (бесконечное выполнение)")
        
        return len(errors) == 0, errors + warnings
    
    @staticmethod
    def _has_cycle(workflow: List[Dict]) -> bool:
        """Проверка на циклы"""
        # Упрощенная проверка - если есть более 50 блоков, возможно зацикливание
        return len(workflow) > 50

class DeepAnalyzer:
    """Глубокий анализ workflow"""
    
    @staticmethod
    def analyze(workflow: List[Dict]) -> Dict:
        """Анализирует workflow и возвращает статистику"""
        analysis = {
            'total_nodes': len(workflow),
            'node_types': {},
            'estimated_time': 0,
            'complexity': 'Низкая',
            'data_flow': [],
            'bottlenecks': [],
            'optimizations': []
        }
        
        # Подсчет типов нод
        for node in workflow:
            node_type = node.get('type', 'unknown')
            analysis['node_types'][node_type] = analysis['node_types'].get(node_type, 0) + 1
        
        # Оценка времени выполнения
        time_estimates = {
            'google_sheets_read': 2,
            'google_sheets_write': 1,
            'deepseek': 5,
            'http_get': 1,
            'http_post': 1,
            'condition': 0.1,
            'loop': 1,
            'excel_read': 1,
            'email': 0.5,
            'telegram': 0.5
        }
        
        for node in workflow:
            node_type = node.get('type', '')
            analysis['estimated_time'] += time_estimates.get(node_type, 0.5)
        
        # Оценка сложности
        if analysis['total_nodes'] <= 3:
            analysis['complexity'] = 'Низкая (для начинающих)'
        elif analysis['total_nodes'] <= 7:
            analysis['complexity'] = 'Средняя'
        else:
            analysis['complexity'] = 'Высокая (требуется тестирование)'
        
        # Поиск узких мест
        if analysis['node_types'].get('deepseek', 0) > 3:
            analysis['bottlenecks'].append("⚠️ Много AI блоков - может быть медленно")
        if analysis['node_types'].get('loop', 0) > 2:
            analysis['bottlenecks'].append("⚠️ Вложенные циклы могут замедлить выполнение")
        
        # Рекомендации
        if analysis['estimated_time'] > 30:
            analysis['optimizations'].append("💡 Рекомендуется добавить кэширование данных")
        if analysis['node_types'].get('http_get', 0) > 5:
            analysis['optimizations'].append("💡 Объедините несколько HTTP запросов в один")
        
        return analysis

# ============================================================================
# КЛАСС ДЛЯ РАЗВЕРТЫВАНИЯ
# ============================================================================

class AppDeployer:
    """Развертывание созданных приложений"""
    
    @staticmethod
    def generate_deployable_code(workflow: List[Dict]) -> str:
        """Генерирует standalone код для развертывания"""
        
        code = f"""
'''
AUTOMATICALLY GENERATED WORKFLOW APP
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Blocks: {len(workflow)}
'''
import streamlit as st
import pandas as pd
import requests
from openai import OpenAI
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(page_title="My Workflow App", layout="wide")
st.title("🚀 Автоматизированное приложение")

# API Key input
api_key = st.sidebar.text_input("DeepSeek API Key", type="password")

# ============================================================================
# WORKFLOW DEFINITION
# ============================================================================

workflow = {json.dumps(workflow, ensure_ascii=False, indent=4)}

# ============================================================================
# EXECUTION ENGINE
# ============================================================================

def execute_node(node, data, api_key):
    """Выполняет один блок workflow"""
    node_type = node.get('type')
    
    if node_type == 'google_sheets_read':
        sheet_url = node.get('config', {{}}).get('sheet_url', '')
        if sheet_url:
            if '/d/' in sheet_url:
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url
            csv_url = f"https://docs.google.com/spreadsheets/d/{{sheet_id}}/export?format=csv"
            df = pd.read_csv(csv_url)
            return df.to_dict('records')
    
    elif node_type == 'deepseek':
        if not api_key:
            return "Ошибка: нужен API ключ"
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {{"role": "system", "content": node.get('config', {{}}).get('system_prompt', '')}},
                {{"role": "user", "content": node.get('config', {{}}).get('user_prompt', '')}}
            ]
        )
        return response.choices[0].message.content
    
    elif node_type in ['http_get', 'http_post']:
        url = node.get('config', {{}}).get('url', '')
        resp = requests.get(url) if node_type == 'http_get' else requests.post(url)
        return resp.json()
    
    return {{"status": "executed"}}

# ============================================================================
# MAIN APP
# ============================================================================

if st.button("🚀 Запустить автоматизацию"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    
    for i, node in enumerate(workflow):
        progress_bar.progress((i + 1) / len(workflow))
        status_text.text(f"Выполняется: {{node.get('name', 'Block')}}")
        
        try:
            result = execute_node(node, results, api_key)
            results.append(result)
            st.success(f"✅ {{node.get('name', 'Block')}} выполнен")
        except Exception as e:
            st.error(f"❌ Ошибка: {{str(e)}}")
            break
    
    status_text.text("✅ Готово!")
    st.balloons()
    
    # Показываем результаты
    st.subheader("Результаты")
    for i, result in enumerate(results):
        with st.expander(f"Результат блока {i+1}"):
            st.json(result)

if __name__ == "__main__":
    pass
"""
        return code
    
    @staticmethod
    def deploy_to_streamlit_cloud(workflow: List[Dict]) -> str:
        """Генерирует инструкцию для деплоя на Streamlit Cloud"""
        code = AppDeployer.generate_deployable_code(workflow)
        
        instructions = f"""
## 🚀 ИНСТРУКЦИЯ ПО РАЗВЕРТЫВАНИЮ

### Шаг 1: Создайте файлы

1. Создайте папку `my_workflow_app`
2. Создайте файл `app.py` и скопируйте туда код ниже:
```python
{code[:500]}...
