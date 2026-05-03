"""
================================================================================
WORKFLOW BUILDER PRO v9.3 – ПОЛНАЯ МОНОПОТОЧНАЯ ВЕРСИЯ
Обучаемые ИИ-агенты | Расширенная работа с таблицами | Голосовой ввод | 
ИИ-обработка изображений | Мобильная адаптация
================================================================================

Описание:
    Платформа для создания автоматизированных рабочих процессов с обучаемыми 
    ИИ-агентами, поддержкой русского языка, интеграцией с таблицами и 
    продвинутым ИИ-редактором изображений с удалением водяных знаков.

Особенности:
    • Монопоточная архитектура (без asyncio/multiprocessing)
    • Полная типизация и документация
    • Расширенная работа с Google Sheets и Excel (ИСПРАВЛЕНО: sheet_names)
    • ИИ-анализ и трансформация данных
    • Голосовой ввод/вывод на русском языке
    • Парсер условий на естественном русском языке
    • Мобильная адаптация интерфейса
    • 🆕 Чат-интерфейс с полем ввода сверху
    • 🆕 Редактирование таблиц с сохранением/удалением результатов
    • 🆕 Массовая работа с изображениями (10,000+ файлов)
    • 🆕 ИИ-удаление водяных знаков через Vision API
    • 🆕 Локальное сохранение результатов обработки изображений

Зависимости:
    pip install streamlit pandas openpyxl openai plotly requests pillow rembg numpy
    
    Для расширенной работы с изображениями и ИИ:
    pip install opencv-python-headless torch torchvision

Автор: Workflow Builder Team
Версия: 9.3.0
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
from pathlib import Path
import shutil

# Работа с изображениями
try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
    from rembg import remove
    import numpy as np
    import cv2
    IMAGE_SUPPORT = True
except ImportError:
    IMAGE_SUPPORT = False
    Image = None
    remove = None
    np = None
    cv2 = None

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
# АВТОСОХРАНЕНИЕ ДАННЫХ (без ручного экспорта/импорта)
# ============================================================================
DATA_DIR = Path(__file__).parent / ".workflow_data"
DATA_DIR.mkdir(exist_ok=True)

# Папка для сохраненных изображений
IMAGES_DIR = DATA_DIR / "processed_images"
IMAGES_DIR.mkdir(exist_ok=True)

WORKFLOW_FILE = DATA_DIR / "workflow.json"
AGENTS_FILE = DATA_DIR / "agents.json"
MESSAGES_FILE = DATA_DIR / "messages.json"
HISTORY_FILE = DATA_DIR / "history.json"
TABLES_FILE = DATA_DIR / "tables.json"
IMAGES_METADATA_FILE = DATA_DIR / "images_metadata.json"


def save_workflow_auto(workflow: List[Dict]):
    """Автосохранение workflow в локальный файл"""
    try:
        with open(WORKFLOW_FILE, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Не удалось сохранить workflow: {e}")


def load_workflow_auto() -> List[Dict]:
    """Автозагрузка workflow из локального файла"""
    if WORKFLOW_FILE.exists():
        try:
            with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить workflow: {e}")
    return []


def save_agents_auto(agents_ Dict):
    """Автосохранение агентов"""
    try:
        with open(AGENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(agents_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Не удалось сохранить агентов: {e}")


def load_agents_auto() -> Optional[Dict]:
    """Автозагрузка агентов"""
    if AGENTS_FILE.exists():
        try:
            with open(AGENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить агентов: {e}")
    return None


def save_messages_auto(messages: List[Dict]):
    """Автосохранение сообщений чата"""
    try:
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Не удалось сохранить сообщения: {e}")


def load_messages_auto() -> List[Dict]:
    """Автозагрузка сообщений чата"""
    if MESSAGES_FILE.exists():
        try:
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить сообщения: {e}")
    return []


def save_history_auto(history: List[Dict]):
    """Автосохранение истории"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Не удалось сохранить историю: {e}")


def load_history_auto() -> List[Dict]:
    """Автозагрузка истории"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить историю: {e}")
    return []


def save_tables_auto(tables_ Dict):
    """Автосохранение таблиц"""
    try:
        with open(TABLES_FILE, 'w', encoding='utf-8') as f:
            # Конвертируем DataFrame в dict для JSON
            serializable = {}
            for key, value in tables_data.items():
                if isinstance(value, pd.DataFrame):
                    serializable[key] = {
                        'data': value.to_dict('records'),
                        'columns': list(value.columns),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    serializable[key] = value
            json.dump(serializable, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Не удалось сохранить таблицы: {e}")


def load_tables_auto() -> Dict:
    """Автозагрузка таблиц"""
    if TABLES_FILE.exists():
        try:
            with open(TABLES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Восстанавливаем DataFrame
                result = {}
                for key, value in data.items():
                    if isinstance(value, dict) and 'data' in value:
                        result[key] = pd.DataFrame(value['data'])
                    else:
                        result[key] = value
                return result
        except Exception as e:
            logger.warning(f"Не удалось загрузить таблицы: {e}")
    return {}


def save_images_metadata_auto(metadata: Dict):
    """Автосохранение метаданных изображений"""
    try:
        with open(IMAGES_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Не удалось сохранить метаданные изображений: {e}")


def load_images_metadata_auto() -> Dict:
    """Автозагрузка метаданных изображений"""
    if IMAGES_METADATA_FILE.exists():
        try:
            with open(IMAGES_METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить метаданные изображений: {e}")
    return {}


# ============================================================================
# КОНСТАНТЫ И КОНФИГУРАЦИЯ
# ============================================================================
@dataclass
class AppConfig:
    """Глобальная конфигурация приложения"""
    APP_TITLE: str = "Workflow Builder Pro – Голосовой помощник"
    APP_ICON: str = "🧠"
    APP_VERSION: str = "9.3.0"
    
    # API настройки
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_VISION_MODEL: str = "deepseek-vl"
    API_TIMEOUT: int = 180
    MAX_TOKENS: int = 4096
    
    # Настройки таблиц
    MAX_ROWS_GOOGLE: int = 10000
    MAX_ROWS_EXCEL: int = 100000
    SUPPORTED_EXCEL_FORMATS: Tuple[str, ...] = ("xlsx", "xlsm", "xls")
    DEFAULT_SHEET_NAME: str = "Sheet1"
    
    # Настройки изображений
    MAX_IMAGE_UPLOAD: int = 10000
    SUPPORTED_IMAGE_FORMATS: Tuple[str, ...] = ("jpg", "jpeg", "png", "webp", "bmp", "gif")
    MAX_IMAGE_SIZE_MB: int = 50
    
    # Настройки кэширования
    CACHE_TTL_SECONDS: int = 300
    
    # Настройки интерфейса
    DEFAULT_LANGUAGE: str = "ru"
    MOBILE_BREAKPOINT: int = 768
    ITEMS_PER_PAGE: int = 10
    
    # Цветовая схема
    COLORS: Dict[str, str] = field(default_factory=lambda: {
        'primary': '#6974dc',
        'primary_dark': '#764ba2',
        'success': '#00ff88',
        'error': '#ff4444',
        'warning': '#ffa500',
        'accent': '#4ECDC4',
        'dark_bg': '#1a1a2e',
        'dark_bg_2': '#16213e',
        'card_bg': '#ffffff'
    })


CONFIG = AppConfig()


# ============================================================================
# DECORATORS И УТИЛИТЫ
# ============================================================================
def cache_result(ttl_seconds: int = CONFIG.CACHE_TTL_SECONDS):
    """Декоратор для кэширования результатов функций"""
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
    """Декоратор для обработки исключений с логированием"""
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


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Конвертирует PIL Image в base64 строку"""
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode()


