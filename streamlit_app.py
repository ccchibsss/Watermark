"""
================================================================================
WORKFLOW BUILDER PRO v9.0.1 – ПОЛНАЯ МОНОПОТОЧНАЯ ВЕРСИЯ
Обучаемые ИИ-агенты | Расширенная работа с таблицами | Голосовой ввод | Мобильная адаптация
================================================================================

Исправления v9.0.1:
    ✅ Белый текст на всех тёмных фонах (полный CSS)
    ✅ Исправлена ошибка импорта: KeyError: 'role' → безопасная десериализация
    ✅ Валидация session_state при загрузке агентов
    ✅ Полная монопоточная архитектура (без asyncio/multiprocessing)
    ✅ Улучшена читаемость: типизация, docstrings, логирование

Зависимости:
    pip install streamlit pandas openpyxl openai plotly requests
    pip install SpeechRecognition gTTS  # опционально, для голоса

Автор: Workflow Builder Team
Версия: 9.0.1
Дата: 2026
Лицензия: MIT
================================================================================
"""

# ============================================================================
# ИМПОРТ ЗАВИСИМОСТЕЙ
# ============================================================================
import streamlit as st
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import re
import hashlib
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import plotly.express as px
from openai import OpenAI
from io import BytesIO
import base64
import logging
import os
import tempfile

# Библиотеки для работы с таблицами
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
    from openpyxl.utils import get_column_letter, column_index_from_string
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference, Series
    from openpyxl.worksheet.datavalidation import DataValidation
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False
    openpyxl = None

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_SUPPORT = True
except ImportError:
    GSHEETS_SUPPORT = False
    gspread = None

# Голосовые библиотеки
try:
    import speech_recognition as sr
    from gtts import gTTS
    VOICE_SUPPORT = True
except ImportError:
    VOICE_SUPPORT = False
    sr = None
    gTTS = None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# ============================================================================
# КОНСТАНТЫ И КОНФИГУРАЦИЯ
# ============================================================================
@dataclass
class AppConfig:
    """Глобальная конфигурация приложения"""
    APP_TITLE: str = "Workflow Builder Pro – Голосовой помощник"
    APP_ICON: str = "🧠"
    APP_VERSION: str = "9.0.1"
    
    # API настройки
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    API_TIMEOUT: int = 60
    MAX_TOKENS: int = 4096
    
    # Настройки таблиц
    MAX_ROWS_GOOGLE: int = 10000
    MAX_ROWS_EXCEL: int = 100000
    SUPPORTED_EXCEL_FORMATS: Tuple[str, ...] = ("xlsx", "xlsm", "xls")
    DEFAULT_SHEET_NAME: str = "Sheet1"
    
    # Настройки кэширования
    CACHE_TTL_SECONDS: int = 300
    
    # Настройки интерфейса
    DEFAULT_LANGUAGE: str = "ru"
    MOBILE_BREAKPOINT: int = 768
    ITEMS_PER_PAGE: int = 10
    
    # Цветовая схема
    COLORS: Dict[str, str] = field(default_factory=lambda: {
        'primary': '#667eea',
        'primary_dark': '#764ba2',
        'success': '#00ff88',
        'error': '#ff4444',
        'warning': '#ffa500',
        'accent': '#4ECDC4',
        'dark_bg': '#1a1a2e',
        'dark_bg_2': '#16213e',
        'card_bg': '#1e1e2e'
    })


CONFIG = AppConfig()


# ============================================================================
# DECORATORS И УТИЛИТЫ
# ============================================================================
def cache_result(ttl_seconds: int = CONFIG.CACHE_TTL_SECONDS):
    """
    Декоратор для кэширования результатов функций.
    
    Args:
        ttl_seconds: Время жизни кэша в секундах
    """
    def decorator(func: Callable):
        cache: Dict[str, Tuple[Any, float]] = {}
        
        def wrapper(*args, **kwargs) -> Any:
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            current_time = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    logger.debug(f"Cache hit: {key}")
                    return result
            
            logger.debug(f"Cache miss: {key}, executing function")
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result
        return wrapper
    return decorator


def handle_errors(default_return: Any = None):
    """
    Декоратор для обработки исключений с логированием.
    
    Args:
        default_return: Значение, возвращаемое при ошибке
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в {func.__name__}: {str(e)}", exc_info=True)
                st.error(f"⚠️ {func.__name__}: {str(e)}")
                return default_return
        return wrapper
    return decorator


def format_bytes(size: int) -> str:
    """Форматирует размер в байтах в человекочитаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


# ============================================================================
# ENUMS ДЛЯ ТИПИЗАЦИИ
# ============================================================================
class NodeType(Enum):
    """Типы узлов workflow"""
    GOOGLE_SHEETS_READ = "google_sheets_read"
    GOOGLE_SHEETS_WRITE = "google_sheets_write"
    EXCEL_READ = "excel_read"
    EXCEL_WRITE = "excel_write"
    EXCEL_FORMAT = "excel_format"
    EXCEL_CHART = "excel_chart"
    DEEPSEEK_AI = "deepseek"
    CONDITION = "condition"
    LOOP = "loop"
    HTTP_GET = "http_get"
    HTTP_POST = "http_post"
    EMAIL = "email"
    TELEGRAM = "telegram"
    AI_AGENT = "ai_agent"
    DATA_CLEAN = "data_clean"
    PIVOT_TABLE = "pivot_table"
    FILTER = "filter"
    TRANSFORM = "transform"


class ConditionType(Enum):
    """Типы условий для парсинга"""
    GREATER = "greater"
    LESS = "less"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    BETWEEN = "between"
    IN_LIST = "in_list"
    CUSTOM = "custom"


class MemoryImportance(Enum):
    """Уровни важности памяти агента"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class WorkflowStatus(Enum):
    """Статусы выполнения workflow"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    PAUSED = "paused"


