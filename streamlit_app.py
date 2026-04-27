#!/usr/bin/env python3
"""
Mass Watermark Remover - Ultimate Edition
Поддерживает: 9 методов авто-детекции, AI, 2000+ фото, параллельная обработка
"""

import streamlit as st
from streamlit_drawable_canvas import st_canvas
import cv2
import numpy as np
from PIL import Image
import zipfile
from pathlib import Path
import tempfile
import time
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from typing import Tuple, List, Dict, Optional
import io
import warnings
warnings.filterwarnings('ignore')

# Опциональные импорты для AI детекции
try:
    import torch
    from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
    TORCH_AVAILABLE = torch.cuda.is_available() or torch.cpu.is_available()
    CLIPSEG_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    CLIPSEG_AVAILABLE = False

try:
    from skimage import filters, morphology, exposure
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

try:
    from scipy import ndimage
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Настройки страницы
st.set_page_config(
    page_title="Ultimate Watermark Remover",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== НАСТРОЙКИ СТИЛЕЙ ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .info-box {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .ai-box {
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== ИНИЦИАЛИЗАЦИЯ СЕССИИ ==========
if 'master_mask' not in st.session_state:
    st.session_state.master_mask = None
if 'reference_image' not in st.session_state:
    st.session_state.reference_image = None
if 'auto_mask' not in st.session_state:
    st.session_state.auto_mask = None
if 'detection_history' not in st.session_state:
    st.session_state.detection_history = []
if 'processing_params' not in st.session_state:
    st.session_state.processing_params = {
        'algorithm': 'telea',
        'parallel_workers': 4,
        'quality': 'balanced'
    }

# ========== ПРОДВИНУТЫЕ МЕТОДЫ ДЕТЕКЦИИ ==========

class AdvancedWatermarkDetector:
    """9 продвинутых методов детекции водяных знаков"""
    
    def __init__(self):
        self.clipseg_model = None
        self.clipseg_processor = None
        self._init_ai_models()
    
    def _init_ai_models(self):
        """Инициализация AI моделей (ленивая загрузка)"""
        if CLIPSEG_AVAILABLE and TORCH_AVAILABLE and self.clipseg_model is None:
            try:
                self.clipseg_processor = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
                self.clipseg_model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")
                if torch.cuda.is_available():
                    self.clipseg_model = self.clipseg_model.cuda()
                st.success("✅ AI модели загружены (CLIPSeg)")
            except Exception as e:
                st.warning(f"⚠️ Не удалось загрузить AI модели: {e}")
    
    # Метод 1: Edge detection (Canny)
    @staticmethod
    def detect_by_edges(image: np.ndarray, sensitivity: int = 100) -> np.ndarray:
        """Обнаружение по краям - для любых водяных знаков"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, sensitivity, sensitivity * 2)
        
        # Морфологическое закрытие
        kernel = np.ones((10, 10), np.uint8)
        mask = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        return mask
    
    # Метод 2: Adaptive thresholding
    @staticmethod
    def detect_by_adaptive_threshold(image: np.ndarray, block_size: int = 15) -> np.ndarray:
        """Адаптивная пороговая обработка - для текста и логотипов"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Адаптивный порог
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, block_size, 2)
        
        # Морфологическая обработка
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=3)
        
        return mask
    
    # Метод 3: Color segmentation
    @staticmethod
    def detect_by_color(image: np.ndarray, color_range: str = 'white') -> np.ndarray:
        """Обнаружение по цвету"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        if color_range == 'white':
            lower = np.array([0, 0, 200])
            upper = np.array([180, 30, 255])
        elif color_range == 'black':
            lower = np.array([0, 0, 0])
            upper = np.array([180, 255, 50])
        elif color_range == 'red':
            lower1 = np.array([0, 50, 50])
            upper1 = np.array([10, 255, 255])
            lower2 = np.array([170, 50, 50])
            upper2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
            return mask
        else:  # semi-transparent
            lower = np.array([0, 0, 100])
            upper = np.array([180, 50, 200])
        
        mask = cv2.inRange(hsv, lower, upper)
        kernel = np.ones((7, 7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=3)
        
        return mask
    
    # Метод 4: Texture analysis (Local Binary Patterns)
    @staticmethod
    def detect_by_texture(image: np.ndarray) -> np.ndarray:
        """Обнаружение по текстуре - для полупрозрачных знаков"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # LBP - Local Binary Patterns
        lbp = np.zeros_like(gray)
        for i in range(1, gray.shape[0] - 1):
            for j in range(1, gray.shape[1] - 1):
                center = gray[i, j]
                code = 0
                code |= (gray[i-1, j-1] > center) << 7
                code |= (gray[i-1, j] > center) << 6
                code |= (gray[i-1, j+1] > center) << 5
                code |= (gray[i, j+1] > center) << 4
                code |= (gray[i+1, j+1] > center) << 3
                code |= (gray[i+1, j] > center) << 2
                code |= (gray[i+1, j-1] > center) << 1
                code |= (gray[i, j-1] > center) << 0
                lbp[i, j] = code
        
        # Выделяем необычные текстуры
        _, mask = cv2.threshold(lbp, 100, 255, cv2.THRESH_BINARY)
        kernel = np.ones((15, 15), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    # Метод 5: Frequency domain (FFT)
    @staticmethod
    def detect_by_frequency(image: np.ndarray) -> np.ndarray:
        """Обнаружение в частотной области - для повторяющихся паттернов"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # FFT
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1)
        
        # Выделяем высокие частоты (обычно водяные знаки)
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2
        mask_fft = np.zeros((rows, cols), np.uint8)
        mask_fft[crow-30:crow+30, ccol-30:ccol+30] = 255
        
        # Инвертируем
        fshift = fshift * (1 - mask_fft/255)
        f_ishift = np.fft.ifftshift(fshift)
        img_back = np.fft.ifft2(f_ishift)
        img_back = np.abs(img_back)
        
        # Нормализация
        img_back = (img_back - img_back.min()) / (img_back.max() - img_back.min()) * 255
        
        # Выделяем области отличий
        diff = cv2.absdiff(gray.astype(np.float32), img_back.astype(np.float32))
        _, mask = cv2.threshold(diff.astype(np.uint8), 30, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        return mask
    
    # Метод 6: Motion analysis (gradient)
    @staticmethod
    def detect_by_gradient(image: np.ndarray) -> np.ndarray:
        """Обнаружение по градиентам - для резких переходов"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Градиенты Собеля
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        # Нормализация
        magnitude = (magnitude - magnitude.min()) / (magnitude.max() - magnitude.min()) * 255
        
        # Выделяем сильные градиенты
        _, mask = cv2.threshold(magnitude.astype(np.uint8), 50, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=3)
        
        return mask
    
    # Метод 7: Morphological analysis
    @staticmethod
    def detect_by_morphology(image: np.ndarray) -> np.ndarray:
        """Морфологический анализ - для логотипов и символов"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Топ-хэт преобразование
        kernel = np.ones((15, 15), np.uint8)
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
        
        # Черное-топ-хэт
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        
        # Комбинация
        combined = cv2.addWeighted(tophat, 0.5, blackhat, 0.5, 0)
        
        # Пороговая обработка
        _, mask = cv2.threshold(combined, 30, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=4)
        
        return mask
    
    # Метод 8: Machine Learning (contour analysis)
    @staticmethod
    def detect_by_contours(image: np.ndarray, min_area: int = 500) -> np.ndarray:
        """Анализ контуров - для поиска компактных областей"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Эвристический порог
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Поиск контуров
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        mask = np.zeros_like(gray)
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area < area < image.shape[0] * image.shape[1] * 0.3:
                cv2.drawContours(mask, [contour], -1, 255, -1)
        
        kernel = np.ones((7, 7), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        return mask
    
    # Метод 9: AI CLIPSeg (если доступен)
    def detect_by_ai(self, image: np.ndarray, prompt: str = "watermark, logo, copyright") -> Optional[np.ndarray]:
        """Нейросетевая детекция через CLIPSeg"""
        if not CLIPSEG_AVAILABLE or not TORCH_AVAILABLE:
            return None
        
        self._init_ai_models()
        
        if self.clipseg_model is None:
            return None
        
        try:
            # Подготовка
            image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            inputs = self.clipseg_processor(
                text=[prompt],
                images=[image_pil],
                padding=True,
                return_tensors="pt"
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.clipseg_model(**inputs)
            
            # Конвертация в маску
            logits = outputs.logits
            if torch.cuda.is_available():
                logits = logits.cpu()
            
            mask = torch.sigmoid(logits).numpy()[0, 0]
            mask = (mask > 0.3).astype(np.uint8) * 255
            
            # Ресайз к оригинальному размеру
            if mask.shape != image.shape[:2]:
                mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
            
            kernel = np.ones((7, 7), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=3)
            
            return mask
            
        except Exception as e:
            st.warning(f"⚠️ Ошибка AI детекции: {e}")
            return None
    
    # Метод 9b: Background subtraction
    @staticmethod
    def detect_by_background(image: np.ndarray, blur_radius: int = 21) -> np.ndarray:
        """Вычитание фона - для полупрозрачных знаков"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Размытие фона
        blurred = cv2.GaussianBlur(gray, (blur_radius, blur_radius), 0)
        
        # Вычитание
        diff = cv2.absdiff(gray, blurred)
        
        # Нормализация
        diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        
        # Пороговая обработка
        _, mask = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=3)
        
        return mask

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def resize_mask_to_image(mask: np.ndarray, image_shape: Tuple[int, int]) -> np.ndarray:
    """Приводит маску к размеру изображения"""
    if mask.shape[:2] != image_shape[:2]:
        return cv2.resize(mask, (image_shape[1], image_shape[0]), interpolation=cv2.INTER_NEAREST)
    return mask

def remove_watermark_single(image: np.ndarray, mask: np.ndarray, algorithm: str = 'telea') -> np.ndarray:
    """Удаляет водяной знак с одного изображения"""
    mask_resized = resize_mask_to_image(mask, image.shape)
    
    if algorithm == 'telea':
        return cv2.inpaint(image, mask_resized, 3, cv2.INPAINT_TELEA)
    elif algorithm == 'ns':
        return cv2.inpaint(image, mask_resized, 3, cv2.INPAINT_NS)
    else:  # fast
        kernel = np.ones((5,5), np.uint8)
        mask_dilated = cv2.dilate(mask_resized, kernel, iterations=1)
        return cv2.inpaint(image, mask_dilated, 2, cv2.INPAINT_TELEA)

def process_single_image(args: tuple) -> Dict:
    """Для параллельной обработки"""
    img_path, mask, algorithm, output_path = args
    try:
        img = cv2.imread(str(img_path))
        if img is None:
            return {'success': False, 'path': str(img_path), 'error': 'Cannot read'}
        
        result = remove_watermark_single(img, mask, algorithm)
        cv2.imwrite(str(output_path), result)
        return {'success': True, 'path': str(img_path), 'output': str(output_path)}
    except Exception as e:
        return {'success': False, 'path': str(img_path), 'error': str(e)}

def combine_masks(masks: List[np.ndarray], method: str = 'union') -> np.ndarray:
    """Комбинирует несколько масок"""
    if not masks:
        return None
    
    combined = np.zeros_like(masks[0])
    
    if method == 'union':
        for mask in masks:
            combined = cv2.bitwise_or(combined, mask)
    elif method == 'intersection':
        combined = np.ones_like(masks[0]) * 255
        for mask in masks:
            combined = cv2.bitwise_and(combined, mask)
    else:  # weighted
        for mask in masks:
            combined = cv2.addWeighted(combined, 0.5, mask, 0.5, 0)
    
    return combined

def postprocess_mask(mask: np.ndarray, cleanup: bool = True, smooth: bool = True) -> np.ndarray:
    """Постобработка маски для улучшения качества"""
    if cleanup:
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # Удаление шума
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # Заполнение дыр
    
    if smooth:
        mask = cv2.medianBlur(mask, 5)
    
    return mask

def batch_process_parallel(image_paths: List[Path], mask: np.ndarray, 
                          algorithm: str, output_dir: Path, 
                          max_workers: int = 4, progress_callback=None) -> List[Dict]:
    """Параллельная пакетная обработка"""
    tasks = []
    for img_path in image_paths:
        output_path = output_dir / f"cleaned_{img_path.name}"
        tasks.append((img_path, mask, algorithm, output_path))
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_image, task): task for task in tasks}
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(tasks))
    
    return results

def create_zip_from_folder(folder_path: Path, zip_path: Path) -> None:
    """Создает ZIP архив из папки"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in folder_path.iterdir():
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                zf.write(file_path, file_path.name)

# ========== ЗАГОЛОВОК ==========
st.markdown('<div class="main-header">🚀 Ultimate Watermark Remover Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="info-box">💡 9 методов авто-детекции + AI + параллельная обработка 2000+ фото</div>', unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Настройки")
    
    st.session_state.processing_params['algorithm'] = st.selectbox(
        "Алгоритм удаления",
        ['telea', 'ns', 'fast'],
        index=0,
        format_func=lambda x: {
            'telea': '📐 Telea (средне)',
            'ns': '🎨 Navier-Stokes (качественно)',
            'fast': '⚡ Fast (быстро)'
        }[x]
    )
    
    st.session_state.processing_params['parallel_workers'] = st.slider(
        "🔄 Параллельных процессов",
        min_value=1,
        max_value=mp.cpu_count(),
        value=min(4, mp.cpu_count()),
        help="Больше = быстрее, но больше RAM"
    )
    
    st.divider()
    st.caption(f"💻 CPU ядер: {mp.cpu_count()}")
    st.caption(f"🧠 CUDA доступен: {torch.cuda.is_available() if TORCH_AVAILABLE else 'Нет'}")
    st.caption(f"🤖 CLIPSeg доступен: {CLIPSEG_AVAILABLE}")

# ========== ОСНОВНОЙ КОНТЕНТ ==========
tab1, tab2, tab3, tab4 = st.tabs(["🎨 Ручная маска", "🤖 Авто-детекция (9 методов)", "🔬 Сравнение методов", "⚡ Пакетная обработка"])

# TAB 1: РУЧНОЕ СОЗДАНИЕ МАСКИ
with tab1:
    st.header("📝 Создание маски вручную")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_ref = st.file_uploader(
            "📸 Загрузите изображение для разметки",
            type=['png', 'jpg', 'jpeg'],
            key="manual_upload"
        )
        
        if uploaded_ref:
            image = Image.open(uploaded_ref)
            st.session_state.reference_image = np.array(image)
            
            st.markdown("**🖌️ Рисуйте поверх водяных знаков**")
            
            col_a, col_b = st.columns(2)
            with col_a:
                brush_size = st.slider("Размер кисти", 5, 100, 30, key="brush_size")
            with col_b:
                draw_mode = st.selectbox("Режим", ["freedraw", "rect", "circle"], key="draw_mode")
            
            canvas = st_canvas(
                fill_color="rgba(255, 0, 0, 0.3)",
                stroke_width=brush_size,
                stroke_color="#FF0000",
                background_image=image,
                drawing_mode=draw_mode,
                key="watermark_canvas",
                height=400,
                width=600,
                display_toolbar=True
            )
            
            if st.button("💾 Сохранить маску", key="save_mask_manual"):
                if canvas.image_data is not None:
                    red_channel = canvas.image_data[:, :, 0] > 0
                    st.session_state.master_mask = red_channel.astype(np.uint8) * 255
                    st.success("✅ Маска сохранена!")
                    st.balloons()
    
    with col2:
        if st.session_state.master_mask is not None:
            st.markdown("### 👁️ Текущая маска")
            st.image(st.session_state.master_mask, caption="Области для удаления", use_column_width=True)
            st.metric("Площадь", f"{np.sum(st.session_state.master_mask > 0):,} px")
            
            if st.button("🗑️ Сбросить маску", key="reset_mask"):
                st.session_state.master_mask = None
                st.rerun()

# TAB 2: АВТО-ДЕТЕКЦИЯ (9 МЕТОДОВ)
with tab2:
    st.header("🤖 Продвинутая авто-детекция - 9 методов")
    
    uploaded_auto = st.file_uploader(
        "📸 Загрузите изображение с водяным знаком",
        type=['png', 'jpg', 'jpeg'],
        key="auto_upload"
    )
    
    if uploaded_auto:
        auto_image = Image.open(uploaded_auto)
        auto_np = np.array(auto_image)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(auto_image, caption="Исходное изображение", use_column_width=True)
        
        with col2:
            st.markdown("### Выберите метод детекции")
            
            detection_methods = {
                "1️⃣ Edge Detection (Края)": "edges",
                "2️⃣ Adaptive Threshold (Адаптивный порог)": "adaptive",
                "3️⃣ Color Segmentation (Цвет)": "color",
                "4️⃣ Texture Analysis (Текстура)": "texture",
                "5️⃣ Frequency Analysis (Частоты)": "frequency",
                "6️⃣ Gradient Analysis (Градиенты)": "gradient",
                "7️⃣ Morphological Analysis (Морфология)": "morphology",
                "8️⃣ Contour Analysis (Контуры)": "contours",
                "9️⃣ AI CLIPSeg (Нейросеть)": "ai",
                "🔟 Background Subtraction (Фон)": "background"
            }
            
            selected_method = st.selectbox(
                "Метод обнаружения",
                list(detection_methods.keys()),
                help="Каждый метод подходит для разных типов водяных знаков"
            )
            
            # Дополнительные параметры
            col_a, col_b = st.columns(2)
            
            detector = AdvancedWatermarkDetector()
            
            with col_a:
                sensitivity = st.slider("Чувствительность", 1, 200, 100, key="detect_sens")
            
            with col_b:
                post_clean = st.checkbox("Пост-обработка маски", True)
            
            # Параметры для конкретных методов
            if selected_method == "3️⃣ Color Segmentation (Цвет)":
                color_type = st.selectbox("Цвет", ["white", "black", "red", "semi-transparent"])
            else:
                color_type = None
            
            if st.button("🔍 Найти водяные знаки", key="detect_btn_advanced"):
                with st.spinner(f"Анализ методом {selected_method}..."):
                    method_key = detection_methods[selected_method]
                    
                    # Вызов метода
                    if method_key == "edges":
                        mask = detector.detect_by_edges(auto_np, sensitivity)
                    elif method_key == "adaptive":
                        mask = detector.detect_by_adaptive_threshold(auto_np)
                    elif method_key == "color":
                        mask = detector.detect_by_color(auto_np, color_type)
                    elif method_key == "texture":
                        mask = detector.detect_by_texture(auto_np)
                    elif method_key == "frequency":
                        mask = detector.detect_by_frequency(auto_np)
                    elif method_key == "gradient":
                        mask = detector.detect_by_gradient(auto_np)
                    elif method_key == "morphology":
                        mask = detector.detect_by_morphology(auto_np)
                    elif method_key == "contours":
                        mask = detector.detect_by_contours(auto_np)
                    elif method_key == "ai":
                        mask = detector.detect_by_ai(auto_np)
                    else:  # background
                        mask = detector.detect_by_background(auto_np)
                    
                    if mask is None:
                        st.error("❌ Метод недоступен. Установите torch и transformers для AI детекции")
                    else:
                        # Пост-обработка
                        if post_clean:
                            mask = postprocess_mask(mask)
                        
                        st.session_state.auto_mask = mask
                        
                        # Отображение результата
                        col_res1, col_res2 = st.columns(2)
                        
                        with col_res1:
                            st.image(mask, caption=f"Результат {selected_method}", use_column_width=True)
                            st.metric("Обнаружено пикселей", f"{np.sum(mask > 0):,}")
                        
                        with col_res2:
                            # Наложение маски на исходное
                            overlay = auto_np.copy()
                            overlay[mask > 0] = [255, 0, 0]
                            st.image(overlay, caption="Наложение маски", use_column_width=True)
                        
                        # Кнопка сохранения
                        if st.button("✅ Использовать эту маску", key="use_auto_mask_advanced"):
                            st.session_state.master_mask = mask
                            st.success("✅ Маска сохранена! Перейдите в 'Пакетную обработку'")
                            st.balloons()
                        
                        # Сохраняем в историю
                        st.session_state.detection_history.append({
                            'method': selected_method,
                            'area': int(np.sum(mask > 0)),
                            'timestamp': time.time()
                        })

# TAB 3: СРАВНЕНИЕ МЕТОДОВ
with tab3:
    st.header("🔬 Сравнение всех методов детекции")
    
    if uploaded_auto is None:
        st.info("👆 Сначала загрузите изображение на вкладке 'Авто-детекция'")
    else:
        st.markdown("### 📊 Сравнительный анализ")
        
        if st.button("🚀 Запустить все методы (может занять 30 сек)", key="compare_all"):
            detector = AdvancedWatermarkDetector()
            
            all_masks = {}
            methods_to_test = {
                "Edge Detection": lambda: detector.detect_by_edges(auto_np, 100),
                "Adaptive Threshold": lambda: detector.detect_by_adaptive_threshold(auto_np),
                "Color (White)": lambda: detector.detect_by_color(auto_np, 'white'),
                "Color (Black)": lambda: detector.detect_by_color(auto_np, 'black'),
                "Texture": lambda: detector.detect_by_texture(auto_np),
                "Frequency": lambda: detector.detect_by_frequency(auto_np),
                "Gradient": lambda: detector.detect_by_gradient(auto_np),
                "Morphology": lambda: detector.detect_by_morphology(auto_np),
                "Contours": lambda: detector.detect_by_contours(auto_np),
                "Background Sub": lambda: detector.detect_by_background(auto_np)
            }
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, (name, func) in enumerate(methods_to_test.items()):
                status_text.text(f"Тестирование: {name}")
                try:
                    mask = func()
                    mask = postprocess_mask(mask)
                    all_masks[name] = mask
                except Exception as e:
                    st.warning(f"Ошибка в {name}: {e}")
                    all_masks[name] = np.zeros_like(auto_np[:, :, 0])
                
                progress_bar.progress((i + 1) / len(methods_to_test))
            
            status_text.text("✅ Тестирование завершено!")
            
            # Отображение результатов в сетке
            cols = st.columns(3)
            for idx, (name, mask) in enumerate(all_masks.items()):
                with cols[idx % 3]:
                    st.markdown(f"**{name}**")
                    st.image(mask, use_column_width=True)
                    area = np.sum(mask > 0)
                    st.caption(f"Площадь: {area:,} px")
            
            # Комбинированная маска
            st.markdown("### 🎯 Комбинированный результат")
            
            col_c1, col_c2, col_c3 = st.columns(3)
            
            with col_c1:
                if st.button("Объединение (Union)"):
                    combined = combine_masks(list(all_masks.values()), 'union')
                    combined = postprocess_mask(combined)
                    st.image(combined, use_column_width=True)
                    
                    if st.button("✅ Использовать Union маску"):
                        st.session_state.master_mask = combined
                        st.success("✅ Маска сохранена!")
            
            with col_c2:
                if st.button("Пересечение (Intersection)"):
                    combined = combine_masks(list(all_masks.values()), 'intersection')
                    combined = postprocess_mask(combined)
                    st.image(combined, use_column_width=True)
                    
                    if st.button("✅ Использовать Intersection маску"):
                        st.session_state.master_mask = combined
                        st.success("✅ Маска сохранена!")
            
            with col_c3:
                if st.button("Взвешенное (Weighted)"):
                    combined = combine_masks(list(all_masks.values()), 'weighted')
                    combined = postprocess_mask(combined)
                    st.image(combined, use_column_width=True)
                    
                    if st.button("✅ Использовать Weighted маску"):
                        st.session_state.master_mask = combined
                        st.success("✅ Маска сохранена!")

# TAB 4: ПАКЕТНАЯ ОБРАБОТКА
with tab4:
    st.header("⚡ Пакетная обработка 2000+ изображений")
    
    if st.session_state.master_mask is None:
        st.markdown('<div class="warning-box">⚠️ Сначала создайте маску на вкладке "Ручная маска" или "Авто-детекция"</div>', unsafe_allow_html=True)
    else:
        mask_area = np.sum(st.session_state.master_mask > 0)
        st.markdown(f'<div class="success-box">✅ Маска готова! Будет обработано {mask_area:,} пикселей на каждом изображении</div>', unsafe_allow_html=True)
        
        # Статистика методов в истории
        if st.session_state.detection_history:
            st.markdown("### 📊 История детекции")
            for hist in st.session_state.detection_history[-3:]:
                st.caption(f"• {hist['method']}: {hist['area']:,} px")
        
        # Загрузка ZIP
        st.subheader("📦 Загрузите архив с изображениями")
        
        uploaded_zip = st.file_uploader(
            "ZIP архив с изображениями (поддерживаются JPG, PNG, BMP, TIFF)",
            type=['zip'],
            key="batch_zip"
        )
        
        if uploaded_zip:
            # Подсчет файлов
            with zipfile.ZipFile(uploaded_zip, 'r') as zf:
                file_list = [f for f in zf.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'))]
                file_count = len(file_list)
            
            st.info(f"📸 Найдено изображений: {file_count}")
            
            if file_count == 0:
                st.error("❌ В архиве нет поддерживаемых изображений")
            else:
                # Оценка времени
                est_time = file_count * 0.4 / st.session_state.processing_params['parallel_workers']
                st.caption(f"⏱️ Примерное время: {est_time:.1f} мин (алгоритм: {st.session_state.processing_params['algorithm']})")
                
                # Дополнительные настройки
                col_opt1, col_opt2 = st.columns(2)
                with col_opt1:
                    save_intermediate = st.checkbox("Сохранять промежуточные результаты", False)
                with col_opt2:
                    auto_cleanup = st.checkbox("Авто-очистка маски при обработке", True)
                
                if st.button("🚀 СТАРТ ОБРАБОТКИ", type="primary", use_container_width=True):
                    start_time = time.time()
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmp_path = Path(tmpdir)
                        
                        # Распаковка
                        status_text.text("📦 Распаковка архива...")
                        with zipfile.ZipFile(uploaded_zip, 'r') as zf:
                            zf.extractall(tmp_path)
                        
                        # Поиск изображений
                        image_paths = []
                        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']:
                            image_paths.extend(tmp_path.glob(ext))
                            image_paths.extend(tmp_path.glob(f"**/{ext}"))
                        
                        status_text.text(f"🖼️ Найдено {len(image_paths)} изображений")
                        
                        # Подготовка маски
                        final_mask = st.session_state.master_mask.copy()
                        if auto_cleanup:
                            final_mask = postprocess_mask(final_mask, cleanup=True, smooth=True)
                        
                        # Создание папки для результатов
                        output_dir = tmp_path / "watermark_free"
                        output_dir.mkdir(exist_ok=True)
                        
                        # Обработка
                        def update_progress(current, total):
                            progress_bar.progress(current / total)
                            status_text.text(f"🔄 Обработано: {current} из {total} ({current/total*100:.1f}%) | "
                                           f"Скорость: ~{current/(time.time()-start_time):.1f} фото/сек")
                        
                        results = batch_process_parallel(
                            image_paths=image_paths,
                            mask=final_mask,
                            algorithm=st.session_state.processing_params['algorithm'],
                            output_dir=output_dir,
                            max_workers=st.session_state.processing_params['parallel_workers'],
                            progress_callback=update_progress
                        )
                        
                        # Подсчет результатов
                        success_count = sum(1 for r in results if r['success'])
                        error_count = len(results) - success_count
                        
                        # Создание ZIP
                        status_text.text("📦 Создание ZIP архива...")
                        result_zip = tmp_path / "watermark_free_images.zip"
                        create_zip_from_folder(output_dir, result_zip)
                        
                        elapsed = time.time() - start_time
                        
                        # Финальная статистика
                        status_text.text("✅ Обработка завершена!")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("✅ Успешно", success_count)
                        with col2:
                            st.metric("❌ Ошибок", error_count)
                        with col3:
                            st.metric("⏱️ Время", f"{elapsed/60:.1f} мин")
                        with col4:
                            st.metric("⚡ Скорость", f"{success_count/elapsed:.2f} фото/сек")
                        
                        # Кнопка скачивания
                        with open(result_zip, "rb") as f:
                            st.download_button(
                                label="💾 Скачать все обработанные изображения (ZIP)",
                                data=f,
                                file_name="watermark_free_images.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                        
                        st.balloons()
                        st.success("🎉 Готово! Все изображения очищены от водяных знаков!")

# ========== FOOTER ==========
st.divider()
st.caption("""
    🚀 **Ultimate Watermark Remover Pro** | Версия 3.0
    - 9+ методов авто-детекции водяных знаков
    - AI детекция через CLIPSeg
    - Параллельная обработка 2000+ фото
    - Комбинирование масок
    - GPU поддержка
""")
