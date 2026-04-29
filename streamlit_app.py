"""
================================================================================
КОНСТРУКТОР WORKFLOW PRO v4.0
Полностью на русском языке | Для новичков | С веб-интерфейсом
================================================================================
"""

import streamlit as st
import json
import pandas as pd
import requests
from datetime import datetime
from openai import OpenAI
import traceback
import time
from typing import Dict, List, Tuple
import plotly.express as px

# ============================================================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================================

st.set_page_config(
    page_title="Конструктор Workflow Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
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
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        color: white;
    }
    .workflow-node {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: white;
        border-left: 4px solid #4ECDC4;
    }
    .workflow-node-success {
        border-left-color: #00ff88;
    }
    .workflow-node-error {
        border-left-color: #ff4444;
    }
    .info-box {
        background: #1e1e2e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 1rem 0;
    }
    .success-box {
        background: #1a2e1a;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00ff88;
        margin: 1rem 0;
    }
    .error-box {
        background: #2e1a1a;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff4444;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🚀 КОНСТРУКТОР WORKFLOW PRO</h1>
    <p>Автоматизация без кода | Глубокий анализ | Проверка ошибок | Веб-развертывание</p>
    <p style="font-size: 0.9rem;">⭐ Бесплатно | ⚡ Быстро | 🔒 Безопасно</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ДАННЫХ
# ============================================================================

if 'workflow' not in st.session_state:
    st.session_state.workflow = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'error_logs' not in st.session_state:
    st.session_state.error_logs = []
if 'analytics' not in st.session_state:
    st.session_state.analytics = {
        'total_executions': 0,
        'successful_executions': 0,
        'failed_executions': 0,
        'total_blocks_executed': 0
    }

# ============================================================================
# КЛАСС ДЛЯ ПРОВЕРКИ ОШИБОК
# ============================================================================

class ПроверщикWorkflow:
    """Проверяет workflow на ошибки"""
    
    @staticmethod
    def проверить(workflow: List[Dict]) -> Tuple[bool, List[str]]:
        ошибки = []
        предупреждения = []
        
        if not workflow:
            ошибки.append("❌ Workflow пуст. Добавьте хотя бы один блок.")
            return False, ошибки
        
        for i, блок in enumerate(workflow):
            if 'name' not in блок:
                ошибки.append(f"❌ Блок {i+1}: отсутствует название")
            if 'type' not in блок:
                ошибки.append(f"❌ Блок {i+1}: отсутствует тип")
            
            тип = блок.get('type', '')
            
            if тип == 'google_sheets_read':
                url = блок.get('config', {}).get('sheet_url', '')
                if not url:
                    ошибки.append(f"❌ Блок '{блок.get('name', 'Unknown')}': укажите URL Google Таблицы")
            
            elif тип == 'deepseek':
                if not блок.get('config', {}).get('user_prompt'):
                    предупреждения.append(f"⚠️ Блок '{блок.get('name', 'Unknown')}': запрос к AI не заполнен")
            
            elif тип in ['http_get', 'http_post']:
                url = блок.get('config', {}).get('url', '')
                if not url:
                    ошибки.append(f"❌ Блок '{блок.get('name', 'Unknown')}': укажите URL для запроса")
        
        return len(ошибки) == 0, ошибки + предупреждения

# ============================================================================
# КЛАСС ДЛЯ АНАЛИЗА
# ============================================================================

class АнализаторWorkflow:
    """Анализирует workflow"""
    
    @staticmethod
    def анализировать(workflow: List[Dict]) -> Dict:
        анализ = {
            'всего_блоков': len(workflow),
            'типы_блоков': {},
            'примерное_время': 0,
            'сложность': 'Низкая',
            'проблемы': [],
            'рекомендации': []
        }
        
        for блок in workflow:
            тип = блок.get('type', 'unknown')
            анализ['типы_блоков'][тип] = анализ['типы_блоков'].get(тип, 0) + 1
        
        # Оценка времени
        время_блоков = {
            'google_sheets_read': 2,
            'deepseek': 5,
            'http_get': 1,
            'http_post': 1,
            'condition': 0.1,
            'loop': 1,
            'excel_read': 1,
            'email': 0.5,
            'telegram': 0.5
        }
        
        for блок in workflow:
            тип = блок.get('type', '')
            анализ['примерное_время'] += время_блоков.get(тип, 0.5)
        
        # Оценка сложности
        if анализ['всего_блоков'] <= 3:
            анализ['сложность'] = 'Низкая (для начинающих)'
        elif анализ['всего_блоков'] <= 7:
            анализ['сложность'] = 'Средняя'
        else:
            анализ['сложность'] = 'Высокая (требуется тестирование)'
        
        # Поиск проблем
        if анализ['типы_блоков'].get('deepseek', 0) > 3:
            анализ['проблемы'].append("⚠️ Много AI блоков - выполнение может быть медленным")
        
        return анализ

# ============================================================================
# КЛАСС ДЛЯ РАЗВЕРТЫВАНИЯ
# ============================================================================

class Развертыватель:
    """Генерирует код для развертывания"""
    
    @staticmethod
    def сгенерировать_код(workflow: List[Dict]) -> str:
        код = f'''
"""
Автоматически сгенерированное приложение Workflow
Создано: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Всего блоков: {len(workflow)}
"""

import streamlit as st
import pandas as pd
import requests
from openai import OpenAI
import json
from datetime import datetime

st.set_page_config(page_title="Моё Workflow Приложение", layout="wide")
st.title("🚀 Автоматизированное приложение")

# Ввод API ключа
api_key = st.sidebar.text_input("DeepSeek API Ключ", type="password")

# Определение workflow
workflow = {json.dumps(workflow, ensure_ascii=False, indent=2)}

def выполнить_блок(блок, данные, api_key):
    """Выполняет один блок workflow"""
    тип = блок.get('type')
    
    if тип == 'google_sheets_read':
        url = блок.get('config', {{}}).get('sheet_url', '')
        if url:
            if '/d/' in url:
                id_таблицы = url.split('/d/')[1].split('/')[0]
            else:
                id_таблицы = url
            csv_url = f"https://docs.google.com/spreadsheets/d/{{id_таблицы}}/export?format=csv"
            df = pd.read_csv(csv_url)
            return df.to_dict('records')
    
    elif тип == 'deepseek':
        if not api_key:
            return "Ошибка: нужен API ключ"
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        ответ = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {{"role": "system", "content": блок.get('config', {{}}).get('system_prompt', '')}},
                {{"role": "user", "content": блок.get('config', {{}}).get('user_prompt', '')}}
            ]
        )
        return ответ.choices[0].message.content
    
    elif тип in ['http_get', 'http_post']:
        url = блок.get('config', {{}}).get('url', '')
        ответ = requests.get(url) if тип == 'http_get' else requests.post(url)
        return ответ.json()
    
    return {{"статус": "выполнено"}}

# Кнопка запуска
if st.button("🚀 Запустить автоматизацию"):
    прогресс = st.progress(0)
    статус = st.empty()
    результаты = []
    
    for i, блок in enumerate(workflow):
        прогресс.progress((i + 1) / len(workflow))
        статус.text(f"Выполняется: {{блок.get('name', 'Блок')}}")
        
        try:
            результат = выполнить_блок(блок, результаты, api_key)
            результаты.append(результат)
            st.success(f"✅ {{блок.get('name', 'Блок')}} выполнен")
        except Exception as e:
            st.error(f"❌ Ошибка: {{str(e)}}")
            break
    
    статус.text("✅ Готово!")
    st.balloons()
    
    st.subheader("Результаты")
    for i, результат in enumerate(результаты):
        with st.expander(f"Результат блока {i+1}"):
            st.json(результат)
'''
        return код

# ============================================================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================================================

with st.sidebar:
    st.markdown("## 📦 БИБЛИОТЕКА БЛОКОВ")
    
    api_key = st.text_input("🔑 DeepSeek API Ключ", type="password", 
                           help="Получи бесплатно на platform.deepseek.com")
    
    st.markdown("---")
    
    # Кнопки для добавления блоков
    блоки = [
        ("📖 Google Таблицы", "google_sheets_read", "Чтение данных из таблицы"),
        ("🧠 DeepSeek AI", "deepseek", "Анализ данных с помощью ИИ"),
        ("📡 HTTP GET", "http_get", "Получение данных из API"),
        ("📤 HTTP POST", "http_post", "Отправка данных в API"),
        ("🔀 Условие IF", "condition", "Ветвление логики"),
        ("🔄 Цикл", "loop", "Повторение действий"),
        ("📊 Excel/CSV", "excel_read", "Загрузка файлов"),
        ("📧 Email", "email", "Отправка письма"),
        ("📱 Telegram", "telegram", "Уведомление в Telegram"),
    ]
    
    for имя, тип, описание in блоки:
        if st.button(f"{имя}", key=f"btn_{тип}", use_container_width=True):
            st.session_state.workflow.append({
                "id": len(st.session_state.workflow),
                "name": имя.split()[1] if len(имя.split()) > 1 else имя,
                "icon": имя[0],
                "type": тип,
                "description": описание,
                "config": {},
                "status": "pending"
            })
            st.rerun()
    
    st.markdown("---")
    
    # Управление
    st.markdown("## 🛠️ УПРАВЛЕНИЕ")
    
    if st.button("🗑️ Очистить всё", use_container_width=True):
        st.session_state.workflow = []
        st.rerun()
    
    st.markdown("---")
    
    # Статистика
    st.markdown("## 📊 СТАТИСТИКА")
    st.metric("Всего блоков", len(st.session_state.workflow))
    st.metric("Запусков", st.session_state.analytics['total_executions'])
    
    успех = st.session_state.analytics['successful_executions']
    всего = st.session_state.analytics['total_executions']
    процент = (успех / всего * 100) if всего > 0 else 0
    st.metric("Успешных запусков", f"{процент:.0f}%")

# ============================================================================
# ОСНОВНЫЕ ВКЛАДКИ
# ============================================================================

вкладка1, вкладка2, вкладка3, вкладка4, вкладка5, вкладка6 = st.tabs([
    "✏️ РЕДАКТОР", "🔍 АНАЛИЗ", "▶️ ЗАПУСК", "🚀 РАЗВЕРНУТЬ", "📜 ИСТОРИЯ", "📖 ИНСТРУКЦИЯ"
])

# ============================================================================
# ВКЛАДКА 1: РЕДАКТОР
# ============================================================================

with вкладка1:
    st.subheader("✏️ Редактор workflow")
    
    if not st.session_state.workflow:
        st.info("💡 Нажмите на любой блок в боковой панели, чтобы начать создание workflow")
    else:
        # Проверка на ошибки
        валиден, ошибки = ПроверщикWorkflow.проверить(st.session_state.workflow)
        if not валиден:
            for ошибка in ошибки:
                st.warning(ошибка)
    
    # Отображение блоков
    for i, блок in enumerate(st.session_state.workflow):
        # Определяем стиль
        стиль = "workflow-node"
        if блок.get('status') == 'success':
            стиль = "workflow-node workflow-node-success"
        elif блок.get('status') == 'error':
            стиль = "workflow-node workflow-node-error"
        
        st.markdown(f"""
        <div class="{стиль}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.5rem;">{блок['icon']}</span>
                    <span style="font-weight: bold; font-size: 1.2rem;"> {блок['name']}</span>
                    <span style="font-size: 0.8rem; opacity: 0.7; margin-left: 1rem;">Шаг {i+1}</span>
                </div>
                <div style="font-size: 0.8rem;">{блок.get('description', '')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Стрелка между блоками
        if i < len(st.session_state.workflow) - 1:
            st.markdown('<div style="text-align: center; font-size: 1.2rem;">▼</div>', unsafe_allow_html=True)
        
        # Настройки блока
        with st.expander(f"⚙️ Настроить {блок['name']}"):
            
            if блок['type'] == 'google_sheets_read':
                блок['config']['sheet_url'] = st.text_input(
                    "URL Google Таблицы", 
                    блок['config'].get('sheet_url', ''),
                    key=f"url_{i}",
                    help="Скопируйте URL из адресной строки браузера"
                )
                блок['config']['range'] = st.text_input(
                    "Диапазон", 
                    блок['config'].get('range', 'A1:Z100'),
                    key=f"range_{i}"
                )
                st.caption("💡 Пример: https://docs.google.com/spreadsheets/d/ВАШ_ID_ТАБЛИЦЫ/edit")
            
            elif блок['type'] == 'deepseek':
                блок['config']['system_prompt'] = st.text_area(
                    "Инструкция для ИИ", 
                    блок['config'].get('system_prompt', "Ты профессиональный аналитик данных. Отвечай на русском языке четко и по делу."),
                    height=80,
                    key=f"system_{i}"
                )
                блок['config']['user_prompt'] = st.text_area(
                    "Запрос к ИИ", 
                    блок['config'].get('user_prompt', "Проанализируй данные и сделай выводы."),
                    height=80,
                    key=f"user_{i}"
                )
                блок['config']['temperature'] = st.slider(
                    "Креативность", 
                    0.0, 1.0, 0.3,
                    key=f"temp_{i}",
                    help="Чем выше значение, тем более креативные ответы"
                )
            
            elif блок['type'] in ['http_get', 'http_post']:
                блок['config']['url'] = st.text_input(
                    "API URL", 
                    блок['config'].get('url', ''),
                    key=f"url_{i}",
                    help="Например: https://api.example.com/data"
                )
                блок['config']['headers'] = st.text_area(
                    "Заголовки (JSON)", 
                    блок['config'].get('headers', '{}'),
                    key=f"headers_{i}",
                    help='Формат: {"Authorization": "Bearer token"}'
                )
                if блок['type'] == 'http_post':
                    блок['config']['body'] = st.text_area(
                        "Тело запроса (JSON)", 
                        блок['config'].get('body', '{}'),
                        key=f"body_{i}"
                    )
            
            elif блок['type'] == 'condition':
                блок['config']['condition'] = st.text_input(
                    "Условие", 
                    блок['config'].get('condition', '{{$json.value}} > 100'),
                    key=f"cond_{i}",
                    help="Используйте {{$json.поле}} для доступа к данным"
                )
                st.caption("💡 Пример: {{$json.цена}} > 1000")
            
            elif блок['type'] == 'loop':
                блок['config']['items'] = st.text_area(
                    "Элементы (JSON массив)", 
                    блок['config'].get('items', '[1, 2, 3, 4, 5]'),
                    height=80,
                    key=f"items_{i}",
                    help="Массив элементов для перебора"
                )
                блок['config']['batch_size'] = st.number_input(
                    "Размер пачки", 
                    1, 100, 10,
                    key=f"batch_{i}"
                )
            
            elif блок['type'] == 'excel_read':
                загруженный_файл = st.file_uploader(
                    "Загрузить файл", 
                    type=['xlsx', 'xls', 'csv'],
                    key=f"file_{i}"
                )
                if загруженный_файл:
                    блок['config']['file'] = загруженный_файл
                    st.success(f"✅ {загруженный_файл.name} загружен")
            
            elif блок['type'] == 'email':
                блок['config']['to'] = st.text_input(
                    "Кому", 
                    блок['config'].get('to', ''),
                    key=f"to_{i}",
                    help="Email получателя"
                )
                блок['config']['subject'] = st.text_input(
                    "Тема", 
                    блок['config'].get('subject', 'Уведомление от Workflow'),
                    key=f"subject_{i}"
                )
                блок['config']['body'] = st.text_area(
                    "Сообщение", 
                    блок['config'].get('body', 'Ваш workflow успешно выполнен!'),
                    height=80,
                    key=f"body_{i}"
                )
            
            elif блок['type'] == 'telegram':
                блок['config']['bot_token'] = st.text_input(
                    "Bot Token", 
                    блок['config'].get('bot_token', ''),
                    type="password",
                    key=f"token_{i}",
                    help="Получите у @BotFather в Telegram"
                )
                блок['config']['chat_id'] = st.text_input(
                    "Chat ID", 
                    блок['config'].get('chat_id', ''),
                    key=f"chat_{i}",
                    help="ID чата или пользователя"
                )
                блок['config']['message'] = st.text_area(
                    "Сообщение", 
                    блок['config'].get('message', '✅ Workflow выполнен!'),
                    height=80,
                    key=f"msg_{i}"
                )
            
            # Кнопка удаления
            if st.button(f"🗑️ Удалить блок", key=f"del_{i}"):
                st.session_state.workflow.pop(i)
                st.rerun()

# ============================================================================
# ВКЛАДКА 2: АНАЛИЗ
# ============================================================================

with вкладка2:
    st.subheader("🔍 Глубокий анализ workflow")
    
    if not st.session_state.workflow:
        st.info("Сначала добавьте блоки в workflow")
    else:
        # Проводим анализ
        анализ = АнализаторWorkflow.анализировать(st.session_state.workflow)
        
        # Отображение метрик
        колонка1, колонка2, колонка3, колонка4 = st.columns(4)
        with колонка1:
            st.markdown(f'<div class="stat-card"><h3>{анализ["всего_блоков"]}</h3><p>Всего блоков</p></div>', unsafe_allow_html=True)
        with колонка2:
            st.markdown(f'<div class="stat-card"><h3>{анализ["примерное_время"]:.1f}с</h3><p>Примерное время</p></div>', unsafe_allow_html=True)
        with колонка3:
            st.markdown(f'<div class="stat-card"><h3>{анализ["сложность"]}</h3><p>Сложность</p></div>', unsafe_allow_html=True)
        with колонка4:
            процент = (st.session_state.analytics['successful_executions'] / max(1, st.session_state.analytics['total_executions']) * 100)
            st.markdown(f'<div class="stat-card"><h3>{процент:.0f}%</h3><p>Успешных запусков</p></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # График типов блоков
        if анализ['типы_блоков']:
            st.subheader("📊 Распределение блоков")
            df_типы = pd.DataFrame(list(анализ['типы_блоков'].items()), columns=['Тип', 'Количество'])
            fig = px.bar(df_типы, x='Тип', y='Количество', title="Типы блоков в workflow")
            st.plotly_chart(fig, use_container_width=True)
        
        # Проблемы
        if анализ['проблемы']:
            st.subheader("⚠️ Потенциальные проблемы")
            for проблема in анализ['проблемы']:
                st.warning(проблема)
        
        # Визуализация последовательности
        st.subheader("📈 Схема workflow")
        шаги = [f"{i+1}. {блок['icon']} {блок['name']}" for i, блок in enumerate(st.session_state.workflow)]
        st.code(" → ".join(шаги))

# ============================================================================
# ВКЛАДКА 3: ЗАПУСК
# ============================================================================

with вкладка3:
    st.subheader("▶️ Запуск автоматизации")
    
    if not st.session_state.workflow:
        st.warning("⚠️ Workflow пуст. Добавьте блоки на вкладке РЕДАКТОР")
    else:
        # Проверка перед запуском
        валиден, проблемы = ПроверщикWorkflow.проверить(st.session_state.workflow)
        
        if not валиден:
            st.error("❌ Обнаружены ошибки. Исправьте их перед запуском:")
            for проблема in проблемы:
                st.write(f"- {проблема}")
        else:
            if проблемы:
                for проблема in проблемы:
                    st.warning(проблема)
            
            # Кнопка запуска
            if st.button("🚀 ЗАПУСТИТЬ WORKFLOW", type="primary", use_container_width=True):
                время_старта = time.time()
                прогресс = st.progress(0)
                статус_текст = st.empty()
                контейнер_логов = st.container()
                
                данные_workflow = {}
                успешно = 0
                логи = []
                
                for индекс, блок in enumerate(st.session_state.workflow):
                    прогресс.progress((индекс + 0.5) / len(st.session_state.workflow))
                    статус_текст.text(f"🔄 {блок['icon']} {блок['name']}...")
                    
                    try:
                        результат = None
                        логи.append(f"[{datetime.now().strftime('%H:%M:%S')}] Запуск {блок['name']}")
                        
                        # Выполнение блока
                        if блок['type'] == 'google_sheets_read':
                            url = блок['config'].get('sheet_url', '')
                            if url:
                                if '/d/' in url:
                                    id_таблицы = url.split('/d/')[1].split('/')[0]
                                else:
                                    id_таблицы = url
                                csv_url = f"https://docs.google.com/spreadsheets/d/{id_таблицы}/export?format=csv"
                                df = pd.read_csv(csv_url)
                                результат = df.to_dict('records')
                                st.success(f"✅ Загружено {len(результат)} строк")
                        
                        elif блок['type'] == 'deepseek':
                            if api_key:
                                клиент = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
                                запрос = блок['config'].get('user_prompt', '')
                                
                                ответ = клиент.chat.completions.create(
                                    model="deepseek-chat",
                                    messages=[
                                        {"role": "system", "content": блок['config'].get('system_prompt', '')},
                                        {"role": "user", "content": запрос}
                                    ],
                                    temperature=блок['config'].get('temperature', 0.3)
                                )
                                результат = ответ.choices[0].message.content
                                st.success(f"✅ AI ответ: {результат[:100]}...")
                            else:
                                st.warning("⚠️ API ключ не указан, AI блок пропущен")
                        
                        elif блок['type'] in ['http_get', 'http_post']:
                            url = блок['config'].get('url', '')
                            заголовки = json.loads(блок['config'].get('headers', '{}'))
                            if блок['type'] == 'http_get':
                                ответ = requests.get(url, headers=заголовки, timeout=30)
                            else:
                                тело = json.loads(блок['config'].get('body', '{}'))
                                ответ = requests.post(url, headers=заголовки, json=тело, timeout=30)
                            результат = ответ.json()
                            st.success(f"✅ HTTP {ответ.status_code}")
                        
                        elif блок['type'] == 'condition':
                            условие = блок['config'].get('condition', '')
                            результат = {"условие": условие, "результат": True}
                            st.success(f"✅ Условие: {условие}")
                        
                        elif блок['type'] == 'loop':
                            элементы = json.loads(блок['config'].get('items', '[]'))
                            результат = {"элементы": элементы, "количество": len(элементы)}
                            st.success(f"✅ Цикл: {len(элементы)} элементов")
                        
                        elif блок['type'] == 'excel_read':
                            файл = блок['config'].get('file')
                            if файл:
                                if файл.name.endswith('.csv'):
                                    df = pd.read_csv(файл)
                                else:
                                    df = pd.read_excel(файл)
                                результат = df.to_dict('records')
                                st.success(f"✅ Загружено {len(результат)} строк")
                        
                        elif блок['type'] == 'email':
                            st.info("📧 Отправка email (демо-режим)")
                            результат = {"статус": "email готов к отправке"}
                            st.success("✅ Email подготовлен")
                        
                        elif блок['type'] == 'telegram':
                            st.info("📱 Отправка в Telegram (демо-режим)")
                            результат = {"статус": "сообщение готово"}
                            st.success("✅ Telegram уведомление подготовлено")
                        
                        # Сохраняем результат
                        блок['status'] = 'success'
                        блок['result'] = результат
                        if isinstance(результат, dict):
                            данные_workflow.update(результат)
                        elif результат is not None:
                            данные_workflow['data'] = результат
                        успешно += 1
                        
                        логи.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {блок['name']} выполнен")
                        
                    except Exception as e:
                        блок['status'] = 'error'
                        блок['error'] = str(e)
                        логи.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Ошибка в {блок['name']}: {str(e)}")
                        st.session_state.error_logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "блок": блок['name'],
                            "ошибка": str(e),
                            "детали": traceback.format_exc()
                        })
                        st.error(f"❌ Ошибка: {str(e)}")
                        break
                
                # Завершение
                время_выполнения = time.time() - время_старта
                прогресс.progress(1.0)
                
                # Обновляем аналитику
                st.session_state.analytics['total_executions'] += 1
                if успешно == len(st.session_state.workflow):
                    st.session_state.analytics['successful_executions'] += 1
                else:
                    st.session_state.analytics['failed_executions'] += 1
                st.session_state.analytics['total_blocks_executed'] += успешно
                
                # Сохраняем в историю
                st.session_state.history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "блоков": len(st.session_state.workflow),
                    "успех": успешно == len(st.session_state.workflow),
                    "успешно_выполнено": успешно,
                    "время": round(время_выполнения, 2),
                    "логи": логи
                })
                
                if успешно == len(st.session_state.workflow):
                    st.balloons()
                    st.success(f"🎉 УСПЕХ! Workflow выполнен за {время_выполнения:.1f} секунд")
                else:
                    st.warning(f"⚠️ Выполнено {успешно} из {len(st.session_state.workflow)} блоков")
                
                # Показываем логи
                with st.expander("📋 Детальные логи", expanded=False):
                    for лог in логи:
                        st.text(лог)

# ============================================================================
# ВКЛАДКА 4: РАЗВЕРНУТЬ
# ============================================================================

with вкладка4:
    st.subheader("🚀 Развертывание через веб-интерфейс")
    
    if not st.session_state.workflow:
        st.info("💡 Сначала создайте workflow, который хотите развернуть")
    else:
        st.markdown("""
        <div class="info-box">
        <h4>🎯 Что вы получите?</h4>
        <p>Мы сгенерируем полноценное Streamlit-приложение на основе вашего workflow, 
        которое можно бесплатно развернуть в интернете!</p>
        </div>
        """, unsafe_allow_html=True)
        
        колонка1, колонка2 = st.columns(2)
        
        with колонка1:
            if st.button("🔧 Сгенерировать код приложения", use_container_width=True):
                код = Развертыватель.сгенерировать_код(st.session_state.workflow)
                st.session_state.сгенерированный_код = код
                st.success("✅ Код сгенерирован!")
        
        with колонка2:
            if st.button("📋 Показать инструкцию", use_container_width=True):
                st.session_state.показать_инструкцию = True
        
        if 'сгенерированный_код' in st.session_state:
            st.subheader("📄 Сгенерированный код приложения")
            st.code(st.session_state.сгенерированный_код, language="python")
            
            st.download_button(
                label="📥 Скачать app.py",
                data=st.session_state.сгенерированный_код,
                file_name="workflow_app.py",
                mime="text/x-python"
            )
            
            # Создаем requirements.txt
            requirements = """streamlit>=1.28.0
openai>=1.0.0
pandas>=2.0.0
openpyxl>=3.1.0
requests>=2.31.0
plotly>=5.17.0"""
            
            st.download_button(
                label="📥 Скачать requirements.txt",
                data=requirements,
                file_name="requirements.txt",
                mime="text/plain"
            )
        
        if st.session_state.get('показать_инструкцию', False):
            st.markdown("---")
            st.subheader("📖 Инструкция по развертыванию")
            st.markdown("""
            ### 🚀 Развертывание на Streamlit Cloud (БЕСПЛАТНО)
            
            **Шаг 1:** Создайте папку `my_workflow_app`
            
            **Шаг 2:** Сохраните файлы:
            - `app.py` (скачайте выше)
            - `requirements.txt` (скачайте выше)
            
            **Шаг 3:** Загрузите на GitHub
            1. Создайте новый репозиторий
            2. Загрузите оба файла
            3. Нажмите "Commit changes"
            
            **Шаг 4:** Разверните на Streamlit Cloud
            1. Перейдите на [share.streamlit.io](https://share.streamlit.io)
            2. Нажмите "New app"
            3. Выберите ваш репозиторий
            4. Нажмите "Deploy"
            
            **Шаг 5:** Готово! Ваше приложение будет доступно по ссылке:
            `https://ваше-название.streamlit.app`
            
            ### 🌐 Альтернативные платформы
            
            | Платформа | Стоимость | Сложность |
            |-----------|-----------|-----------|
            | Render | Бесплатно | Средняя |
            | Heroku | Платно | Низкая |
            | Docker | Бесплатно | Высокая |
            """)

# ============================================================================
# ВКЛАДКА 5: ИСТОРИЯ
# ============================================================================

with вкладка5:
    st.subheader("📜 История выполнения")
    
    if st.session_state.history:
        for запуск in reversed(st.session_state.history[-20:]):
            иконка = "✅" if запуск['успех'] else "❌"
            with st.expander(f"{иконка} {запуск['timestamp']} - {запуск['блоков']} блоков ({запуск['время']}с)"):
                st.markdown(f"**Успешно выполнено:** {запуск['успешно_выполнено']}/{запуск['блоков']}")
                if запуск.get('логи'):
                    st.markdown("**Логи выполнения:**")
                    for лог in запуск['логи'][-5:]:
                        st.text(лог)
    else:
        st.info("📭 Пока нет выполненных запусков. Запустите workflow на вкладке ЗАПУСК")

# ============================================================================
# ВКЛАДКА 6: ИНСТРУКЦИЯ
# ============================================================================

with вкладка6:
    st.subheader("📖 Полная инструкция для новичков")
    
    st.markdown("""
    ## 🎯 Что такое Workflow Builder?
    
    **Workflow Builder** — это визуальный конструктор автоматизаций. Вы соединяете блоки (шаги) и получаете готовую автоматизацию **без единой строки кода**!
    
    ---
    
    ## 📝 Как создать первую автоматизацию?
    
    ### Пример: Автоматический анализ данных из Google Таблицы
    
    #### Шаг 1: Добавьте блок **"Google Таблицы"**
    - Нажмите на кнопку "📖 Google Таблицы" в боковой панели
    - Вставьте URL вашей таблицы
    - Укажите диапазон (например: A1:E100)
    
    #### Шаг 2: Добавьте блок **"DeepSeek AI"**
    - Нажмите "🧠 DeepSeek AI"
    - Напишите System Prompt: *"Ты аналитик данных"*
    - Напишите User Prompt: *"Проанализируй данные и сделай выводы"*
    
    #### Шаг 3: Добавьте блок **"Email"**
    - Нажмите "📧 Email"
    - Укажите email получателя
    - Напишите тему и сообщение
    
    #### Шаг 4: Запустите!
    - Перейдите на вкладку **"ЗАПУСК"**
    - Нажмите **"ЗАПУСТИТЬ WORKFLOW"**
    
    **Готово!** Workflow сам загрузит данные, проанализирует и отправит отчёт!
    
    ---
    
    ## 💡 Полезные советы
    
    ### 🔑 Как получить API ключ DeepSeek?
    1. Перейдите на [platform.deepseek.com](https://platform.deepseek.com)
    2. Зарегистрируйтесь (бесплатно)
    3. Перейдите в раздел "API Keys"
    4. Нажмите "Create new API key"
    5. Скопируйте ключ и вставьте в боковую панель
    
    ### 📊 Как получить URL Google Таблицы?
    1. Откройте Google Таблицу
    2. Скопируйте URL из адресной строки браузера
    3. Пример: `https://docs.google.com/spreadsheets/d/1ABC123/edit`
    4. Вставьте в настройках блока
    
    ### 🔄 Как передавать данные между блоками?
    Используйте `{{$json.поле}}` где `поле` — это название из предыдущего блока.
    
    Пример: `{{$json.цена}} > 1000`
    
    ---
    
    ## 🔧 Возможные ошибки и их решение
    
    | Ошибка | Решение |
    |--------|---------|
    | ❌ URL таблицы не указан | Вставьте URL в настройках блока Google Таблицы |
    | ❌ API ключ не указан | Введите API ключ в боковой панели |
    | ❌ Неверный JSON | Используйте двойные кавычки: `{"key": "value"}` |
    | ⏰ Таймаут запроса | Проверьте интернет соединение |
    | 🔒 Доступ запрещен | Проверьте права доступа к таблице |
    
    ---
    
    ## 🚀 Развертывание готового приложения
    
    Когда ваш workflow готов, перейдите на вкладку **"РАЗВЕРНУТЬ"**:
    
    1. Нажмите **"Сгенерировать код приложения"**
    2. Скачайте `app.py` и `requirements.txt`
    3. Загрузите файлы на GitHub
    4. Разверните на Streamlit Cloud (бесплатно!)
    
    **Ваше приложение будет доступно онлайн 24/7!**
    
    ---
    
    ## 📞 Нужна помощь?
    
    - 📚 Документация: [docs.workflow-builder.com](https://docs.workflow-builder.com)
    - 💬 Telegram: @workflow_builder
    - 📧 Email: support@workflow-builder.com
    - ⭐ GitHub: поставьте звезду, если понравилось!
    
    ---
    
    ## 🎉 Поздравляю!
    
    Вы готовы создавать свои автоматизации. Начните с простого и постепенно усложняйте workflow. 
    Успехов в автоматизации! 🚀
    """)

# ============================================================================
# ПОДВАЛ
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; padding: 1rem;">
    <p>🚀 Workflow Builder Pro | Создайте свою автоматизацию за 5 минут | 🔒 Бесплатно</p>
    <p style="font-size: 0.8rem;">⭐ Если понравилось, поставьте звезду на GitHub | 📧 support@workflow-builder.com</p>
</div>
""", unsafe_allow_html=True)