def base64_to_image(base64_string: str) -> Image.Image:
    """Конвертирует base64 строку в PIL Image"""
    image_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_data))


def resize_image_for_api(image: Image.Image, max_size: int = 1024) -> Image.Image:
    """Уменьшает изображение для отправки в API"""
    if max(image.size) <= max_size:
        return image
    ratio = max_size / max(image.size)
    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS)


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


class ImageEditOperation(Enum):
    """Операции редактирования изображений"""
    REMOVE_BACKGROUND = "remove_background"
    REMOVE_WATERMARK = "remove_watermark"
    AI_REMOVE_WATERMARK = "ai_remove_watermark"
    RESIZE = "resize"
    CROP = "crop"
    ROTATE = "rotate"
    ENHANCE = "enhance"
    FILTER = "filter"
    ADD_TEXT = "add_text"
    ADD_WATERMARK = "add_watermark"
    CONVERT_FORMAT = "convert_format"


# ============================================================================
# CSS СТИЛИ
# ============================================================================
def get_app_styles() -> str:
    """Возвращает CSS стили приложения"""
    return """
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #6974dc 0%, #764ba2 100%);
            --success-color: #00ff88;
            --error-color: #ff4444;
            --warning-color: #ffa500;
            --accent-color: #4ECDC4;
            --text-on-light: #000000;
            --text-secondary: #4a4a6a;
        }
        
        body, .stApp, .main, .block-container {
            color: var(--text-on-light) !important;
            background-color: #f0f2f6 !important;
        }
        
        p, span, div, li, a, label, h1, h2, h3, h4, h5, h6, strong, b {
            color: var(--text-on-light) !important;
        }
        
        small, .caption { color: var(--text-secondary) !important; }
        
        .stTextInput input, .stTextArea textarea, .stNumberInput input,
        .stSelectbox select, .stMultiselect select, input[type="text"],
        input[type="number"], input[type="password"], textarea {
            color: #000000 !important;
            background-color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }
        
        .stButton button {
            border-radius: 12px !important; 
            font-weight: 600 !important;
            transition: all 0.2s ease;
            border: none !important;
            background-color: #ffffff !important;
            color: #000000 !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }
        
        .stButton button:hover { 
            transform: scale(1.03); 
            box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
            background-color: #f8f9fa !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border: none !important;
            box-shadow: 2px 0 10px rgba(0,0,0,0.05) !important;
        }
        
        .main-header {
            background: var(--primary-gradient);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            animation: fadeIn 1s ease-in;
            box-shadow: 0 10px 40px rgba(105, 116, 220, 0.3);
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .main-header h1 { color: white !important; margin: 0; font-size: 2.5rem; }
        .main-header p { color: rgba(255,255,255,0.95) !important; margin: 0.5rem 0 0 0; }
        .version-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-top: 0.5rem;
            color: white !important;
        }
        
        .agent-card {
            background: #ffffff !important;
            border-radius: 15px; 
            padding: 1rem; 
            margin: 0.5rem 0;
            border: none !important;
            transition: all 0.3s ease;
            color: #000000 !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }
        
        .agent-card:hover { 
            transform: translateX(5px); 
            box-shadow: 0 8px 25px rgba(105, 116, 220, 0.2);
        }
        
        .agent-card-selected {
            background: linear-gradient(135deg, #f0fff4 0%, #e6ffed 100%) !important;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.15);
            border-left: 4px solid var(--success-color) !important;
        }
        
        .stat-card {
            background: #ffffff !important;
            padding: 1.2rem; 
            border-radius: 15px; 
            text-align: center; 
            color: #000000 !important;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }
        
        .stat-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 10px 30px rgba(105, 116, 220, 0.15);
        }
        
        .stat-card h3 { margin: 0; font-size: 2rem; font-weight: bold; color: #6974dc !important; }
        .stat-card p { margin: 0.3rem 0 0 0; opacity: 0.9; color: #4a4a6a !important; }
        
        .memory-box, .condition-box, .info-box {
            background: #ffffff !important;
            padding: 1rem; 
            border-radius: 12px;
            margin: 0.5rem 0;
            border: none !important;
            color: #000000 !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        }
        
        .memory-box { border-left: 4px solid var(--warning-color) !important; }
        .condition-box { border-left: 4px solid var(--warning-color) !important; font-family: 'Courier New', monospace; }
        .info-box { border-left: 4px solid var(--accent-color) !important; }
        
        .workflow-node {
            background: #ffffff !important;
            border-radius: 15px; 
            padding: 1rem; 
            margin: 0.5rem 0; 
            color: #000000 !important;
            border: none !important;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }
        
        .workflow-node:hover { 
            transform: translateX(5px); 
            box-shadow: 0 8px 25px rgba(105, 116, 220, 0.15);
        }
        
        .workflow-node-success {
            background: linear-gradient(135deg, #f0fff4 0%, #e6ffed 100%) !important;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.15);
        }
        
        .workflow-node-error {
            background: linear-gradient(135deg, #fff5f5 0%, #ffe6e6 100%) !important;
            box-shadow: 0 0 20px rgba(255, 68, 68, 0.15);
        }
        
        .workflow-connector {
            text-align: center;
            font-size: 1.2rem;
            color: var(--accent-color) !important;
            margin: 0.3rem 0;
        }
        
        .dataframe {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border: none !important;
            background-color: #ffffff !important;
        }
        
        @media (max-width: 768px) {
            .main-header { padding: 1.5rem; border-radius: 15px; }
            .main-header h1 { font-size: 1.8rem !important; }
            .stButton button { padding: 0.8rem 1.5rem !important; width: 100%; }
            div[data-testid="column"] { flex: 1 1 100% !important; max-width: 100% !important; }
            .desktop-only { display: none !important; }
        }
        
        .chat-input-container {
            position: sticky;
            top: 0;
            background: #ffffff;
            padding: 1rem 0;
            border-bottom: 1px solid #e0e0e0;
            z-index: 100;
            margin-bottom: 1rem;
        }
        
        .chat-message-user {
            background: linear-gradient(135deg, #6974dc, #764ba2);
            color: white !important;
            padding: 0.8rem 1.2rem;
            border-radius: 18px 18px 4px 18px;
            margin-left: auto;
            max-width: 80%;
        }
        
        .chat-message-agent {
            background: #f0f2f6;
            color: #000000 !important;
            padding: 0.8rem 1.2rem;
            border-radius: 18px 18px 18px 4px;
            margin-right: auto;
            max-width: 80%;
        }
        
        .table-editor {
            background: #ffffff;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin: 0.5rem 0;
        }
        
        .image-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 0.8rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin: 0.5rem;
            text-align: center;
        }
        
        .image-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            padding: 1rem;
        }
        
        .upload-progress {
            background: linear-gradient(135deg, #6974dc, #764ba2);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            text-align: center;
        }
    </style>
    """