# ============================================================================
# CSS СТИЛИ С РАСШИРЕННОЙ МОБИЛЬНОЙ АДАПТАЦИЕЙ – ИСПРАВЛЕНО: БЕЛЫЙ ТЕКСТ
# ============================================================================
def get_app_styles() -> str:
    """Возвращает CSS стили для приложения с белым текстом на тёмном фоне"""
    return """
    <style>
        /* ========== БАЗОВЫЕ СТИЛИ ========== */
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --dark-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            --success-color: #00ff88;
            --error-color: #ff4444;
            --warning-color: #ffa500;
            --accent-color: #4ECDC4;
            --card-bg: #1e1e2e;
            --text-primary: #ffffff;
            --text-secondary: rgba(255,255,255,0.92);
            --text-muted: rgba(255,255,255,0.7);
            --bg-input: #2a2a3e;
        }
        
        /* Глобальный сброс цвета текста для тёмных секций */
        .main-header,
        .agent-card,
        .workflow-node,
        .memory-box,
        .condition-box,
        .info-box,
        .stat-card,
        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] div,
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] span,
        div[data-testid="stExpander"] label,
        div[data-testid="stExpander"] small,
        .stMarkdown,
        .stMarkdown p,
        .stMarkdown span,
        .stMarkdown strong,
        .stMarkdown code {
            color: var(--text-primary) !important;
        }
        
        .agent-card small,
        .workflow-node small,
        .memory-box small,
        .condition-box small,
        .info-box small,
        .agent-stats,
        .stCaption {
            color: var(--text-muted) !important;
        }
        
        .main-header {
            background: var(--primary-gradient);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            animation: fadeIn 1s ease-in;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .main-header h1 { 
            color: white !important; 
            margin: 0; 
            font-size: 2.5rem; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .main-header p { 
            color: rgba(255,255,255,0.95) !important; 
            margin: 0.5rem 0 0 0; 
            font-size: 1.1rem;
        }
        
        .version-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-top: 0.5rem;
            color: white !important;
        }
        
        /* ========== КАРТОЧКИ АГЕНТОВ ========== */
        .agent-card {
            background: var(--dark-gradient);
            border-radius: 15px; 
            padding: 1rem; 
            margin: 0.5rem 0;
            border-left: 4px solid var(--accent-color); 
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            color: var(--text-primary) !important;
        }
        
        .agent-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.1), transparent);
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .agent-card:hover { 
            transform: translateX(5px); 
            box-shadow: 0 8px 25px rgba(0,0,0,0.4);
        }
        
        .agent-card:hover::before { opacity: 1; }
        
        .agent-card-selected {
            border-left-color: var(--success-color);
            background: linear-gradient(135deg, #0a2e1f 0%, #0a1a10 100%);
            box-shadow: 0 0 20px rgba(0,255,136,0.2);
        }
        
        .agent-stats {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.8rem;
            opacity: 0.9;
            color: var(--text-muted) !important;
        }
        
        /* ========== СТАТИСТИКА ========== */
        .stat-card {
            background: var(--primary-gradient);
            padding: 1.2rem; 
            border-radius: 15px; 
            text-align: center; 
            color: white !important;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .stat-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .stat-card h3 { 
            margin: 0; 
            font-size: 2rem; 
            font-weight: bold;
            color: white !important;
        }
        
        .stat-card p { 
            margin: 0.3rem 0 0 0; 
            opacity: 0.9;
            font-size: 0.9rem;
            color: rgba(255,255,255,0.95) !important;
        }
        
        /* ========== БЛОКИ ПАМЯТИ И УСЛОВИЙ ========== */
        .memory-box, .condition-box, .info-box {
            background: var(--card-bg); 
            padding: 1rem; 
            border-radius: 10px;
            margin: 0.5rem 0;
            border-left: 4px solid var(--accent-color);
            color: var(--text-primary) !important;
        }
        
        .memory-box { border-left-color: var(--warning-color); }
        .condition-box { 
            border-left-color: var(--warning-color); 
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            color: #e0e0ff !important;
        }
        .info-box { border-left-color: var(--accent-color); }
        
        /* ========== УЗЛЫ WORKFLOW ========== */
        .workflow-node {
            background: var(--dark-gradient);
            border-radius: 15px; 
            padding: 1rem; 
            margin: 0.5rem 0; 
            color: var(--text-primary) !important;
            border-left: 4px solid var(--accent-color); 
            transition: all 0.3s ease;
            position: relative;
        }
        
        .workflow-node::after {
            content: '';
            position: absolute;
            bottom: -10px; left: 50%;
            width: 2px; height: 10px;
            background: var(--accent-color);
            transform: translateX(-50%);
        }
        
        .workflow-node:hover { 
            transform: translateX(5px); 
            box-shadow: 0 5px 20px rgba(0,0,0,0.4);
        }
        
        .workflow-node-success {
            border-left-color: var(--success-color);
            background: linear-gradient(135deg, #0a2e1f 0%, #0a1a10 100%);
        }
        
        .workflow-node-error {
            border-left-color: var(--error-color);
            background: linear-gradient(135deg, #3e1a1a 0%, #2a0f0f 100%);
        }
        
        .workflow-connector {
            text-align: center;
            font-size: 1.2rem;
            color: var(--accent-color) !important;
            margin: 0.3rem 0;
        }
        
        /* ========== ЭЛЕМЕНТЫ УПРАВЛЕНИЯ ========== */
        .stButton button {
            border-radius: 10px !important; 
            font-weight: 600 !important;
            transition: all 0.2s ease;
            border: none !important;
            color: white !important;
        }
        
        .stButton button:hover { 
            transform: scale(1.03); 
            box-shadow: 0 5px 20px rgba(0,0,0,0.25);
        }
        
        .stTextArea textarea, 
        .stTextInput input,
        .stSelectbox select,
        .stNumberInput input { 
            border-radius: 10px; 
            border: 1px solid #444 !important;
            transition: border-color 0.2s;
            color: var(--text-primary) !important;
            background: var(--bg-input) !important;
        }
        
        .stTextArea textarea:focus,
        .stTextInput input:focus,
        .stSelectbox select:focus,
        .stNumberInput input:focus {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 2px rgba(78, 205, 196, 0.3);
        }
        
        .stTextArea textarea::placeholder,
        .stTextInput input::placeholder,
        .stSelectbox select::placeholder {
            color: rgba(255,255,255,0.5) !important;
        }
        
        /* ========== EXPANDER ========== */
        div[data-testid="stExpander"] details {
            background: var(--dark-gradient);
            border-radius: 15px; 
            border: none;
            margin: 0.5rem 0;
            color: var(--text-primary) !important;
        }
        
        div[data-testid="stExpander"] summary { 
            color: white !important; 
            font-weight: 600;
            padding: 0.8rem 1rem;
        }
        
        /* Вложенный контент в expander'ах */
        div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"],
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] span,
        div[data-testid="stExpander"] label,
        div[data-testid="stExpander"] small {
            color: var(--text-secondary) !important;
        }
        
        /* ========== ТАБЛИЦЫ ========== */
        .dataframe {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .dataframe th {
            background: var(--primary-gradient) !important;
            color: white !important;
        }
        
        .dataframe td {
            color: var(--text-primary) !important;
            background: var(--card-bg) !important;
        }
        
        /* ========== CODE BLOCKS ========== */
        code, pre, .stCode {
            background: rgba(255,255,255,0.1) !important;
            color: var(--success-color) !important;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
        
        /* ========== ССЫЛКИ ========== */
        .agent-card a,
        .workflow-node a,
        .memory-box a,
        .info-box a {
            color: var(--accent-color) !important;
            text-decoration: none;
        }
        
        .agent-card a:hover,
        .workflow-node a:hover,
        .memory-box a:hover,
        .info-box a:hover {
            color: var(--success-color) !important;
            text-decoration: underline;
        }
        
        /* ========== TAGS ========== */
        .tag {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            margin: 0.2rem;
            color: white !important;
        }
        .tag-success { background: rgba(0,255,136,0.2); }
        .tag-error { background: rgba(255,68,68,0.2); }
        .tag-warning { background: rgba(255,165,0,0.2); }
        .tag-info { background: rgba(78,205,196,0.2); }
        
        /* ========== МОБИЛЬНАЯ АДАПТАЦИЯ ========== */
        @media (max-width: 768px) {
            .main-header { padding: 1.5rem; border-radius: 15px; }
            .main-header h1 { font-size: 1.8rem !important; }
            .main-header p { font-size: 0.95rem !important; }
            
            .stat-card { padding: 1rem; }
            .stat-card h3 { font-size: 1.5rem !important; }
            .stat-card p { font-size: 0.85rem !important; }
            
            .stButton button { 
                padding: 0.8rem 1.5rem !important; 
                font-size: 1rem !important;
                width: 100%;
            }
            
            .stTextArea textarea, 
            .stTextInput input { 
                font-size: 1rem !important; 
                padding: 0.9rem !important;
            }
            
            div[data-testid="column"] {
                flex: 1 1 100% !important;
                max-width: 100% !important;
            }
            
            .agent-card, .workflow-node, .memory-box {
                padding: 0.9rem !important;
                margin: 0.5rem 0 !important;
            }
            
            .desktop-only { display: none !important; }
            .mobile-only { display: block !important; }
        }
        
        @media (min-width: 769px) {
            div[data-testid="column"] {
                flex: 1 1 48% !important;
            }
            .mobile-only { display: none !important; }
        }
        
        /* ========== АНИМАЦИИ ========== */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .loading { animation: pulse 1.5s infinite; }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* ========== ПРОГРЕСС БАР ========== */
        .progress-container {
            background: var(--card-bg);
            border-radius: 10px;
            padding: 0.5rem;
            margin: 0.5rem 0;
        }
        
        .progress-bar {
            height: 8px;
            background: var(--primary-gradient);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
    </style>
    """


# ============================================================================
# КЛАСС ДЛЯ ПРЕОБРАЗОВАНИЯ РУССКИХ УСЛОВИЙ
# ============================================================================
class RussianConditionParser:
    """
    Преобразует условия на русском языке в исполняемый код.
    
    Поддерживает сложные конструкции:
    - Простые сравнения: "цена больше 1000"
    - Логические операторы: "если ... то ... иначе"
    - Составные условия: "цена между 100 и 500 И статус равен 'активен'"
    - Работа с полями: "{{поле}} содержит 'срочно'"
    
    Attributes:
        PATTERNS: Словарь регулярных выражений для распознавания условий
        OPERATOR_MAP: Словарь замены русских операторов на Python
        EXAMPLES: Список примеров условий для справки
    """
    
    PATTERNS: Dict[str, str] = {
        'greater': r'(.+?)\s+(больше|выше|превышает|>)\s+(.+)',
        'less': r'(.+?)\s+(меньше|ниже|<)\s+(.+)',
        'equal': r'(.+?)\s+(равно|равняется|==|=|есть)\s+(.+)',
        'not_equal': r'(.+?)\s+(не равно|не равняется|!=|<>|не есть)\s+(.+)',
        'contains': r'(.+?)\s+(содержит|включает|имеет|в себе)\s+(.+)',
        'not_contains': r'(.+?)\s+(не содержит|не включает)\s+(.+)',
        'starts_with': r'(.+?)\s+(начинается с|начинается)\s+(.+)',
        'ends_with': r'(.+?)\s+(заканчивается на|заканчивается)\s+(.+)',
        'is_empty': r'(.+?)\s+(пусто|не заполнено|отсутствует|пустое|is empty)',
        'is_not_empty': r'(.+?)\s+(не пусто|заполнено|присутствует)',
        'between': r'(.+?)\s+(между|от)\s+(.+?)\s+(и|до)\s+(.+)',
        'in_list': r'(.+?)\s+(в\s+списке|один из|включая)\s+(.+)',
    }
    
    OPERATOR_MAP: Dict[str, str] = {
        'больше': '>', 'выше': '>', 'превышает': '>',
        'меньше': '<', 'ниже': '<',
        'равно': '==', 'равняется': '==', 'есть': '==',
        'не равно': '!=', 'не равняется': '!=', 'не есть': '!=',
        'содержит': 'in', 'включает': 'in',
        'начинается с': '.startswith(', 'заканчивается на': '.endswith(',
    }
    
    EXAMPLES: List[str] = [
        "если цена больше 1000 то отправить уведомление",
        "если статус равно 'успех' иначе отправить ошибку", 
        "если количество меньше 5 то пополнить склад",
        "если текст содержит 'срочно' то отметить как важное",
        "если поле пусто то заполнить значением по умолчанию",
        "если сумма между 1000 и 5000 то одобрить заявку",
        "если имя начинается с 'VIP' то применить скидку",
        "если дата заканчивается на '2024' то архивировать",
    ]
    
    @classmethod
    def parse(cls, condition_text: str) -> Dict[str, Any]:
        """
        Преобразует русское условие в структурированный формат.
        
        Args:
            condition_text: Условие на русском языке
            
        Returns:
            Dict с полями: original, type, condition, code, examples, errors
        """
        condition_text = condition_text.lower().strip()
        
        result: Dict[str, Any] = {
            'original': condition_text,
            'type': ConditionType.CUSTOM.value,
            'condition': condition_text,
            'code': None,
            'python_expr': None,
            'variables': [],
            'examples': cls.EXAMPLES.copy(),
            'errors': [],
            'confidence': 0.0
        }
        
        # Обработка конструкции "если ... то ... иначе"
        if 'если' in condition_text:
            result = cls._parse_if_statement(condition_text, result)
            return result
        
        # Поиск по паттернам
        for pattern_type, pattern in cls.PATTERNS.items():
            match = re.search(pattern, condition_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                result['type'] = pattern_type
                result['matches'] = groups
                result['code'] = cls._generate_code(pattern_type, groups)
                result['python_expr'] = cls._to_python_expr(pattern_type, groups)
                result['variables'] = cls._extract_variables(condition_text)
                result['confidence'] = 0.9
                break
        
        # Если не распознано - пробуем общий парсер
        if result['code'] is None:
            result['code'], result['errors'] = cls._fallback_parse(condition_text)
            result['confidence'] = 0.5 if result['code'] else 0.0
        
        return result
    
    @classmethod
    def _parse_if_statement(cls, text: str, result: Dict) -> Dict:
        """Парсит конструкцию если-то-иначе"""
        text = re.sub(r'^если\s+', '', text)
        
        then_part = None
        else_part = None
        
        if 'иначе' in text:
            parts = re.split(r'\s+иначе\s+', text)
            text = parts[0]
            else_part = parts[1] if len(parts) > 1 else None
        
        if ' то ' in text:
            parts = text.split(' то ', 1)
            condition = parts[0]
            then_part = parts[1] if len(parts) > 1 else None
        else:
            condition = text
        
        result['type'] = 'if_else' if else_part else 'if_then'
        result['condition'] = condition.strip()
        result['then_action'] = then_part.strip() if then_part else None
        result['else_action'] = else_part.strip() if else_part else None
        
        cond_code = cls._to_python_expr('custom', (condition,))
        result['code'] = f"if {cond_code}:\n    # {then_part or 'действие'}"
        if else_part:
            result['code'] += f"\nelse:\n    # {else_part}"
        
        result['variables'] = cls._extract_variables(condition)
        result['confidence'] = 0.85
        return result
    
    @classmethod
    def _generate_code(cls, pattern_type: str, groups: tuple) -> Optional[str]:
        """Генерирует Python-код из распознанного паттерна"""
        templates = {
            'greater': lambda g: f"if {g[0].strip()} > {g[2].strip()}:",
            'less': lambda g: f"if {g[0].strip()} < {g[2].strip()}:",
            'equal': lambda g: f"if {g[0].strip()} == {g[2].strip()}:",
            'not_equal': lambda g: f"if {g[0].strip()} != {g[2].strip()}:",
            'contains': lambda g: f"if {g[2].strip()} in {g[0].strip()}:",
            'not_contains': lambda g: f"if {g[2].strip()} not in {g[0].strip()}:",
            'starts_with': lambda g: f"if {g[0].strip()}.startswith({g[2].strip()}):",
            'ends_with': lambda g: f"if {g[0].strip()}.endswith({g[2].strip()}):",
            'is_empty': lambda g: f"if not {g[0].strip()}:",
            'is_not_empty': lambda g: f"if {g[0].strip()}:",
            'between': lambda g: f"if {g[1].strip()} <= {g[0].strip()} <= {g[3].strip()}:",
        }
        return templates.get(pattern_type, lambda g: None)(groups)
    
    @classmethod
    def _to_python_expr(cls, pattern_type: str, groups: tuple) -> str:
        """Преобразует условие в Python-выражение (без if)"""
        exprs = {
            'greater': lambda g: f"{g[0].strip()} > {g[2].strip()}",
            'less': lambda g: f"{g[0].strip()} < {g[2].strip()}",
            'equal': lambda g: f"{g[0].strip()} == {g[2].strip()}",
            'contains': lambda g: f"{g[2].strip()} in {g[0].strip()}",
            'is_empty': lambda g: f"not {g[0].strip()}",
            'between': lambda g: f"{g[1].strip()} <= {g[0].strip()} <= {g[3].strip()}",
        }
        return exprs.get(pattern_type, lambda g: f"# {pattern_type}: {groups}")(groups)
    
    @classmethod
    def _extract_variables(cls, text: str) -> List[str]:
        """Извлекает имена переменных из условия"""
        vars_found = re.findall(r'\{\{(\w+)\}\}', text)
        if not vars_found:
            words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ_][a-zA-Zа-яА-яЁё0-9_]*\b', text)
            keywords = {'если', 'то', 'иначе', 'и', 'или', 'не', 'больше', 'меньше', 'равно'}
            vars_found = [w for w in words if w.lower() not in keywords and len(w) > 2][:5]
        return vars_found
    
    @classmethod
    def _fallback_parse(cls, text: str) -> Tuple[Optional[str], List[str]]:
        """Резервный парсер для нераспознанных условий"""
        errors: List[str] = []
        
        for rus, eng in cls.OPERATOR_MAP.items():
            text = re.sub(rf'\b{rus}\b', eng, text, flags=re.IGNORECASE)
        
        text = re.sub(r'\{\{(\w+)\}\}', r'data.get("\1", None)', text)
        
        try:
            compile(text, '<string>', 'eval')
            return text, errors
        except SyntaxError as e:
            errors.append(f"Синтаксическая ошибка: {e}")
            return None, errors


# ============================================================================
# DATA CLASSES ДЛЯ ТАБЛИЦ
# ============================================================================
@dataclass
class TableCell:
    """Представляет ячейку таблицы с форматированием"""
    row: int
    column: int
    value: Any
    formula: Optional[str] = None
    font: Optional[Dict] = None
    fill: Optional[Dict] = None
    border: Optional[Dict] = None
    alignment: Optional[Dict] = None
    data_validation: Optional[Dict] = None
    
    def to_openpyxl_style(self) -> Dict[str, Any]:
        """Конвертирует стили в формат openpyxl"""
        styles = {}
        if self.font and openpyxl:
            styles['font'] = Font(**{k: v for k, v in self.font.items() if v is not None})
        if self.fill and openpyxl:
            styles['fill'] = PatternFill(**self.fill)
        if self.border and openpyxl:
            side = Side(**{k: v for k, v in self.border.items() if v is not None})
            styles['border'] = Border(left=side, right=side, top=side, bottom=side)
        if self.alignment and openpyxl:
            styles['alignment'] = Alignment(**self.alignment)
        return styles


@dataclass
class TableRange:
    """Диапазон ячеек для операций"""
    sheet_name: str
    start_row: int
    end_row: int
    start_col: Union[int, str]
    end_col: Union[int, str]
    
    @property
    def a1_notation(self) -> str:
        """Возвращает диапазон в A1-нотации"""
        start_col_letter = get_column_letter(self.start_col) if isinstance(self.start_col, int) else self.start_col
        end_col_letter = get_column_letter(self.end_col) if isinstance(self.end_col, int) else self.end_col
        return f"{self.sheet_name}!{start_col_letter}{self.start_row}:{end_col_letter}{self.end_row}"


@dataclass
class ChartConfig:
    """Конфигурация для создания диаграмм"""
    chart_type: str
    title: str
    x_column: str
    y_columns: List[str]
    x_title: Optional[str] = None
    y_title: Optional[str] = None
    colors: Optional[List[str]] = None
    width: int = 800
    height: int = 400