# ============================================================================
# КЛАСС ДЛЯ ПРЕОБРАЗОВАНИЯ РУССКИХ УСЛОВИЙ
# ============================================================================
class RussianConditionParser:
    """Преобразует условия на русском языке в исполняемый код"""
    
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
    ]
    
    @classmethod
    def parse(cls, condition_text: str) -> Dict[str, Any]:
        """Преобразует русское условие в структурированный формат"""
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
        
        if 'если' in condition_text:
            result = cls._parse_if_statement(condition_text, result)
            return result
        
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
# МЕНЕДЖЕР ДЛЯ РАБОТЫ С ТАБЛИЦАМИ (ИСПРАВЛЕНО: sheet_names)
# ============================================================================
class TableManager:
    """Универсальный менеджер для работы с Google Sheets и Excel"""
    
    def __init__(self, api_key: Optional[str] = None):
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
        """Читает данные из Google Sheets"""
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
        """Читает данные из Excel файла"""
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
        ИСПРАВЛЕНО: доступ к sheet_names через writer.book.sheetnames
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
        """
        Применяет форматирование к листу Excel.
        ИСПРАВЛЕНО: правильный доступ к листам через writer.sheets или writer.book
        """
        # ИСПРАВЛЕНИЕ: Получаем имя активного листа корректно
        if hasattr(writer, 'book') and hasattr(writer.book, 'sheetnames'):
            # Для openpyxl writer
            sheet_names = writer.book.sheetnames
            worksheet_name = sheet_names[0] if sheet_names else 'Sheet1'
            worksheet = writer.book[worksheet_name]
        elif hasattr(writer, 'sheets'):
            # Альтернативный доступ
            worksheet = list(writer.sheets.values())[0] if writer.sheets else None
            if worksheet is None:
                return
        else:
            return
        
        # Авто-ширина колонок
        for column in worksheet.columns:
            max_length = max(
                (len(str(cell.value)) if cell.value else 0) 
                for cell in column
            )
            col_letter = column[0].column_letter
            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
        
        # Форматирование заголовка
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
        """Создаёт диаграмму в Excel файле"""
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
        """Анализирует DataFrame через ИИ и возвращает рекомендации"""
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
            
            # Убираем markdown разметку
            if "```json" in content:
                content = content.split("```json", 1)[1]
                content = content.split("```", 1)[0]
            elif "```" in content:
                content = content.split("```", 1)[1]
                content = content.split("```", 1)[0]
            
            # Ищем JSON объект
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group()
                
                # Чистим от комментариев
                json_str = re.sub(r'//[^\n]*', '', json_str)
                json_str = re.sub(r'/\*[\s\S]*?\*/', '', json_str)
                
                # Фиксим trailing commas
                json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)
                
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    return {'error': f'Ошибка парсинга JSON: {str(e)}'}
            
            return {'error': 'Не удалось извлечь JSON из ответа'}
            
        except Exception as e:
            return {'error': f'Ошибка ИИ: {str(e)}'}
    
    def execute_transformation(
        self, 
        df: pd.DataFrame, 
        transformation_code: str
    ) -> pd.DataFrame:
        """Выполняет код трансформации над DataFrame"""
        safe_globals = {"pd": pd, "np": __import__('numpy') if 'numpy' in transformation_code else None, "df": df.copy()}
        
        try:
            exec(transformation_code, safe_globals, safe_globals)
            return safe_globals.get('df', df)
        except Exception as e:
            logger.error(f"Ошибка выполнения: {e}")
            raise


# ============================================================================
# 🆕 МЕНЕДЖЕР ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ (С ИИ-УДАЛЕНИЕМ ВОДЯНЫХ ЗНАКОВ)
# ============================================================================
class ImageManager:
    """Менеджер для массовой обработки изображений с ИИ"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.processed_count = 0
        self.total_count = 0
        
    def remove_background(self, image: Image.Image) -> Image.Image:
        """Удаляет фон с изображения используя rembg"""
        if not IMAGE_SUPPORT or remove is None:
            raise ImportError("Установите rembg: pip install rembg")
        
        # Конвертируем в bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Удаляем фон
        output = remove(img_byte_arr.read())
        
        # Возвращаем как Image
        return Image.open(BytesIO(output))
    
    def remove_watermark_basic(self, image: Image.Image) -> Image.Image:
        """Базовое удаление водяного знака (инпейнтинг через OpenCV)"""
        if not IMAGE_SUPPORT or cv2 is None or np is None:
            raise ImportError("Установите opencv-python: pip install opencv-python")
        
        # Конвертируем PIL в OpenCV
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Простая эвристика: ищем полупрозрачные области или области с высокой контрастностью
        if image.mode == 'RGBA':
            alpha = np.array(image)[:, :, 3]
            # Находим области с низкой прозрачностью (типичный водяной знак)
            watermark_mask = (alpha < 200) & (alpha > 50)
        else:
            # Для RGB: ищем очень светлые или очень темные области
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # Предполагаем, что водяной знак - это небольшие контрастные области
            watermark_mask = binary < 128
        
        # Инпейнтинг через OpenCV
        mask_uint8 = (watermark_mask * 255).astype(np.uint8)
        
        # Применяем телеа-инпейнтинг
        result_cv = cv2.inpaint(img_cv, mask_uint8, 3, cv2.INPAINT_TELEA)
        
        # Конвертируем обратно в PIL
        result_rgb = cv2.cvtColor(result_cv, cv2.COLOR_BGR2RGB)
        return Image.fromarray(result_rgb)
    
    @handle_errors(default_return=None)
    def ai_remove_watermark(self, image: Image.Image, api_key: str, 
                           description: str = "Удали водяной знак, сохранив основное изображение") -> Optional[Image.Image]:
        """
        🆕 ИИ-удаление водяного знака через Vision API
        
        Отправляет изображение в ИИ с инструкцией удалить водяной знак.
        Использует возможности мультимодальных моделей для понимания контекста.
        """
        if not api_key:
            raise ValueError("API ключ не указан")
        
        if not IMAGE_SUPPORT:
            raise ImportError("Установите pillow: pip install pillow")
        
        try:
            client = OpenAI(api_key=api_key, base_url=CONFIG.DEEPSEEK_BASE_URL)
            
            # Уменьшаем изображение для API
            processed_image = resize_image_for_api(image, max_size=1024)
            
            # Конвертируем в base64
            img_base64 = image_to_base64(processed_image, format="JPEG")
            
            # Формируем промпт для ИИ
            prompt = f"""
Ты эксперт по обработке изображений. 

Задача: {description}

Проанализируй изображение и определи:
1. Где находится водяной знак/логотип/текст
2. Как лучше всего его удалить, чтобы не повредить основное изображение
3. Какие области нужно восстановить (инпейнтинг)

Верни ответ в формате JSON:
{{
    "watermark_detected": true/false,
    "watermark_location": {{
        "description": "где находится водяной знак",
        "approximate_coords": [x1, y1, x2, y2]
    }},
    "removal_strategy": "описание стратегии удаления",
    "confidence": 0.0-1.0,
    "instructions_for_post_processing": [
        "шаг 1",
        "шаг 2"
    ]
}}

Если водяной знак не найден или удаление невозможно, верни watermark_detected: false.
Отвечай ТОЛЬКО валидным JSON на русском или английском.
"""
            
            # Отправляем запрос с изображением
            response = client.chat.completions.create(
                model=CONFIG.DEEPSEEK_VISION_MODEL if hasattr(CONFIG, 'DEEPSEEK_VISION_MODEL') else CONFIG.DEEPSEEK_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                timeout=CONFIG.API_TIMEOUT,
                max_tokens=CONFIG.MAX_TOKENS
            )
            
            content = response.choices[0].message.content
            
            # Парсим JSON ответ
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                analysis = json.loads(json_match.group())
                
                if analysis.get('watermark_detected', False):
                    # Применяем стратегию удаления на основе анализа ИИ
                    return self._apply_ai_watermark_removal(image, analysis)
                else:
                    logger.info("ИИ не обнаружил водяной знак")
                    return image  # Возвращаем оригинал
            else:
                # Если не удалось распарсить, пробуем базовый метод
                logger.warning("Не удалось распарсить ответ ИИ, использую базовый метод")
                return self.remove_watermark_basic(image)
                
        except Exception as e:
            logger.error(f"Ошибка ИИ-удаления водяного знака: {e}")
            # Фолбэк на базовый метод
            try:
                return self.remove_watermark_basic(image)
            except:
                return image
    
    def _apply_ai_watermark_removal(self, image: Image.Image, analysis: Dict) -> Image.Image:
        """
        Применяет стратегию удаления водяного знака на основе анализа ИИ
        """
        if not IMAGE_SUPPORT or cv2 is None or np is None:
            return self.remove_watermark_basic(image)
        
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        coords = analysis.get('watermark_location', {}).get('approximate_coords')
        
        if coords and len(coords) == 4:
            x1, y1, x2, y2 = coords
            # Создаем маску для области водяного знака
            mask = np.zeros(img_cv.shape[:2], dtype=np.uint8)
            
            # Рисуем прямоугольник маски
            cv2.rectangle(mask, (int(x1), int(y1)), (int(x2), int(y2)), 255, -1)
            
            # Применяем инпейнтинг только к указанной области
            result = cv2.inpaint(img_cv, mask, 3, cv2.INPAINT_TELEA)
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            return Image.fromarray(result_rgb)
        else:
            # Если координаты не указаны, используем базовый метод
            return self.remove_watermark_basic(image)
    
    def resize_image(self, image: Image.Image, width: Optional[int] = None, 
                     height: Optional[int] = None, maintain_aspect: bool = True) -> Image.Image:
        """Изменяет размер изображения"""
        if width is None and height is None:
            return image
        
        if maintain_aspect:
            img_width, img_height = image.size
            if width and height:
                ratio = min(width / img_width, height / img_height)
            elif width:
                ratio = width / img_width
            else:
                ratio = height / img_height
            
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
        else:
            new_width = width or image.size[0]
            new_height = height or image.size[1]
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def crop_image(self, image: Image.Image, left: int, top: int, 
                   right: int, bottom: int) -> Image.Image:
        """Обрезает изображение"""
        return image.crop((left, top, right, bottom))
    
    def rotate_image(self, image: Image.Image, angle: float, expand: bool = True) -> Image.Image:
        """Поворачивает изображение"""
        return image.rotate(angle, expand=expand, resample=Image.Resampling.BICUBIC)
    
    def enhance_image(self, image: Image.Image, brightness: float = 1.0, 
                      contrast: float = 1.0, sharpness: float = 1.0) -> Image.Image:
        """Улучшает изображение"""
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)
        
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)
        
        if sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(sharpness)
        
        return image
    
    def apply_filter(self, image: Image.Image, filter_type: str) -> Image.Image:
        """Применяет фильтр к изображению"""
        filters = {
            'blur': ImageFilter.BLUR,
            'sharpen': ImageFilter.SHARPEN,
            'edge_enhance': ImageFilter.EDGE_ENHANCE,
            'contour': ImageFilter.CONTOUR,
            'emboss': ImageFilter.EMBOSS,
            'smooth': ImageFilter.SMOOTH,
            'detail': ImageFilter.DETAIL,
        }
        
        if filter_type in filters:
            return image.filter(filters[filter_type])
        return image
    
    def add_text_watermark(self, image: Image.Image, text: str, position: str = "bottom-right",
                           font_size: int = 40, opacity: int = 128, 
                           color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        """Добавляет текстовый водяной знак"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        draw = ImageDraw.Draw(txt_layer)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        img_width, img_height = image.size
        padding = 20
        
        if position == "top-left":
            x, y = padding, padding
        elif position == "top-right":
            x, y = img_width - text_width - padding, padding
        elif position == "bottom-left":
            x, y = padding, img_height - text_height - padding
        else:
            x, y = img_width - text_width - padding, img_height - text_height - padding
        
        draw.text((x, y), text, font=font, fill=(*color, opacity))
        
        return Image.alpha_composite(image, txt_layer)
    
    def convert_format(self, image: Image.Image, format: str) -> Image.Image:
        """Конвертирует изображение в другой формат"""
        if format.upper() in ['JPEG', 'JPG']:
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                return background
            return image.convert('RGB')
        return image
    
    def process_batch(self, images: List[Tuple[str, Image.Image]], 
                      operation: ImageEditOperation, 
                      params: Dict[str, Any],
                      api_key: Optional[str] = None,
                      progress_callback: Optional[Callable] = None) -> List[Tuple[str, Image.Image]]:
        """Обрабатывает пакет изображений"""
        self.total_count = len(images)
        self.processed_count = 0
        results = []
        
        for filename, image in images:
            try:
                processed = self._apply_operation(image, operation, params, api_key)
                results.append((filename, processed))
                
                self.processed_count += 1
                if progress_callback:
                    progress_callback(self.processed_count, self.total_count, filename)
                    
            except Exception as e:
                logger.error(f"Ошибка обработки {filename}: {e}")
                results.append((filename, None))
        
        return results
    
    def _apply_operation(self, image: Image.Image, operation: ImageEditOperation, 
                         params: Dict[str, Any], api_key: Optional[str] = None) -> Image.Image:
        """Применяет операцию к изображению"""
        if operation == ImageEditOperation.REMOVE_BACKGROUND:
            return self.remove_background(image)
        
        elif operation == ImageEditOperation.REMOVE_WATERMARK:
            return self.remove_watermark_basic(image)
        
        elif operation == ImageEditOperation.AI_REMOVE_WATERMARK:
            if api_key:
                return self.ai_remove_watermark(image, api_key, params.get('description', 'Удали водяной знак'))
            else:
                logger.warning("API ключ не указан для ИИ-обработки, использую базовый метод")
                return self.remove_watermark_basic(image)
        
        elif operation == ImageEditOperation.RESIZE:
            return self.resize_image(
                image, 
                width=params.get('width'),
                height=params.get('height'),
                maintain_aspect=params.get('maintain_aspect', True)
            )
        
        elif operation == ImageEditOperation.CROP:
            return self.crop_image(
                image,
                params.get('left', 0),
                params.get('top', 0),
                params.get('right', image.size[0]),
                params.get('bottom', image.size[1])
            )
        
        elif operation == ImageEditOperation.ROTATE:
            return self.rotate_image(
                image, 
                params.get('angle', 0),
                params.get('expand', True)
            )
        
        elif operation == ImageEditOperation.ENHANCE:
            return self.enhance_image(
                image,
                brightness=params.get('brightness', 1.0),
                contrast=params.get('contrast', 1.0),
                sharpness=params.get('sharpness', 1.0)
            )
        
        elif operation == ImageEditOperation.FILTER:
            return self.apply_filter(image, params.get('filter_type', 'blur'))
        
        elif operation == ImageEditOperation.ADD_WATERMARK:
            return self.add_text_watermark(
                image,
                text=params.get('text', 'Watermark'),
                position=params.get('position', 'bottom-right'),
                font_size=params.get('font_size', 40),
                opacity=params.get('opacity', 128),
                color=tuple(params.get('color', [255, 255, 255]))
            )
        
        elif operation == ImageEditOperation.CONVERT_FORMAT:
            return self.convert_format(image, params.get('format', 'PNG'))
        
        return image