# ============================================================================
# МЕНЕДЖЕР ДЛЯ РАБОТЫ С ТАБЛИЦАМИ
# ============================================================================
class TableManager:
    """
    Универсальный менеджер для работы с Google Sheets и Excel.
    
    Возможности:
    - Чтение/запись данных с выбором диапазона
    - Работа с несколькими листами
    - Применение форматирования через ИИ
    - Создание диаграмм и сводных таблиц
    - Умная очистка и трансформация данных
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализирует менеджер таблиц.
        
        Args:
            api_key: API ключ для ИИ-функций
        """
        self.api_key = api_key
        self._cache: Dict[str, pd.DataFrame] = {}
        self._last_operation: Optional[Dict] = None
        
    @handle_errors(default_return=None)
    def read_google_sheets(
        self, 
        url: str, 
        sheet_name: Optional[str] = None,
        range_a1: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Читает данные из Google Sheets.
        
        Args:
            url: URL Google таблицы или ID
            sheet_name: Имя листа (по умолчанию первый)
            range_a1: Диапазон в A1-нотации (опционально)
            use_cache: Использовать кэширование
            
        Returns:
            DataFrame с данными или None при ошибке
        """
        if '/d/' in url:
            sheet_id = url.split('/d/')[1].split('/')[0]
        else:
            sheet_id = url
            
        cache_key = f"gsheets:{sheet_id}:{sheet_name}:{range_a1}"
        
        if use_cache and cache_key in self._cache:
            logger.info(f"Возвращаю данные из кэша: {cache_key}")
            return self._cache[cache_key].copy()
        
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
        params = {'format': 'csv'}
        if sheet_name:
            params['gid'] = self._get_sheet_gid(url, sheet_name)
        if range_a1:
            params['range'] = range_a1
            
        response = requests.get(csv_url, params=params, timeout=CONFIG.API_TIMEOUT)
        response.raise_for_status()
        
        df = pd.read_csv(BytesIO(response.content))
        
        if use_cache:
            self._cache[cache_key] = df.copy()
            
        self._last_operation = {
            'type': 'read',
            'source': 'google_sheets',
            'rows': len(df),
            'columns': list(df.columns),
            'timestamp': datetime.now().isoformat()
        }
        
        return df
    
    def _get_sheet_gid(self, url: str, sheet_name: str) -> Optional[str]:
        """Получает GID листа по имени (упрощённая реализация)"""
        return None
    
    @handle_errors(default_return=None)
    def read_excel(
        self, 
        file_path: Union[str, BytesIO],
        sheet_name: Optional[Union[str, int]] = 0,
        range_a1: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Читает данные из Excel файла.
        
        Args:
            file_path: Путь к файлу или BytesIO объект
            sheet_name: Имя или индекс листа
            range_a1: Диапазон для чтения (поддерживается ограниченно)
            
        Returns:
            DataFrame с данными
        """
        if not EXCEL_SUPPORT:
            raise ImportError("Установите openpyxl: pip install openpyxl")
        
        cache_key = f"excel:{hash(str(file_path))}:{sheet_name}"
        
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        df = pd.read_excel(
            file_path, 
            sheet_name=sheet_name, 
            engine='openpyxl',
            **({'usecols': range_a1} if range_a1 else {})
        )
        
        if use_cache:
            self._cache[cache_key] = df.copy()
            
        self._last_operation = {
            'type': 'read',
            'source': 'excel',
            'rows': len(df),
            'columns': list(df.columns),
            'timestamp': datetime.now().isoformat()
        }
        
        return df
    
    @handle_errors(default_return=False)
    def write_excel(
        self,
        df: pd.DataFrame,
        output_path: str,
        sheet_name: str = 'Sheet1',
        apply_formatting: bool = True,
        formatting_rules: Optional[Dict] = None
    ) -> bool:
        """
        Записывает DataFrame в Excel с расширенным форматированием.
        
        Args:
            df: DataFrame для записи
            output_path: Путь для сохранения
            sheet_name: Имя листа
            apply_formatting: Применять авто-форматирование
            formatting_rules: Пользовательские правила форматирования
            
        Returns:
            True при успехе
        """
        if not EXCEL_SUPPORT:
            raise ImportError("Требуется openpyxl")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            if apply_formatting:
                self._apply_excel_formatting(writer, df, formatting_rules)
                
        return True
    
    def _apply_excel_formatting(
        self, 
        writer: pd.ExcelWriter, 
        df: pd.DataFrame,
        rules: Optional[Dict] = None
    ):
        """Применяет форматирование к листу Excel"""
        worksheet = writer.sheets[writer.sheet_names[0]]
        
        for column in worksheet.columns:
            max_length = max(
                (len(str(cell.value)) if cell.value else 0) 
                for cell in column
            )
            col_letter = column[0].column_letter
            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
        
        header_fill = PatternFill(start_color="667eea", end_color="764ba2", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        if rules:
            self._apply_custom_rules(worksheet, df, rules)
    
    def _apply_custom_rules(self, worksheet, df: pd.DataFrame, rules: Dict):
        """Применяет кастомные правила форматирования"""
        if rules.get('conditional_format'):
            for rule in rules['conditional_format']:
                col_name = rule.get('column')
                condition = rule.get('condition')
                format_config = rule.get('format', {})
                
                if col_name in df.columns:
                    col_idx = df.columns.get_loc(col_name) + 1
                    self._apply_conditional_format(
                        worksheet, col_idx, len(df) + 1, condition, format_config
                    )
    
    def _apply_conditional_format(self, worksheet, col_idx: int, max_row: int, 
                                  condition: str, format_config: Dict):
        """Применяет условное форматирование"""
        fill_color = format_config.get('color', 'FFEB3B')
        
        for row in range(2, max_row + 1):
            cell = worksheet.cell(row=row, column=col_idx)
            value = cell.value
            
            if condition == 'highlight_negatives' and isinstance(value, (int, float)) and value < 0:
                cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            elif condition == 'highlight_high' and isinstance(value, (int, float)) and value > 1000:
                cell.fill = PatternFill(start_color='90EE90', end_color='90EE90', fill_type="solid")
    
    @handle_errors(default_return=None)
    def create_chart_in_excel(
        self,
        file_path: str,
        chart_config: ChartConfig,
        sheet_name: str = 'Sheet1'
    ) -> bool:
        """
        Создаёт диаграмму в Excel файле.
        
        Args:
            file_path: Путь к файлу
            chart_config: Конфигурация диаграммы
            sheet_name: Имя листа
            
        Returns:
            True при успехе
        """
        if not EXCEL_SUPPORT:
            return False
        
        wb = openpyxl.load_workbook(file_path)
        ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
        
        chart = self._create_chart_object(chart_config)
        chart.title = chart_config.title
        
        self._configure_chart_data(chart, ws, chart_config)
        
        ws.add_chart(chart, "A1")
        wb.save(file_path)
        return True
    
    def _create_chart_object(self, config: ChartConfig):
        """Создаёт объект диаграммы openpyxl"""
        charts = {
            'bar': BarChart,
            'line': LineChart, 
            'pie': PieChart,
            'scatter': None
        }
        chart_class = charts.get(config.chart_type, BarChart)
        return chart_class() if chart_class else BarChart()
    
    def _configure_chart_data(self, chart, worksheet, config: ChartConfig):
        """Настраивает данные для диаграммы"""
        pass
    
    @cache_result()
    def ai_analyze_dataframe(
        self, 
        df: pd.DataFrame, 
        instruction: str, 
        api_key: str
    ) -> Dict[str, Any]:
        """
        Анализирует DataFrame через ИИ и возвращает рекомендации.
        
        Args:
            df: DataFrame для анализа
            instruction: Инструкция на естественном языке
            api_key: API ключ для ИИ
            
        Returns:
            Dict с результатами анализа и трансформациями
        """
        if not api_key:
            return {'error': 'API ключ не указан'}
        
        df_summary = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': {str(k): str(v) for k, v in df.dtypes.to_dict().items()},
            'sample': df.head(3).to_dict('records'),
            'null_counts': df.isnull().sum().to_dict(),
            'stats': df.describe(include='all').to_dict() if not df.empty else {}
        }
        
        client = OpenAI(api_key=api_key, base_url=CONFIG.DEEPSEEK_BASE_URL)
        
        prompt = f"""
Ты эксперт по анализу данных в Python pandas.

ДАННЫЕ:
{json.dumps(df_summary, ensure_ascii=False, default=str)[:8000]}

ЗАДАЧА: {instruction}

Верни ответ в формате JSON:
{{
    "analysis": "Краткий анализ данных на русском",
    "issues_found": ["список проблем"],
    "recommendations": ["список рекомендаций"],
    "transformations": [
        {{
            "type": "clean|filter|aggregate|pivot|format",
            "code": "pandas код для выполнения",
            "description": "что делает этот код"
        }}
    ],
    "ready_code": "полный готовый код для копирования"
}}

Отвечай ТОЛЬКО валидным JSON, без пояснений.
"""
        
        try:
            response = client.chat.completions.create(
                model=CONFIG.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Ты аналитик данных. Отвечай только валидным JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                timeout=CONFIG.API_TIMEOUT,
                max_tokens=CONFIG.MAX_TOKENS
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
            return {'error': 'Не удалось распарсить ответ ИИ'}
            
        except Exception as e:
            return {'error': f'Ошибка ИИ: {str(e)}'}
    
    def execute_transformation(
        self, 
        df: pd.DataFrame, 
        transformation_code: str
    ) -> pd.DataFrame:
        """
        Выполняет код трансформации над DataFrame.
        
        ⚠️ ВНИМАНИЕ: Используйте только с доверенным кодом!
        
        Args:
            df: Исходный DataFrame
            transformation_code: Код трансформации на Python
            
        Returns:
            Преобразованный DataFrame
        """
        safe_globals = {"pd": pd, "np": __import__('numpy') if 'numpy' in transformation_code else None, "df": df.copy()}
        
        try:
            exec(transformation_code, safe_globals, safe_globals)
            return safe_globals.get('df', df)
        except Exception as e:
            logger.error(f"Ошибка выполнения: {e}")
            raise


# ============================================================================
# КЛАСС ИИ АГЕНТА – ИСПРАВЛЕНО: БЕЗОПАСНАЯ ДЕСЕРИАЛИЗАЦИЯ
# ============================================================================
class AIAgent:
    """
    Класс для создания и обучения ИИ агентов.
    
    Атрибуты:
        id: Уникальный идентификатор агента
        name: Имя агента
        role: Роль/специализация агента
        system_prompt: Системный промпт для настройки поведения
        created_at: Дата создания
        training_examples: Примеры для обучения
        memory: Долговременная память агента
        conversation_history: История диалогов
        knowledge_base: База знаний
        stats: Статистика использования
    """
    
    def __init__(self, name: str, role: str, system_prompt: str, agent_id: Optional[str] = None):
        """
        Инициализирует нового ИИ агента.
        
        Args:
            name: Имя агента
            role: Роль/специализация
            system_prompt: Системный промпт
            agent_id: Опциональный внешний ID
        """
        self.id = agent_id or hashlib.md5(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.created_at = datetime.now().isoformat()
        self.training_examples: List[Dict] = []
        self.memory: List[Dict] = []
        self.conversation_history: List[Dict] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.stats: Dict[str, Any] = {
            'total_trainings': 0,
            'total_conversations': 0,
            'success_rate': 0.0,
            'last_trained': None,
            'last_used': None
        }
    
    def add_training_example(self, user_input: str, expected_output: str, context: str = "") -> Dict:
        """
        Добавляет пример для обучения агента.
        
        Args:
            user_input: Входной запрос пользователя
            expected_output: Ожидаемый ответ агента
            context: Дополнительный контекст
            
        Returns:
            Созданный пример обучения
        """
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
    
    def add_to_memory(self, key: str, value: Any, importance: str = "normal") -> Dict:
        """
        Добавляет факт в память агента.
        
        Args:
            key: Ключ для доступа к значению
            value: Значение для запоминания
            importance: Уровень важности (low/normal/high)
            
        Returns:
            Созданный элемент памяти
        """
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
        
        return memory_item
    
    def get_from_memory(self, key: str) -> Any:
        """
        Получает значение из памяти по ключу.
        
        Args:
            key: Ключ для поиска
            
        Returns:
            Значение из памяти или None
        """
        for mem in self.memory:
            if mem['key'] == key:
                mem['access_count'] += 1
                return mem['value']
        return None
    
    def add_conversation(self, user_message: str, agent_response: str, feedback: Optional[str] = None):
        """
        Добавляет диалог в историю.
        
        Args:
            user_message: Сообщение пользователя
            agent_response: Ответ агента
            feedback: Обратная связь (positive/negative)
        """
        conversation = {
            'user': user_message,
            'agent': agent_response,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat(),
            'context': self.get_context_summary()
        }
        self.conversation_history.append(conversation)
        self.stats['total_conversations'] += 1
        self.stats['last_used'] = datetime.now().isoformat()
        
        if feedback == 'positive':
            self.stats['success_rate'] = (
                self.stats['success_rate'] * (self.stats['total_conversations'] - 1) + 100
            ) / self.stats['total_conversations']
        elif feedback == 'negative':
            self.stats['success_rate'] = (
                self.stats['success_rate'] * (self.stats['total_conversations'] - 1)
            ) / self.stats['total_conversations']
    
    def get_context_summary(self) -> str:
        """Возвращает краткое резюме контекста агента"""
        return (
            f"Роль: {self.role}\n"
            f"Память: {len(self.memory)} фактов\n"
            f"Обучен на: {len(self.training_examples)} примерах\n"
            f"Диалогов: {self.stats['total_conversations']}"
        )
    
    def generate_response(
        self, 
        user_input: str, 
        api_key: str, 
        use_training: bool = True
    ) -> str:
        """
        Генерирует ответ агента на запрос пользователя.
        
        Args:
            user_input: Запрос пользователя
            api_key: API ключ DeepSeek
            use_training: Использовать ли примеры обучения
            
        Returns:
            Текст ответа агента
        """
        if not api_key:
            return "❌ API ключ не указан. Получите бесплатно на platform.deepseek.com"
        
        try:
            client = OpenAI(api_key=api_key, base_url=CONFIG.DEEPSEEK_BASE_URL)
            
            memory_context = ""
            if self.memory:
                memory_context = "\n\n🧠 ЗНАНИЯ АГЕНТА (из памяти):\n"
                for mem in self.memory[-5:]:
                    memory_context += f"- {mem['key']}: {mem['value']}\n"
            
            training_context = ""
            if use_training and self.training_examples:
                training_context = "\n\n📚 ПРИМЕРЫ ОБУЧЕНИЯ:\n"
                for ex in self.training_examples[-3:]:
                    training_context += f"Вопрос: {ex['user_input']}\nОтвет: {ex['expected_output']}\n\n"
            
            history_context = ""
            if self.conversation_history:
                history_context = "\n\n📜 ИСТОРИЯ ДИАЛОГОВ:\n"
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
Будь полезным, точным и дружелюбным. Отвечай на русском языке.
"""
            response = client.chat.completions.create(
                model=CONFIG.DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                timeout=CONFIG.API_TIMEOUT,
                max_tokens=CONFIG.MAX_TOKENS
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return f"⚠️ Ошибка: {str(e)}"
    
    def to_dict(self) -> Dict:
        """Сериализует агента в словарь"""
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
        """
        Десериализует агента из словаря.
        
        ✅ ИСПРАВЛЕНИЕ: безопасное извлечение с дефолтными значениями
        вместо прямого доступа data['key'] который вызывает KeyError
        """
        # ✅ ИСПРАВЛЕНИЕ: используем .get() с дефолтами вместо прямого доступа
        name = data.get('name', 'Безымянный агент')
        role = data.get('role', 'Универсальный помощник')
        system_prompt = data.get('system_prompt', 'Ты полезный ИИ-ассистент.')
        agent_id = data.get('id')
        
        agent = cls(name, role, system_prompt, agent_id)
        agent.created_at = data.get('created_at', datetime.now().isoformat())
        agent.training_examples = data.get('training_examples', [])
        agent.memory = data.get('memory', [])
        agent.conversation_history = data.get('conversation_history', [])
        agent.knowledge_base = data.get('knowledge_base', {})
        agent.stats = data.get('stats', {
            'total_trainings': len(agent.training_examples),
            'total_conversations': len(agent.conversation_history),
            'success_rate': 0.0,
            'last_trained': None,
            'last_used': None
        })
        return agent


# ============================================================================
# МЕНЕДЖЕР АГЕНТОВ – ИСПРАВЛЕНО: ВАЛИДАЦИЯ ПРИ ЗАГРУЗКЕ
# ============================================================================
class AgentManager:
    """Управляет коллекцией ИИ агентов"""
    
    def __init__(self):
        """Инициализирует менеджер агентов"""
        self.agents: Dict[str, AIAgent] = {}
        self.current_agent_id: Optional[str] = None
        self.load_agents()
    
    def load_agents(self):
        """
        Загружает агентов из session_state.
        
        ✅ ИСПРАВЛЕНИЕ: валидация данных перед загрузкой для предотвращения
        ошибки KeyError: 'role' при импорте/загрузке битых данных
        """
        if 'agents' not in st.session_state:
            default_agents = self._create_default_agents()
            st.session_state.agents = {agent.id: agent.to_dict() for agent in default_agents}
            st.session_state.current_agent_id = default_agents[0].id if default_agents else None
        
        # ✅ ИСПРАВЛЕНИЕ: безопасная загрузка с проверкой структуры данных
        for agent_id, agent_dict in dict(st.session_state.agents).items():
            if isinstance(agent_dict, dict) and 'name' in agent_dict:
                try:
                    self.agents[agent_id] = AIAgent.from_dict(agent_dict)
                except Exception as e:
                    logger.warning(f"⚠️ Пропущен битый агент {agent_id}: {e}")
                    continue
        
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
        """Сохраняет агентов в session_state"""
        st.session_state.agents = {agent_id: agent.to_dict() for agent_id, agent in self.agents.items()}
        st.session_state.current_agent_id = self.current_agent_id
    
    def add_agent(self, name: str, role: str, system_prompt: str) -> AIAgent:
        """
        Создаёт и добавляет нового агента.
        
        Args:
            name: Имя агента
            role: Роль агента
            system_prompt: Системный промпт
            
        Returns:
            Созданный агент
        """
        agent = AIAgent(name, role, system_prompt)
        self.agents[agent.id] = agent
        self.save_agents()
        return agent
    
    def delete_agent(self, agent_id: str):
        """Удаляет агента по ID"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            if self.current_agent_id == agent_id:
                self.current_agent_id = next(iter(self.agents.keys())) if self.agents else None
            self.save_agents()
    
    def get_current_agent(self) -> Optional[AIAgent]:
        """Возвращает текущего выбранного агента"""
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
        """Экспортирует агента в JSON"""
        if agent_id in self.agents:
            return json.dumps(self.agents[agent_id].to_dict(), ensure_ascii=False, indent=2)
        return ""
    
    def import_agent(self, agent_json: str) -> bool:
        """
        Импортирует агента из JSON.
        
        Args:
            agent_json: JSON строка с данными агента
            
        Returns:
            True при успешном импорте
        """
        try:
            data = json.loads(agent_json)
            # ✅ ИСПРАВЛЕНИЕ: валидация структуры данных перед загрузкой
            if not isinstance(data, dict):
                raise ValueError("JSON должен быть объектом")
            if 'name' not in data:
                raise ValueError("Отсутствует обязательное поле 'name'")
            
            agent = AIAgent.from_dict(data)
            self.agents[agent.id] = agent
            self.save_agents()
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            st.error(f"❌ Неверный формат JSON: {str(e)}")
            return False
        except ValueError as e:
            logger.error(f"Ошибка валидации: {e}")
            st.error(f"❌ {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Ошибка импорта агента: {e}")
            st.error(f"❌ Ошибка импорта: {str(e)}")
            return False


# ============================================================================
# ГЕНЕРАТОР WORKFLOW ЧЕРЕЗ ИИ
# ============================================================================
class AIWorkflowGenerator:
    """Генерирует workflow из текстового описания на русском"""
    
    @staticmethod
    def generate(description: str, api_key: str) -> List[Dict]:
        """
        Генерирует workflow из описания.
        
        Args:
            description: Описание workflow на русском
            api_key: API ключ DeepSeek
            
        Returns:
            Список узлов workflow
        """
        if not api_key:
            return []
        
        try:
            client = OpenAI(api_key=api_key, base_url=CONFIG.DEEPSEEK_BASE_URL)
            
            prompt = f"""
Ты эксперт по созданию workflow автоматизации. На основе описания пользователя создай JSON workflow.

Описание пользователя: "{description}"

Правила:
1. Workflow - это массив блоков (nodes)
2. Каждый блок имеет: name (название), type (тип), config (настройки)
3. Доступные типы блоков:
   - google_sheets_read: чтение из Google таблиц (config: sheet_url)
   - google_sheets_write: запись в Google таблицы
   - excel_read: чтение Excel файла
   - excel_write: запись в Excel
   - deepseek: AI анализ (config: system_prompt, user_prompt)
   - http_get: GET запрос к API (config: url)
   - http_post: POST запрос (config: url, body)
   - condition: условие (config: condition на русском)
   - loop: цикл (config: items)
   - email: отправка email (config: to, subject, body)
   - telegram: отправка в Telegram (config: chat_id, message)
   - ai_agent: вызов ИИ агента (config: agent_id, question)
   - data_clean: очистка данных (config: rules)
   - pivot_table: сводная таблица (config: index, columns, values)

4. Условия пиши на РУССКОМ языке, используя природные фразы

Верни ТОЛЬКО JSON массив блоков, без пояснений.
"""
            response = client.chat.completions.create(
                model=CONFIG.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Ты генератор workflow автоматизации. Возвращай только JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                timeout=CONFIG.API_TIMEOUT,
                max_tokens=CONFIG.MAX_TOKENS
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                return json.loads(json_match.group())
            else:
                return []
                
        except Exception as e:
            logger.error(f"Ошибка генерации workflow: {e}")
            st.error(f"Ошибка генерации: {str(e)}")
            return []


# ============================================================================
# ИСПОЛНИТЕЛЬ WORKFLOW
# ============================================================================
class WorkflowExecutor:
    """Выполняет workflow с поддержкой условий на русском"""
    
    def __init__(
        self, 
        workflow: List[Dict], 
        api_key: Optional[str] = None, 
        agent_manager: Optional[AgentManager] = None,
        table_manager: Optional[TableManager] = None
    ):
        """
        Инициализирует исполнитель workflow.
        
        Args:
            workflow: Список узлов workflow
            api_key: API ключ для ИИ
            agent_manager: Менеджер агентов
            table_manager: Менеджер таблиц
        """
        self.workflow = workflow
        self.api_key = api_key
        self.agent_manager = agent_manager
        self.table_manager = table_manager or TableManager(api_key)
        self.context: Dict[str, Any] = {}
        self.results: List[Dict] = []
        self.current_node_index: int = 0
        self.start_time: Optional[float] = None
    
    def execute(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Выполняет весь workflow.
        
        Args:
            progress_callback: Функция для обновления прогресса
            
        Returns:
            Результат выполнения
        """
        self.start_time = time.time()
        
        while self.current_node_index < len(self.workflow):
            node = self.workflow[self.current_node_index]
            
            if progress_callback:
                progress_callback(self.current_node_index, node)
            
            try:
                result = self._execute_node(node)
                self.results.append({
                    'node': node.get('name'),
                    'type': node.get('type'),
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
                if isinstance(result, dict) and 'data' in result:
                    self.context.update(result)
                
                node['status'] = WorkflowStatus.SUCCESS.value
                self.current_node_index += 1
                
            except Exception as e:
                logger.error(f"Ошибка в узле {node.get('name')}: {e}")
                node['status'] = WorkflowStatus.ERROR.value
                node['error'] = str(e)
                return {
                    'success': False,
                    'error': str(e),
                    'error_node': node.get('name'),
                    'results': self.results,
                    'execution_time': time.time() - (self.start_time or time.time())
                }
        
        return {
            'success': True,
            'results': self.results,
            'context': self.context,
            'execution_time': time.time() - (self.start_time or time.time())
        }
    
    def _execute_node(self, node: Dict) -> Any:
        """Выполняет отдельный узел"""
        node_type = node.get('type')
        config = node.get('config', {})
        
        executors = {
            NodeType.GOOGLE_SHEETS_READ.value: lambda: self._execute_google_sheets_read(config),
            NodeType.GOOGLE_SHEETS_WRITE.value: lambda: self._execute_google_sheets_write(config),
            NodeType.EXCEL_READ.value: lambda: self._execute_excel_read(config),
            NodeType.EXCEL_WRITE.value: lambda: self._execute_excel_write(config),
            NodeType.DEEPSEEK_AI.value: lambda: self._execute_deepseek(config),
            NodeType.CONDITION.value: lambda: self._execute_condition(config),
            NodeType.LOOP.value: lambda: self._execute_loop(config),
            NodeType.HTTP_GET.value: lambda: self._execute_http_get(config),
            NodeType.HTTP_POST.value: lambda: self._execute_http_post(config),
            NodeType.EMAIL.value: lambda: self._execute_email(config),
            NodeType.TELEGRAM.value: lambda: self._execute_telegram(config),
            NodeType.AI_AGENT.value: lambda: self._execute_ai_agent(config),
            NodeType.DATA_CLEAN.value: lambda: self._execute_data_clean(config),
            NodeType.PIVOT_TABLE.value: lambda: self._execute_pivot_table(config),
        }
        
        executor = executors.get(node_type)
        if executor:
            return executor()
        else:
            return {'status': 'unknown_type', 'type': node_type}
    
    def _execute_google_sheets_read(self, config: Dict) -> Dict:
        """Чтение из Google Sheets"""
        sheet_url = config.get('sheet_url', '')
        sheet_name = config.get('sheet_name')
        range_a1 = config.get('range_a1')
        
        if not sheet_url:
            return {'error': 'URL Google Sheets не указан'}
        
        try:
            df = self.table_manager.read_google_sheets(sheet_url, sheet_name, range_a1)
            if df is None:
                return {'error': 'Не удалось загрузить данные'}
            
            return {
                'data': df.to_dict('records'),
                'rows': len(df),
                'columns': list(df.columns),
                'df': df
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_google_sheets_write(self, config: Dict) -> Dict:
        """Запись в Google Sheets (заглушка)"""
        return {'status': 'not_implemented', 'message': 'Требуется настройка Google Sheets API'}
    
    def _execute_excel_read(self, config: Dict) -> Dict:
        """Чтение из Excel"""
        file_path = config.get('file_path', '')
        sheet_name = config.get('sheet_name', 0)
        
        if not file_path:
            return {'error': 'Путь к файлу не указан'}
        
        try:
            df = self.table_manager.read_excel(file_path, sheet_name)
            if df is None:
                return {'error': 'Не удалось загрузить данные'}
            
            return {
                'data': df.to_dict('records'),
                'rows': len(df),
                'columns': list(df.columns),
                'df': df
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_excel_write(self, config: Dict) -> Dict:
        """Запись в Excel"""
        df = config.get('df')
        output_path = config.get('output_path', 'output.xlsx')
        apply_formatting = config.get('apply_formatting', True)
        
        if df is None:
            return {'error': 'DataFrame не указан'}
        
        try:
            success = self.table_manager.write_excel(df, output_path, apply_formatting=apply_formatting)
            return {'status': 'success' if success else 'failed', 'path': output_path}
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_deepseek(self, config: Dict) -> Dict:
        """Вызов DeepSeek AI"""
        if not self.api_key:
            return {'error': 'API ключ не указан'}
        
        try:
            client = OpenAI(api_key=self.api_key, base_url=CONFIG.DEEPSEEK_BASE_URL)
            user_prompt = config.get('user_prompt', '')
            
            # Подстановка переменных из контекста
            for key, value in self.context.items():
                if isinstance(value, str):
                    user_prompt = user_prompt.replace(f"{{{{{key}}}}}", value)
            
            response = client.chat.completions.create(
                model=CONFIG.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": config.get('system_prompt', 'Ты полезный ассистент')},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=float(config.get('temperature', 0.3)),
                timeout=CONFIG.API_TIMEOUT,
                max_tokens=CONFIG.MAX_TOKENS
            )
            return {
                'response': response.choices[0].message.content,
                'model': CONFIG.DEEPSEEK_MODEL
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_condition(self, config: Dict) -> Dict:
        """Выполнение условия"""
        condition_text = config.get('condition', '')
        parsed = RussianConditionParser.parse(condition_text)
        result = self._evaluate_condition(condition_text)
        
        return {
            'condition': condition_text,
            'result': result,
            'parsed': parsed,
            'code': parsed.get('code')
        }
    
    def _evaluate_condition(self, condition_text: str) -> bool:
        """Оценивает условие"""
        condition_text = condition_text.lower()
        
        # Простые эвристики для демонстрации
        if 'больше' in condition_text:
            match = re.search(r'(\w+)\s+больше\s+(\d+)', condition_text)
            if match:
                var_name = match.group(1)
                value = float(match.group(2))
                context_value = self.context.get(var_name, 0)
                return float(context_value) > value if isinstance(context_value, (int, float)) else False
        
        elif 'меньше' in condition_text:
            match = re.search(r'(\w+)\s+меньше\s+(\d+)', condition_text)
            if match:
                var_name = match.group(1)
                value = float(match.group(2))
                context_value = self.context.get(var_name, 0)
                return float(context_value) < value if isinstance(context_value, (int, float)) else False
        
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
        """Выполнение цикла"""
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
        """HTTP GET запрос"""
        url = config.get('url', '')
        if not url:
            return {'error': 'URL не указан'}
        
        try:
            response = requests.get(url, timeout=CONFIG.API_TIMEOUT)
            return {
                'status': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'url': url
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_http_post(self, config: Dict) -> Dict:
        """HTTP POST запрос"""
        url = config.get('url', '')
        if not url:
            return {'error': 'URL не указан'}
        
        try:
            body = config.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
            response = requests.post(url, json=body, timeout=CONFIG.API_TIMEOUT)
            return {
                'status': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'url': url
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_email(self, config: Dict) -> Dict:
        """Подготовка email (заглушка)"""
        return {
            'to': config.get('to', ''),
            'subject': config.get('subject', ''),
            'body': config.get('body', ''),
            'status': 'ready'
        }
    
    def _execute_telegram(self, config: Dict) -> Dict:
        """Подготовка Telegram сообщения (заглушка)"""
        return {
            'chat_id': config.get('chat_id', ''),
            'message': config.get('message', ''),
            'status': 'ready'
        }
    
    def _execute_ai_agent(self, config: Dict) -> Dict:
        """Вызов ИИ агента"""
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
    
    def _execute_data_clean(self, config: Dict) -> Dict:
        """Очистка данных"""
        df = config.get('df')
        rules = config.get('rules', {})
        
        if df is None:
            return {'error': 'DataFrame не указан'}
        
        try:
            cleaned_df = df.copy()
            
            if rules.get('remove_duplicates'):
                cleaned_df = cleaned_df.drop_duplicates()
            
            if rules.get('remove_empty'):
                cleaned_df = cleaned_df.dropna(how='all')
            
            if rules.get('fill_na'):
                fill_value = rules.get('fill_value', '')
                cleaned_df = cleaned_df.fillna(fill_value)
            
            if rules.get('columns'):
                cleaned_df = cleaned_df[rules['columns']]
            
            return {
                'data': cleaned_df.to_dict('records'),
                'rows': len(cleaned_df),
                'columns': list(cleaned_df.columns),
                'df': cleaned_df,
                'removed_rows': len(df) - len(cleaned_df)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_pivot_table(self, config: Dict) -> Dict:
        """Создание сводной таблицы"""
        df = config.get('df')
        index = config.get('index', [])
        columns = config.get('columns', [])
        values = config.get('values', [])
        aggfunc = config.get('aggfunc', 'sum')
        
        if df is None:
            return {'error': 'DataFrame не указан'}
        
        try:
            pivot = pd.pivot_table(
                df, 
                index=index if isinstance(index, list) else [index],
                columns=columns if isinstance(columns, list) else [columns] if columns else None,
                values=values if isinstance(values, list) else [values] if values else None,
                aggfunc=aggfunc,
                fill_value=0
            )
            
            return {
                'data': pivot.to_dict(),
                'df': pivot.reset_index(),
                'type': 'pivot_table'
            }
        except Exception as e:
            return {'error': str(e)}


# ============================================================================
# ГОЛОСОВЫЕ ФУНКЦИИ
# ============================================================================
def recognize_speech_from_audio(audio_bytes: bytes) -> Optional[str]:
    """
    Распознавание русской речи из аудиобайтов.
    
    Args:
        audio_bytes: Аудиоданные в формате WAV/MP3
        
    Returns:
        Распознанный текст или None
    """
    if not VOICE_SUPPORT or sr is None:
        return None
    
    recognizer = sr.Recognizer()
    try:
        audio_file = BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="ru-RU")
    except Exception as e:
        logger.warning(f"Ошибка распознавания речи: {e}")
        return None


def text_to_speech_mp3(text: str) -> Optional[bytes]:
    """
    Генерация MP3 из текста (русский язык).
    
    Args:
        text: Текст для озвучки
        
    Returns:
        Байты MP3 файла или None
    """
    if not VOICE_SUPPORT or gTTS is None:
        return None
    
    try:
        tts = gTTS(text=text, lang="ru", slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        logger.warning(f"Ошибка синтеза речи: {e}")
        return None


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ STREAMLIT
# ============================================================================
def initialize_session_state():
    """Инициализирует session_state"""
    defaults = {
        'agent_manager': None,
        'workflow': [],
        'agent_messages': [],
        'history': [],
        'analytics': {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0
        },
        'voice_show_upload': False,
        'table_manager': None,
        'current_df': None,
        'excel_loaded': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """Точка входа приложения"""
    # Настройка страницы
    st.set_page_config(
        page_title=CONFIG.APP_TITLE,
        page_icon=CONFIG.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Применение стилей
    st.markdown(get_app_styles(), unsafe_allow_html=True)
    
    # Инициализация сессии
    initialize_session_state()
    
    # Заголовок
    st.markdown(f"""
    <div class="main-header">
        <h1>{CONFIG.APP_ICON} WORKFLOW BUILDER PRO v{CONFIG.APP_VERSION}</h1>
        <p>Обучаемые ИИ агенты | Таблицы | Голос | Мобильная версия</p>
        <span class="version-badge">Монопоточная версия • {datetime.now().strftime('%Y')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Боковая панель
    with st.sidebar:
        st.markdown("## 🧠 МОИ ИИ АГЕНТЫ")
        
        api_key = st.text_input(
            "🔑 DeepSeek API Ключ",
            type="password",
            help="Получите бесплатно на platform.deepseek.com",
            key="api_key_main"
        )
        
        st.markdown("---")
        
        # Менеджер агентов
        if st.session_state.agent_manager is None:
            st.session_state.agent_manager = AgentManager()
        
        agent_manager = st.session_state.agent_manager
        
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
        
        # Создание агента
        with st.expander("➕ СОЗДАТЬ АГЕНТА", expanded=False):
            new_name = st.text_input("Имя", placeholder="Мой Помощник", key="new_agent_name")
            new_role = st.text_input("Роль", placeholder="эксперт по...", key="new_agent_role")
            new_prompt = st.text_area("Промпт", height=80, key="new_agent_prompt")
            
            if st.button("✨ Создать", use_container_width=True, key="create_agent_btn"):
                if new_name and new_role and new_prompt:
                    agent_manager.add_agent(new_name, new_role, new_prompt)
                    st.success(f"✅ Агент {new_name} создан!")
                    st.rerun()
                else:
                    st.warning("Заполните все поля")
        
        st.markdown("---")
        
        # Экспорт/Импорт
        with st.expander("🔄 ЭКСПОРТ/ИМПОРТ", expanded=False):
            current = agent_manager.get_current_agent()
            if current:
                export_json = agent_manager.export_agent(current.id)
                st.download_button(
                    label=f"📤 Экспорт",
                    data=export_json,
                    file_name=f"agent_{current.name}.json",
                    mime="application/json"
                )
            
            import_file = st.file_uploader("Импорт", type=['json'], key="import_agent_file")
            if import_file:
                content = import_file.read().decode('utf-8')
                if agent_manager.import_agent(content):
                    st.success("✅ Агент импортирован!")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("## 📊 СТАТИСТИКА")
        st.metric("Агентов", len(agent_manager.agents))
        
        current_agent = agent_manager.get_current_agent()
        if current_agent:
            st.metric("Обучений", current_agent.stats['total_trainings'])
            st.metric("Диалогов", current_agent.stats['total_conversations'])
        
        st.markdown("---")
        
        if st.button("🗑️ Очистить workflow", use_container_width=True):
            st.session_state.workflow = []
            st.rerun()
    
    # Менеджер таблиц
    if st.session_state.table_manager is None:
        st.session_state.table_manager = TableManager(api_key)
    
    # Основные вкладки
    tabs = st.tabs([
        "💬 Диалог", "📚 Обучение", "🧠 Память", "📊 Аналитика",
        "🤖 Workflow", "🔀 Условия", "🗂 Таблицы+ИИ", "📖 Справка"
    ])
    
    # Вкладка 1: Диалог
    with tabs[0]:
        render_chat_tab(agent_manager, api_key)
    
    # Вкладка 2: Обучение
    with tabs[1]:
        render_training_tab(agent_manager)
    
    # Вкладка 3: Память
    with tabs[2]:
        render_memory_tab(agent_manager)
    
    # Вкладка 4: Аналитика
    with tabs[3]:
        render_analytics_tab(agent_manager)
    
    # Вкладка 5: Workflow
    with tabs[4]:
        render_workflow_tab(agent_manager, api_key)
    
    # Вкладка 6: Условия
    with tabs[5]:
        render_conditions_tab()
    
    # Вкладка 7: Таблицы + ИИ
    with tabs[6]:
        render_tables_tab(api_key)
    
    # Вкладка 8: Справка
    with tabs[7]:
        render_help_tab()


def render_chat_tab(agent_manager: AgentManager, api_key: str):
    """Рендерит вкладку диалога с агентом"""
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Выберите агента в боковой панели")
        return
    
    st.subheader(f"💬 {current_agent.name}")
    st.caption(f"Роль: {current_agent.role}")
    
    # История сообщений
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.agent_messages:
            if msg['role'] == 'user':
                st.markdown(f"**👤 Вы:** {msg['content']}")
            else:
                st.markdown(f"**🤖 {current_agent.name}:** {msg['content']}")
            st.markdown("---")
    
    # Ввод
    user_input = st.text_area("✏️ Сообщение", height=80, key="chat_input")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        use_training = st.checkbox("Обучение", value=True, key="chat_use_training")
    with col2:
        if VOICE_SUPPORT and st.button("🎤 Голос", use_container_width=True):
            st.session_state.voice_show_upload = True
    with col3:
        if st.button("🚀 Отправить", type="primary", use_container_width=True):
            if user_input:
                st.session_state.agent_messages.append({'role': 'user', 'content': user_input})
                
                with st.spinner("Думает..."):
                    response = current_agent.generate_response(user_input, api_key, use_training)
                
                st.session_state.agent_messages.append({'role': 'agent', 'content': response})
                current_agent.add_conversation(user_input, response)
                agent_manager.save_agents()
                st.rerun()
    
    # Загрузка аудио
    if st.session_state.voice_show_upload:
        st.info("🎤 Загрузите аудио (WAV/MP3)")
        audio_file = st.file_uploader("Файл", type=["wav", "mp3"], key="voice_upload")
        if audio_file:
            recognized = recognize_speech_from_audio(audio_file.read())
            if recognized:
                st.success(f"✅ {recognized}")
                st.session_state.chat_input = recognized
                st.session_state.voice_show_upload = False
                st.rerun()
            else:
                st.error("❌ Не распознано")
    
    # Озвучка
    if st.button("🔊 Озвучить", use_container_width=True):
        if st.session_state.agent_messages and st.session_state.agent_messages[-1]['role'] == 'agent':
            audio = text_to_speech_mp3(st.session_state.agent_messages[-1]['content'])
            if audio:
                st.audio(audio, format="audio/mp3")
    
    if st.button("🗑️ Очистить"):
        st.session_state.agent_messages = []
        st.rerun()


def render_training_tab(agent_manager: AgentManager):
    """Рендерит вкладку обучения"""
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Выберите агента")
        return
    
    st.subheader(f"📚 Обучение: {current_agent.name}")
    
    with st.expander("➕ Добавить пример", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            ex_input = st.text_area("Вопрос", height=80, key="train_input")
        with col2:
            ex_output = st.text_area("Ответ", height=80, key="train_output")
        ex_context = st.text_input("Контекст", key="train_context")
        
        if st.button("✨ Добавить", type="primary"):
            if ex_input and ex_output:
                current_agent.add_training_example(ex_input, ex_output, ex_context)
                agent_manager.save_agents()
                st.success("✅ Пример добавлен!")
                st.rerun()
    
    st.markdown(f"### Примеры ({len(current_agent.training_examples)})")
    for i, ex in enumerate(reversed(current_agent.training_examples[-10:])):
        with st.expander(f"#{ex['id']}: {ex['user_input'][:50]}..."):
            st.markdown(f"**Ответ:** {ex['expected_output']}")
            st.caption(f"📅 {ex['timestamp'][:10]}")
            if st.button(f"🗑️ Удалить", key=f"del_ex_{ex['id']}"):
                current_agent.training_examples = [e for e in current_agent.training_examples if e['id'] != ex['id']]
                agent_manager.save_agents()
                st.rerun()


def render_memory_tab(agent_manager: AgentManager):
    """Рендерит вкладку памяти"""
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Выберите агента")
        return
    
    st.subheader(f"🧠 Память: {current_agent.name}")
    
    with st.expander("➕ Добавить факт", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            mem_key = st.text_input("Ключ", key="mem_key")
        with col2:
            mem_value = st.text_input("Значение", key="mem_value")
        importance = st.selectbox("Важность", ["low", "normal", "high"], key="mem_importance")
        
        if st.button("💾 Сохранить"):
            if mem_key and mem_value:
                current_agent.add_to_memory(mem_key, mem_value, importance)
                agent_manager.save_agents()
                st.success("✅ Запомнено!")
                st.rerun()
    
    st.markdown(f"### Факты ({len(current_agent.memory)})")
    for mem in current_agent.memory:
        icon = "🔴" if mem['importance'] == 'high' else "🟡" if mem['importance'] == 'normal' else "🟢"
        st.markdown(f"""
        <div class="memory-box">
            {icon} **{mem['key']}** = {mem['value']}<br>
            <small>👁️ {mem['access_count']} | 📅 {mem['timestamp'][:10]}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🗑️", key=f"del_mem_{mem['key']}"):
            current_agent.memory = [m for m in current_agent.memory if m['key'] != mem['key']]
            agent_manager.save_agents()
            st.rerun()
    
    if st.button("🗑️ Очистить память"):
        current_agent.memory = []
        agent_manager.save_agents()
        st.success("Память очищена")
        st.rerun()


def render_analytics_tab(agent_manager: AgentManager):
    """Рендерит вкладку аналитики"""
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Выберите агента")
        return
    
    st.subheader(f"📊 {current_agent.name}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-card"><h3>{current_agent.stats["total_trainings"]}</h3><p>Обучений</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><h3>{current_agent.stats["total_conversations"]}</h3><p>Диалогов</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><h3>{current_agent.stats["success_rate"]:.0f}%</h3><p>Успешность</p></div>', unsafe_allow_html=True)
    with col4:
        total = len(current_agent.training_examples) + len(current_agent.memory)
        st.markdown(f'<div class="stat-card"><h3>{total}</h3><p>Фактов</p></div>', unsafe_allow_html=True)
    
    if current_agent.training_examples:
        st.subheader("📈 Прогресс")
        df = pd.DataFrame([
            {'Дата': ex['timestamp'][:10], 'Пример': i+1} 
            for i, ex in enumerate(current_agent.training_examples)
        ])
        fig = px.line(df, x='Дата', y='Пример', title="Накопление примеров")
        st.plotly_chart(fig, use_container_width=True)
    
    if current_agent.conversation_history:
        st.subheader("💬 История")
        for conv in current_agent.conversation_history[-5:]:
            with st.expander(f"{conv['timestamp'][:19]}"):
                st.markdown(f"**👤** {conv['user'][:200]}")
                st.markdown(f"**🤖** {conv['agent'][:200]}")


def render_workflow_tab(agent_manager: AgentManager, api_key: str):
    """Рендерит вкладку workflow"""
    st.subheader("🤖 Конструктор Workflow")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📦 Блоки")
        
        blocks = [
            ("📖 Google Sheets", NodeType.GOOGLE_SHEETS_READ.value),
            ("📗 Excel", NodeType.EXCEL_READ.value),
            ("🧠 DeepSeek AI", NodeType.DEEPSEEK_AI.value),
            ("🔀 Условие", NodeType.CONDITION.value),
            ("🔄 Цикл", NodeType.LOOP.value),
            ("📧 Email", NodeType.EMAIL.value),
            ("📱 Telegram", NodeType.TELEGRAM.value),
            ("🧠 ИИ Агент", NodeType.AI_AGENT.value),
            ("🧹 Очистка", NodeType.DATA_CLEAN.value),
            ("📊 Сводная", NodeType.PIVOT_TABLE.value),
        ]
        
        for name, btype in blocks:
            if st.button(f"{name}", key=f"add_{btype}", use_container_width=True):
                st.session_state.workflow.append({
                    "id": len(st.session_state.workflow),
                    "name": name,
                    "type": btype,
                    "config": {},
                    "status": WorkflowStatus.PENDING.value
                })
                st.rerun()
        
        st.markdown("### 🧠 Агенты")
        for agent in agent_manager.agents.values():
            if st.button(f"🧠 {agent.name}", key=f"wf_agent_{agent.id}", use_container_width=True):
                st.session_state.workflow.append({
                    "id": len(st.session_state.workflow),
                    "name": f"Агент: {agent.name}",
                    "type": NodeType.AI_AGENT.value,
                    "agent_id": agent.id,
                    "config": {"question": "", "use_training": True},
                    "status": WorkflowStatus.PENDING.value
                })
                st.rerun()
    
    with col2:
        st.markdown("### 📋 Workflow")
        
        if not st.session_state.workflow:
            st.info("💡 Добавьте блоки слева")
            return
        
        for i, block in enumerate(st.session_state.workflow):
            status_cls = ""
            if block.get('status') == WorkflowStatus.SUCCESS.value:
                status_cls = "workflow-node-success"
            elif block.get('status') == WorkflowStatus.ERROR.value:
                status_cls = "workflow-node-error"
            
            st.markdown(f"""
            <div class="workflow-node {status_cls}">
                <b>{block.get('name')}</b> <small>#{i+1}</small><br>
                <small>{block.get('type')}</small>
            </div>
            """, unsafe_allow_html=True)
            
            if i < len(st.session_state.workflow) - 1:
                st.markdown('<div class="workflow-connector">▼</div>', unsafe_allow_html=True)
            
            with st.expander(f"⚙️ {block.get('name')}"):
                cfg = block.get('config', {})
                
                if block['type'] == NodeType.GOOGLE_SHEETS_READ.value:
                    cfg['sheet_url'] = st.text_input("URL", cfg.get('sheet_url', ''), key=f"gs_url_{i}")
                    cfg['sheet_name'] = st.text_input("Лист", cfg.get('sheet_name', ''), key=f"gs_sheet_{i}")
                
                elif block['type'] == NodeType.EXCEL_READ.value:
                    cfg['file_path'] = st.text_input("Путь", cfg.get('file_path', ''), key=f"ex_path_{i}")
                
                elif block['type'] == NodeType.DEEPSEEK_AI.value:
                    cfg['system_prompt'] = st.text_area("Системный", cfg.get('system_prompt', ''), height=60, key=f"ai_sys_{i}")
                    cfg['user_prompt'] = st.text_area("Запрос", cfg.get('user_prompt', ''), height=60, key=f"ai_user_{i}")
                
                elif block['type'] == NodeType.CONDITION.value:
                    cfg['condition'] = st.text_area("Условие", cfg.get('condition', ''), height=60, key=f"cond_{i}")
                    if cfg.get('condition'):
                        parsed = RussianConditionParser.parse(cfg['condition'])
                        if parsed.get('code'):
                            st.code(parsed['code'], language='python')
                
                elif block['type'] == NodeType.AI_AGENT.value:
                    agent = agent_manager.agents.get(block.get('agent_id'))
                    if agent:
                        st.info(f"🧠 {agent.name}")
                        cfg['question'] = st.text_area("Вопрос", cfg.get('question', ''), height=60, key=f"agent_q_{i}")
                
                elif block['type'] == NodeType.DATA_CLEAN.value:
                    cfg['remove_duplicates'] = st.checkbox("Удалить дубли", cfg.get('remove_duplicates', True), key=f"clean_dup_{i}")
                    cfg['remove_empty'] = st.checkbox("Удалить пустые", cfg.get('remove_empty', True), key=f"clean_empty_{i}")
                
                block['config'] = cfg
                
                if st.button(f"🗑️ Удалить", key=f"del_wf_{i}"):
                    st.session_state.workflow.pop(i)
                    st.rerun()
        
        st.markdown("---")
        
        if st.button("🚀 ЗАПУСТИТЬ", type="primary", use_container_width=True):
            progress = st.progress(0)
            status = st.empty()
            
            def update_progress(idx, node):
                progress.progress((idx + 1) / len(st.session_state.workflow))
                status.text(f"🔄 {node.get('name')}")
            
            executor = WorkflowExecutor(
                st.session_state.workflow, 
                api_key, 
                agent_manager,
                st.session_state.table_manager
            )
            result = executor.execute(update_progress)
            
            progress.progress(1.0)
            
            if result['success']:
                st.balloons()
                st.success(f"✅ Успешно за {result['execution_time']:.1f}с")
                
                with st.expander("📋 Результаты", expanded=True):
                    for res in result['results']:
                        st.markdown(f"**📌 {res['node']}**")
                        st.json({k: v for k, v in res['result'].items() if k != 'df'})
            else:
                st.error(f"❌ Ошибка: {result.get('error')}")


def render_conditions_tab():
    """Рендерит вкладку условий"""
    st.subheader("🔀 Русские условия")
    
    st.markdown("""
    <div class="info-box">
    <b>Примеры:</b><br>
    • если цена больше 1000 то отправить уведомление<br>
    • если статус равно 'успех' иначе отправить ошибку<br>
    • если количество меньше 5 то пополнить склад
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Примеры")
        for ex in RussianConditionParser.EXAMPLES:
            st.code(f"📌 {ex}")
    
    with col2:
        st.markdown("### 🔧 Проверка")
        test_cond = st.text_area("Введите условие", height=100, key="test_condition")
        
        if test_cond:
            parsed = RussianConditionParser.parse(test_cond)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Тип", parsed.get('type'))
            with col_b:
                st.metric("Уверенность", f"{parsed.get('confidence', 0)*100:.0f}%")
            
            if parsed.get('code'):
                st.success(f"💻 `{parsed['code']}`")
            else:
                st.warning("⚠️ Не распознано")
    
    st.markdown("---")
    st.markdown("""
    | Оператор | Пример |
    |----------|--------|
    | больше, > | цена больше 1000 |
    | меньше, < | количество < 5 |
    | равно, == | статус равно 'ок' |
    | содержит | текст содержит 'срочно' |
    | между | сумма между 100 и 500 |
    """)


def render_tables_tab(api_key: str):
    """Рендерит вкладку таблиц с ИИ"""
    st.subheader("🗂 Таблицы + ИИ")
    
    if not EXCEL_SUPPORT:
        st.warning("⚠️ Установите openpyxl: `pip install openpyxl`")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Загрузка")
        source = st.radio("Источник", ["Google Sheets", "Excel"], key="table_source")
        
        if source == "Google Sheets":
            gs_url = st.text_input("URL", placeholder="https://docs.google.com/...")
            if st.button("📊 Загрузить"):
                if gs_url:
                    with st.spinner("Загрузка..."):
                        df = st.session_state.table_manager.read_google_sheets(gs_url)
                        if df is not None:
                            st.session_state.current_df = df
                            st.success(f"✅ {df.shape}")
        else:
            uploaded = st.file_uploader("Файл", type=['xlsx', 'xls'], key="excel_upload")
            if uploaded:
                with st.spinner("Чтение..."):
                    df = st.session_state.table_manager.read_excel(uploaded)
                    if df is not None:
                        st.session_state.current_df = df
                        st.success(f"✅ {df.shape}")
    
    with col2:
        if st.session_state.current_df is not None:
            df = st.session_state.current_df
            st.markdown("### 🔍 Предпросмотр")
            st.dataframe(df.head(10))
            
            st.markdown("### 🤖 ИИ-команда")
            instruction = st.text_area(
                "Опишите действие:",
                placeholder="Пример: удали пустые строки, добавь столбец Итого = Цена * Количество",
                height=80
            )
            
            if st.button("🚀 Выполнить", type="primary"):
                if instruction and api_key:
                    with st.spinner("🧠 Анализ..."):
                        result = st.session_state.table_manager.ai_analyze_dataframe(df, instruction, api_key)
                        
                        if 'error' not in result:
                            st.success("✅ Анализ завершён")
                            
                            with st.expander("📋 Результаты", expanded=True):
                                st.markdown(f"**Анализ:** {result.get('analysis', '')}")
                                if result.get('issues_found'):
                                    for issue in result['issues_found']:
                                        st.warning(f"⚠️ {issue}")
                            
                            if result.get('ready_code'):
                                st.code(result['ready_code'], language='python')
                                if st.button("💾 Применить"):
                                    try:
                                        df = st.session_state.table_manager.execute_transformation(df, result['ready_code'])
                                        st.session_state.current_df = df
                                        st.success("✅ Применено!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Ошибка: {e}")
                        else:
                            st.error(f"❌ {result['error']}")
            
            if st.button("💾 Сохранить Excel"):
                with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                    st.session_state.table_manager.write_excel(df, tmp.name)
                    with open(tmp.name, 'rb') as f:
                        st.download_button("📥 Скачать", f, file_name="result.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def render_help_tab():
    """Рендерит вкладку справки"""
    st.subheader("📖 Справка")
    
    st.markdown("""
    ## 🚀 Быстрый старт
    
    1. **Получите API ключ**: [platform.deepseek.com](https://platform.deepseek.com)
    2. **Вставьте ключ** в боковой панели
    3. **Выберите или создайте агента**
    4. **Начните диалог** или постройте workflow
    
    ---
    
    ## 🧠 ИИ Агенты
    
    Агенты умеют:
    - ✅ Обучаться на ваших примерах
    - ✅ Запоминать важные факты
    - ✅ Адаптироваться под ваш стиль
    - ✅ Работать в workflow
    
    ---
    
    ## 📊 Работа с таблицами
    
    Поддерживается:
    - 📥 Чтение/запись Google Sheets и Excel
    - 🎨 Авто-форматирование через ИИ
    - 📈 Создание диаграмм
    - 🧹 Очистка и трансформация данных
    - 📋 Сводные таблицы
    
    ---
    
    ## 🔀 Условия на русском
    
    Пишите естественно:
    ```
    если цена больше 1000 то отправить уведомление
    если статус равно 'успех' иначе отправить ошибку
    если текст содержит 'срочно' то отметить
    ```
    
    ---
    
    ## 🎤 Голос
    
    - Загружайте аудиофайлы (WAV/MP3)
    - Распознавание русского языка
    - Озвучка ответов агента
    
    ---
    
    ## 📱 Мобильная версия
    
    Интерфейс адаптируется под экраны:
    - < 768px: одноколоночный режим
    - ≥ 769px: двухколоночный режим
    
    ---
    
    ## 🔧 Установка
    
    ```bash
    pip install streamlit pandas openpyxl openai plotly requests
    pip install SpeechRecognition gTTS  # для голоса
    
    streamlit run workflow_builder.py
    ```
    
    ---
    
    *Workflow Builder Pro v9.0.1 • Монопоточная версия • © 2026*
    """)


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================
if __name__ == "__main__":
    main()