# ============================================================================
# КЛАСС ИИ АГЕНТА
# ============================================================================
class AIAgent:
    """Класс для создания и обучения ИИ агентов"""
    
    def __init__(self, name: str, role: str, system_prompt: str, agent_id: Optional[str] = None):
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
        """Добавляет пример для обучения агента"""
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
        """Добавляет факт в память агента"""
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
        """Получает значение из памяти по ключу"""
        for mem in self.memory:
            if mem['key'] == key:
                mem['access_count'] += 1
                return mem['value']
        return None
    
    def add_conversation(self, user_message: str, agent_response: str, feedback: Optional[str] = None):
        """Добавляет диалог в историю"""
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
        """Генерирует ответ агента на запрос пользователя"""
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
    def from_dict(cls,  Dict) -> 'AIAgent':
        """Десериализует агента из словаря"""
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
            'success_rate': 0.0,
            'last_trained': None,
            'last_used': None
        })
        return agent


# ============================================================================
# МЕНЕДЖЕР АГЕНТОВ
# ============================================================================
class AgentManager:
    """Управляет коллекцией ИИ агентов"""
    
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.current_agent_id: Optional[str] = None
        self.load_agents()
    
    def load_agents(self):
        """Загружает агентов из session_state"""
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
        """Сохраняет агентов в session_state и авто-файл"""
        st.session_state.agents = {agent_id: agent.to_dict() for agent_id, agent in self.agents.items()}
        st.session_state.current_agent_id = self.current_agent_id
        save_agents_auto(st.session_state.agents)
    
    def add_agent(self, name: str, role: str, system_prompt: str) -> AIAgent:
        """Создаёт и добавляет нового агента"""
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
        """Импортирует агента из JSON"""
        try:
            data = json.loads(agent_json)
            agent = AIAgent.from_dict(data)
            self.agents[agent.id] = agent
            self.save_agents()
            return True
        except Exception as e:
            logger.error(f"Ошибка импорта агента: {e}")
            st.error(f"Ошибка импорта: {str(e)}")
            return False


# ============================================================================
# ГЕНЕРАТОР WORKFLOW ЧЕРЕЗ ИИ
# ============================================================================
class AIWorkflowGenerator:
    """Генерирует workflow из текстового описания на русском"""
    
    @staticmethod
    def generate(description: str, api_key: str) -> List[Dict]:
        """Генерирует workflow из описания"""
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
        self.workflow = workflow
        self.api_key = api_key
        self.agent_manager = agent_manager
        self.table_manager = table_manager or TableManager(api_key)
        self.context: Dict[str, Any] = {}
        self.results: List[Dict] = []
        self.current_node_index: int = 0
        self.start_time: Optional[float] = None
    
    def execute(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Выполняет весь workflow"""
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
    """Распознавание русской речи из аудиобайтов"""
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
    """Генерация MP3 из текста (русский язык)"""
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
    """Инициализирует session_state с автозагрузкой данных"""
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
        'excel_loaded': False,
        'data_loaded': False,
        'saved_tables': {},
        'table_edit_mode': False,
        'editing_table_id': None,
        'image_manager': None,
        'uploaded_images': {},
        'processed_images': {},
        'image_batch_progress': 0,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    if not st.session_state.get('data_loaded'):
        saved_workflow = load_workflow_auto()
        if saved_workflow:
            st.session_state.workflow = saved_workflow
        
        saved_messages = load_messages_auto()
        if saved_messages:
            st.session_state.agent_messages = saved_messages
        
        saved_history = load_history_auto()
        if saved_history:
            st.session_state.history = saved_history
        
        saved_agents = load_agents_auto()
        if saved_agents and 'agents' not in st.session_state:
            st.session_state.agents = saved_agents
        
        saved_tables = load_tables_auto()
        if saved_tables:
            st.session_state.saved_tables = saved_tables
        
        st.session_state.data_loaded = True


def main():
    """Точка входа приложения"""
    st.set_page_config(
        page_title=CONFIG.APP_TITLE,
        page_icon=CONFIG.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown(get_app_styles(), unsafe_allow_html=True)
    initialize_session_state()
    
    # Автосохранение
    current_workflow = st.session_state.get('workflow', [])
    if hasattr(st, '_last_workflow'):
        if current_workflow != st._last_workflow:
            save_workflow_auto(current_workflow)
    st._last_workflow = current_workflow.copy() if current_workflow else []
    
    current_messages = st.session_state.get('agent_messages', [])
    if hasattr(st, '_last_messages'):
        if current_messages != st._last_messages:
            save_messages_auto(current_messages)
    st._last_messages = current_messages.copy() if current_messages else []
    
    current_history = st.session_state.get('history', [])
    if hasattr(st, '_last_history'):
        if current_history != st._last_history:
            save_history_auto(current_history)
    st._last_history = current_history.copy() if current_history else []
    
    current_tables = st.session_state.get('saved_tables', {})
    if hasattr(st, '_last_tables'):
        if current_tables != st._last_tables:
            save_tables_auto(current_tables)
    st._last_tables = current_tables.copy() if current_tables else {}
    
    # Заголовок
    st.markdown(f"""
    <div class="main-header">
        <h1>{CONFIG.APP_ICON} WORKFLOW BUILDER PRO v{CONFIG.APP_VERSION}</h1>
        <p>ИИ агенты | Таблицы | Изображения с ИИ | Голос | Мобильная версия</p>
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
        
        if st.session_state.agent_manager is None:
            st.session_state.agent_manager = AgentManager()
        
        agent_manager = st.session_state.agent_manager
        
        for agent in agent_manager.agents.values():
            is_selected = agent_manager.current_agent_id == agent.id
            
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
        
        with st.expander("🗑️ Управление данными", expanded=False):
            if st.button("🔄 Сбросить workflow", use_container_width=True):
                st.session_state.workflow = []
                save_workflow_auto([])
                st.rerun()
            
            if st.button("🗑️ Очистить чат", use_container_width=True):
                st.session_state.agent_messages = []
                save_messages_auto([])
                st.rerun()
            
            if st.button("⚠️ Сбросить ВСЁ", use_container_width=True, type="secondary"):
                for f in [WORKFLOW_FILE, AGENTS_FILE, MESSAGES_FILE, HISTORY_FILE, TABLES_FILE, IMAGES_METADATA_FILE]:
                    if f.exists():
                        f.unlink()
                if IMAGES_DIR.exists():
                    shutil.rmtree(IMAGES_DIR)
                    IMAGES_DIR.mkdir(exist_ok=True)
                for key in ['workflow', 'agent_messages', 'history', 'agents', 'data_loaded', 
                           'saved_tables', 'uploaded_images', 'processed_images']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        st.markdown("---")
        st.markdown("## 📊 СТАТИСТИКА")
        st.metric("Агентов", len(agent_manager.agents))
        
        current_agent = agent_manager.get_current_agent()
        if current_agent:
            st.metric("Обучений", current_agent.stats['total_trainings'])
            st.metric("Диалогов", current_agent.stats['total_conversations'])
        
        st.markdown("---")
        st.markdown("## 🖼️ Изображения")
        st.metric("Загружено", len(st.session_state.uploaded_images))
        st.metric("Обработано", len(st.session_state.processed_images))
        
        st.markdown("---")
        
        if st.button("🗑️ Очистить workflow", use_container_width=True):
            st.session_state.workflow = []
            st.rerun()
    
    # Менеджеры
    if st.session_state.table_manager is None:
        st.session_state.table_manager = TableManager(api_key)
    
    if st.session_state.image_manager is None:
        st.session_state.image_manager = ImageManager(api_key)
    
    # Вкладки
    tabs = st.tabs([
        "💬 Диалог", "📚 Обучение", "🧠 Память", "📊 Аналитика",
        "🤖 Workflow", "🔀 Условия", "🗂 Таблицы+ИИ", "🖼️ Изображения", "📖 Справка"
    ])
    
    with tabs[0]:
        render_chat_tab(agent_manager, api_key)
    
    with tabs[1]:
        render_training_tab(agent_manager)
    
    with tabs[2]:
        render_memory_tab(agent_manager)
    
    with tabs[3]:
        render_analytics_tab(agent_manager)
    
    with tabs[4]:
        render_workflow_tab(agent_manager, api_key)
    
    with tabs[5]:
        render_conditions_tab()
    
    with tabs[6]:
        render_tables_tab(api_key)
    
    with tabs[7]:
        render_images_tab(api_key)
    
    with tabs[8]:
        render_help_tab()


def render_chat_tab(agent_manager: AgentManager, api_key: str):
    """Рендерит вкладку диалога - ПОЛЕ ВВОДА ВСЕГДА СВЕРХУ"""
    current_agent = agent_manager.get_current_agent()
    
    if not current_agent:
        st.warning("⚠️ Выберите агента в боковой панели")
        return
    
    st.subheader(f"💬 {current_agent.name}")
    st.caption(f"Роль: {current_agent.role}")
    
    # 🆕 ПОЛЕ ВВОДА СНАЧАЛА (всегда сверху!)
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    
    user_input = st.text_area(
        "✏️ Напишите сообщение...", 
        height=80, 
        key="chat_input",
        placeholder="Введите ваш вопрос...",
        label_visibility="collapsed"
    )
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    
    with col1:
        use_training = st.checkbox("📚 Обуч.", value=True, key="chat_use_training")
    
    with col2:
        if VOICE_SUPPORT and st.button("🎤", use_container_width=True):
            st.session_state.voice_show_upload = True
    
    with col3:
        if st.button("🔊", use_container_width=True):
            if st.session_state.agent_messages and st.session_state.agent_messages[-1]['role'] == 'agent':
                audio = text_to_speech_mp3(st.session_state.agent_messages[-1]['content'])
                if audio:
                    st.audio(audio, format="audio/mp3")
    
    with col4:
        if st.button("🚀 Отправить", type="primary", use_container_width=True):
            if user_input.strip():
                st.session_state.agent_messages.append({'role': 'user', 'content': user_input.strip()})
                st.session_state.chat_input = ""  # 🆕 Автоочистка
                
                with st.spinner("🤖 Агент думает..."):
                    response = current_agent.generate_response(user_input.strip(), api_key, use_training)
                
                st.session_state.agent_messages.append({'role': 'agent', 'content': response})
                current_agent.add_conversation(user_input.strip(), response)
                agent_manager.save_agents()
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 🆕 ИСТОРИЯ СООБЩЕНИЙ (после поля ввода)
    st.markdown("### 📜 История диалога")
    
    if not st.session_state.agent_messages:
        st.info("💬 Начните диалог, введя сообщение выше")
    else:
        for msg in st.session_state.agent_messages:
            if msg['role'] == 'user':
                st.markdown(f'<div class="chat-message-user"><strong>👤 Вы:</strong><br>{msg["content"]}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message-agent"><strong>🤖 {current_agent.name}:</strong><br>{msg["content"]}</div>', 
                           unsafe_allow_html=True)
    
    if st.session_state.voice_show_upload:
        with st.expander("🎤 Голосовой ввод", expanded=True):
            audio_file = st.file_uploader("Выберите файл", type=["wav", "mp3"], key="voice_upload")
            if audio_file:
                recognized = recognize_speech_from_audio(audio_file.read())
                if recognized:
                    st.success(f"✅ Распознано: {recognized}")
                    st.session_state.chat_input = recognized
                    st.session_state.voice_show_upload = False
                    st.rerun()
    
    if st.button("🗑️ Очистить диалог", use_container_width=True):
        st.session_state.agent_messages = []
        save_messages_auto([])
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
    • если статус равно 'успех' иначе отправить ошибку
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


def render_tables_tab(api_key: str):
    """Рендерит вкладку таблиц с ИИ и редактированием"""
    st.subheader("🗂 Таблицы + ИИ + Редактор")
    
    if not EXCEL_SUPPORT:
        st.warning("⚠️ Установите openpyxl: `pip install openpyxl`")
    
    with st.expander("📚 Сохранённые таблицы", expanded=not st.session_state.saved_tables):
        if not st.session_state.saved_tables:
            st.info("💡 Нет сохранённых таблиц")
        else:
            for table_id, df in st.session_state.saved_tables.items():
                with st.expander(f"📊 {table_id} ({df.shape[0]}×{df.shape[1]})", expanded=False):
                    st.dataframe(df.head(5), use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✏️ Открыть", key=f"open_{table_id}", use_container_width=True):
                            st.session_state.current_df = df.copy()
                            st.session_state.editing_table_id = table_id
                            st.rerun()
                    with col2:
                        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                            st.session_state.table_manager.write_excel(df, tmp.name)
                            with open(tmp.name, 'rb') as f:
                                st.download_button("📥 Скачать", f, file_name=f"{table_id}.xlsx",
                                                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                 key=f"dl_saved_{table_id}", use_container_width=True)
                    with col3:
                        if st.button("🗑️ Удалить", key=f"del_saved_{table_id}", use_container_width=True):
                            del st.session_state.saved_tables[table_id]
                            save_tables_auto(st.session_state.saved_tables)
                            if st.session_state.editing_table_id == table_id:
                                st.session_state.current_df = None
                                st.session_state.editing_table_id = None
                            st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Загрузка данных")
        source = st.radio("Источник", ["Google Sheets", "Excel"], key="table_source")
        
        if source == "Google Sheets":
            gs_url = st.text_input("URL Google Sheets", placeholder="https://docs.google.com/spreadsheets/d/...", key="gs_url_input")
            if st.button("📊 Загрузить из Google", use_container_width=True):
                if gs_url:
                    with st.spinner("Загрузка..."):
                        df = st.session_state.table_manager.read_google_sheets(gs_url)
                        if df is not None:
                            table_id = f"gs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            st.session_state.current_df = df
                            st.session_state.editing_table_id = table_id
                            st.session_state.saved_tables[table_id] = df.copy()
                            save_tables_auto(st.session_state.saved_tables)
                            st.success(f"✅ Загружено: {df.shape}")
                            st.rerun()
        else:
            uploaded = st.file_uploader("Excel файл", type=['xlsx', 'xls', 'csv'], key="excel_upload")
            if uploaded:
                with st.spinner("Чтение файла..."):
                    try:
                        if uploaded.name.endswith('.csv'):
                            df = pd.read_csv(uploaded)
                        else:
                            df = st.session_state.table_manager.read_excel(uploaded)
                        if df is not None:
                            table_id = f"ex_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            st.session_state.current_df = df
                            st.session_state.editing_table_id = table_id
                            st.session_state.saved_tables[table_id] = df.copy()
                            save_tables_auto(st.session_state.saved_tables)
                            st.success(f"✅ Загружено: {df.shape}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка чтения: {e}")
    
    with col2:
        if st.session_state.current_df is not None and st.session_state.editing_table_id:
            st.markdown(f'<div class="table-editor">', unsafe_allow_html=True)
            
            st.markdown(f"### 📊 Редактор: {st.session_state.editing_table_id}")
            st.caption(f"Размер: {st.session_state.current_df.shape[0]} строк × {st.session_state.current_df.shape[1]} столбцов")
            
            col_actions = st.columns(4)
            with col_actions[0]:
                if st.button("💾 Сохранить", key=f"save_{st.session_state.editing_table_id}", use_container_width=True):
                    st.session_state.saved_tables[st.session_state.editing_table_id] = st.session_state.current_df.copy()
                    save_tables_auto(st.session_state.saved_tables)
                    st.success("✅ Сохранено!")
            with col_actions[1]:
                if st.button("🗑️ Удалить", key=f"delete_{st.session_state.editing_table_id}", use_container_width=True):
                    if st.session_state.editing_table_id in st.session_state.saved_tables:
                        del st.session_state.saved_tables[st.session_state.editing_table_id]
                        save_tables_auto(st.session_state.saved_tables)
                    st.session_state.current_df = None
                    st.success("🗑️ Удалено")
                    st.rerun()
            with col_actions[2]:
                with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                    st.session_state.table_manager.write_excel(st.session_state.current_df, tmp.name)
                    with open(tmp.name, 'rb') as f:
                        st.download_button("📥 Excel", f, file_name=f"{st.session_state.editing_table_id}.xlsx", 
                                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                         key=f"dl_{st.session_state.editing_table_id}", use_container_width=True)
            
            st.markdown("#### ✏️ Редактирование данных")
            edited_df = st.data_editor(
                st.session_state.current_df,
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_{st.session_state.editing_table_id}",
                hide_index=True
            )
            
            if not st.session_state.current_df.equals(edited_df):
                st.session_state.current_df = edited_df
                st.session_state.saved_tables[st.session_state.editing_table_id] = edited_df.copy()
                save_tables_auto(st.session_state.saved_tables)
                st.toast("🔄 Изменения сохранены", icon="💾")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("💡 Загрузите таблицу слева или выберите из сохранённых выше")


def render_images_tab(api_key: str):
    """🆕 Рендерит вкладку работы с изображениями с ИИ-удалением водяных знаков"""
    st.subheader("🖼️ ИИ-Редактор изображений")
    
    if not IMAGE_SUPPORT:
        st.error("⚠️ Установите необходимые библиотеки:")
        st.code("pip install pillow rembg numpy opencv-python-headless")
        return
    
    image_manager = st.session_state.image_manager
    
    img_tabs = st.tabs([
        "📥 Загрузка", "✏️ Редактирование", "🎨 Массовая обработка", 
        "💾 Результаты", "📊 Статистика"
    ])
    
    with img_tabs[0]:
        st.markdown("### 📥 Массовая загрузка изображений")
        st.info(f"💡 Поддерживается загрузка до {CONFIG.MAX_IMAGE_UPLOAD} файлов")
        
        uploaded_files = st.file_uploader(
            "Выберите изображения",
            type=list(CONFIG.SUPPORTED_IMAGE_FORMATS),
            accept_multiple_files=True,
            key="image_upload"
        )
        
        if uploaded_files:
            st.markdown(f"### 📊 Загружено файлов: {len(uploaded_files)}")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    file_size_mb = uploaded_file.size / (1024 * 1024)
                    if file_size_mb > CONFIG.MAX_IMAGE_SIZE_MB:
                        st.warning(f"⚠️ {uploaded_file.name} > {CONFIG.MAX_IMAGE_SIZE_MB}MB - пропущен")
                        continue
                    
                    image = Image.open(uploaded_file)
                    st.session_state.uploaded_images[uploaded_file.name] = image
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    status_text.text(f"Загрузка: {uploaded_file.name}")
                    
                except Exception as e:
                    st.error(f"❌ Ошибка {uploaded_file.name}: {e}")
            
            progress_bar.empty()
            status_text.empty()
            st.success(f"✅ Загружено {len(st.session_state.uploaded_images)} изображений")
            
            if st.session_state.uploaded_images:
                st.markdown("### 👁️ Предпросмотр")
                cols = st.columns(3)
                for idx, (filename, img) in enumerate(list(st.session_state.uploaded_images.items())[:6]):
                    with cols[idx % 3]:
                        st.image(img, caption=f"{filename}", use_container_width=True)
    
    with img_tabs[1]:
        st.markdown("### ✏️ Редактирование с ИИ")
        
        if not st.session_state.uploaded_images:
            st.info("💡 Загрузите изображения на вкладке 'Загрузка'")
        else:
            selected_filename = st.selectbox(
                "Выберите изображение",
                options=list(st.session_state.uploaded_images.keys()),
                key="selected_image_edit"
            )
            
            if selected_filename:
                original_image = st.session_state.uploaded_images[selected_filename]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Оригинал")
                    st.image(original_image, use_container_width=True)
                
                with col2:
                    st.markdown("#### 🎨 Операции с ИИ")
                    
                    operation = st.selectbox(
                        "Выберите операцию",
                        options=[
                            ('remove_background', '🎨 Удалить фон (rembg)'),
                            ('ai_remove_watermark', '🤖 ИИ-удаление водяного знака'),
                            ('remove_watermark', '💧 Базовое удаление водяного знака'),
                            ('resize', '📐 Изменить размер'),
                            ('enhance', '✨ Улучшить качество'),
                            ('convert_format', '📄 Конвертировать формат'),
                        ],
                        format_func=lambda x: x[1],
                        key="image_operation"
                    )
                    
                    params = {}
                    
                    if operation[0] == 'resize':
                        col_a, col_b = st.columns(2)
                        with col_a:
                            params['width'] = st.number_input("Ширина", min_value=1, value=original_image.size[0], key="img_width")
                        with col_b:
                            params['height'] = st.number_input("Высота", min_value=1, value=original_image.size[1], key="img_height")
                        params['maintain_aspect'] = st.checkbox("Сохранить пропорции", value=True, key="img_aspect")
                    
                    elif operation[0] == 'enhance':
                        params['brightness'] = st.slider("Яркость", 0.0, 2.0, 1.0, key="img_brightness")
                        params['contrast'] = st.slider("Контраст", 0.0, 2.0, 1.0, key="img_contrast")
                    
                    elif operation[0] == 'ai_remove_watermark':
                        params['description'] = st.text_area(
                            "Описание водяного знака:",
                            value="Удали водяной знак, сохранив основное изображение",
                            key="wm_desc",
                            help="Опишите где и как выглядит водяной знак для лучшего результата"
                        )
                    
                    if st.button("🚀 Применить", type="primary", use_container_width=True):
                        try:
                            with st.spinner("Обработка ИИ..."):
                                processed = image_manager._apply_operation(
                                    original_image, 
                                    ImageEditOperation(operation[0]), 
                                    params,
                                    api_key
                                )
                                
                                result_key = f"processed_{selected_filename}"
                                st.session_state.processed_images[result_key] = processed
                                
                                st.success("✅ Обработано!")
                                st.image(processed, caption="Результат", use_container_width=True)
                                
                                if st.button("💾 Сохранить результат", key=f"save_img_{selected_filename}"):
                                    save_path = IMAGES_DIR / result_key
                                    processed.save(save_path)
                                    st.success(f"✅ Сохранено в {save_path}")
                                    
                        except Exception as e:
                            st.error(f"❌ Ошибка: {e}")
    
    with img_tabs[2]:
        st.markdown("### 🎨 Массовая обработка")
        
        if not st.session_state.uploaded_images:
            st.info("💡 Загрузите изображения")
        else:
            st.markdown(f"📊 Доступно: {len(st.session_state.uploaded_images)}")
            
            batch_operation = st.selectbox(
                "Операция для всех",
                options=[
                    ('remove_background', '🎨 Удалить фон'),
                    ('remove_watermark', '💧 Удалить водяной знак'),
                    ('resize', '📐 Изменить размер'),
                    ('enhance', '✨ Улучшить'),
                ],
                format_func=lambda x: x[1],
                key="batch_operation"
            )
            
            batch_params = {}
            if batch_operation[0] == 'resize':
                col_a, col_b = st.columns(2)
                with col_a:
                    batch_params['width'] = st.number_input("Ширина", min_value=1, value=800, key="batch_width")
                with col_b:
                    batch_params['height'] = st.number_input("Высота", min_value=1, value=600, key="batch_height")
                batch_params['maintain_aspect'] = st.checkbox("Пропорции", value=True, key="batch_aspect")
            
            if st.button("🚀 Обработать все", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total, filename):
                    progress_bar.progress(current / total)
                    status_text.text(f"Обработка: {filename} ({current}/{total})")
                
                images_list = list(st.session_state.uploaded_images.items())
                
                results = image_manager.process_batch(
                    images_list,
                    ImageEditOperation(batch_operation[0]),
                    batch_params,
                    api_key,
                    update_progress
                )
                
                for filename, processed_img in results:
                    if processed_img is not None:
                        st.session_state.processed_images[f"batch_{filename}"] = processed_img
                
                progress_bar.empty()
                status_text.empty()
                st.success(f"✅ Обработано {len(results)} изображений")
                
                if st.button("💾 Сохранить все"):
                    saved_count = 0
                    for filename, img in st.session_state.processed_images.items():
                        if img is not None:
                            save_path = IMAGES_DIR / filename
                            img.save(save_path)
                            saved_count += 1
                    st.success(f"✅ Сохранено {saved_count} файлов в {IMAGES_DIR}")
    
    with img_tabs[3]:
        st.markdown("### 💾 Результаты")
        
        if not st.session_state.processed_images:
            st.info("💡 Нет обработанных изображений")
        else:
            st.markdown(f"📊 Всего: {len(st.session_state.processed_images)}")
            
            cols = st.columns(3)
            
            for idx, (filename, img) in enumerate(st.session_state.processed_images.items()):
                with cols[idx % 3]:
                    st.image(img, caption=filename, use_container_width=True)
                    
                    col_save, col_dl, col_del = st.columns(3)
                    
                    with col_save:
                        if st.button("💾", key=f"save_res_{idx}"):
                            save_path = IMAGES_DIR / filename
                            img.save(save_path)
                            st.success("✅")
                    
                    with col_dl:
                        img_bytes = BytesIO()
                        img.save(img_bytes, format='PNG')
                        st.download_button("📥", img_bytes, filename, "image/png", key=f"dl_res_{idx}")
                    
                    with col_del:
                        if st.button("🗑️", key=f"del_res_{idx}"):
                            del st.session_state.processed_images[filename]
                            st.rerun()
            
            if st.button("💾 Сохранить все в папку", use_container_width=True):
                saved_count = 0
                for filename, img in st.session_state.processed_images.items():
                    if img is not None:
                        save_path = IMAGES_DIR / filename
                        img.save(save_path)
                        saved_count += 1
                st.success(f"✅ Сохранено {saved_count} файлов в {IMAGES_DIR}")
    
    with img_tabs[4]:
        st.markdown("### 📊 Статистика")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Загружено", len(st.session_state.uploaded_images))
        with col2:
            st.metric("Обработано", len(st.session_state.processed_images))
        with col3:
            total_size = sum(img.size[0] * img.size[1] * 3 for img in st.session_state.uploaded_images.values())
            st.metric("Размер", f"{total_size / (1024*1024):.1f} MB")
        with col4:
            st.metric("Сохранено", len(list(IMAGES_DIR.glob("*"))) if IMAGES_DIR.exists() else 0)
        
        if st.session_state.uploaded_images:
            formats_count = {}
            for filename in st.session_state.uploaded_images.keys():
                ext = filename.split('.')[-1].upper()
                formats_count[ext] = formats_count.get(ext, 0) + 1
            
            df_formats = pd.DataFrame([
                {'Формат': fmt, 'Количество': count}
                for fmt, count in formats_count.items()
            ])
            
            fig = px.pie(df_formats, values='Количество', names='Формат', title="Форматы")
            st.plotly_chart(fig, use_container_width=True)


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
    
    ## 💬 Чат-интерфейс
    
    🆕 Обновления:
    - ✅ **Поле ввода всегда сверху** - как в современных мессенджерах
    - ✅ **Автоочистка** - поле очищается после отправки
    - ✅ **Цветовое оформление** - ваши сообщения справа, ответы агента слева
    
    ---
    
    ## 🖼️ ИИ-обработка изображений
    
    🆕 Новые возможности:
    - 📥 **Массовая загрузка** - до 10,000+ изображений
    - 🤖 **ИИ-удаление водяных знаков** - через Vision API с анализом контекста
    - 🎨 **Удаление фона** - автоматическое через rembg
    - ✨ **Улучшение качества** - яркость, контраст, четкость
    - 💾 **Локальное сохранение** - результаты в папке .workflow_data/processed_images
    
    ### Как работает ИИ-удаление водяных знаков:
    1. Изображение отправляется в ИИ с описанием задачи
    2. ИИ анализирует изображение и определяет положение водяного знака
    3. Возвращается стратегия удаления с координатами
    4. Применяется инпейнтинг (восстановление) только к нужной области
    5. Результат сохраняется с максимальным качеством
    
    💡 **Совет**: Для лучшего результата опишите водяной знак:
    - "Удали логотип в правом нижнем углу"
    - "Убери полупрозрачный текст по центру"
    - "Удали водяной знак, не затрагивая основное изображение"
    
    ---
    
    ## 🗂 Работа с таблицами
    
    ✅ Исправлена ошибка `sheet_names` в write_excel
    - ✏️ Редактирование данных в интерфейсе
    - 💾 Автосохранение изменений
    - 🤖 ИИ-трансформации на русском языке
    
    ---
    
    ## 🔧 Установка
    
    ```bash
    # Базовая установка
    pip install streamlit pandas openpyxl openai plotly requests pillow
    
    # Для работы с изображениями
    pip install rembg numpy opencv-python-headless
    
    # Для голосовых функций
    pip install SpeechRecognition gTTS
    
    # Запуск
    streamlit run workflow_builder.py
    ```
    
    ---
    
    *Workflow Builder Pro v9.3 • Монопоточная версия • © 2026*
    """)


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================
if __name__ == "__main__":
    main()
