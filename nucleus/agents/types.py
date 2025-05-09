"""
Базовые типы данных для вывода агентов nucleus: текст, изображение, аудио.
Все типы переопределяют преобразование к строке, хранят "сырой" и сериализованный вид.
"""

import os
import tempfile
import uuid
from PIL import Image

class NucleusAgentResult:
    """
    Базовый класс для результатов работы агентов.
    Предоставляет методы для получения сырого значения и строкового представления.
    """
    def __init__(self, value):
        self._data = value

    def __str__(self):
        return self.to_str()

    def to_raw(self):
        return self._data

    def to_str(self):
        return str(self._data)

class NucleusTextResult(NucleusAgentResult, str):
    """
    Результат текстового типа — наследует str и базовый класс.
    """
    def to_raw(self):
        return self._data

    def to_str(self):
        return str(self._data)

class NucleusImageResult(NucleusAgentResult):
    """
    Результат-изображение: хранит PIL.Image или путь к файлу.
    """
    def __init__(self, value):
        super().__init__(value)
        self._file_path = None
        self._img = None
        if isinstance(value, Image.Image):
            self._img = value
        elif isinstance(value, str) and os.path.exists(value):
            self._file_path = value
        else:
            raise TypeError(f"Не поддерживается тип для NucleusImageResult: {type(value)}")

    def to_raw(self):
        if self._img is not None:
            return self._img
        if self._file_path is not None:
            self._img = Image.open(self._file_path)
            return self._img

    def to_str(self):
        if self._file_path is not None:
            return self._file_path
        if self._img is not None:
            tmp_dir = tempfile.mkdtemp()
            self._file_path = os.path.join(tmp_dir, f"{uuid.uuid4()}.png")
            self._img.save(self._file_path, format="png")
            return self._file_path

class NucleusAudioResult(NucleusAgentResult, str):
    """
    Результат-аудио: путь к аудиофайлу и sample rate.
    """
    def __init__(self, value, rate=16000):
        super().__init__(value)
        self._file = value
        self.samplerate = rate

    def to_raw(self):
        return self._file

    def to_str(self):
        return self._file

def format_agent_output(result):
    """
    Приведение результата к подходящему типу-обёртке.
    """
    if isinstance(result, str):
        return NucleusTextResult(result)
    if isinstance(result, Image.Image):
        return NucleusImageResult(result)
    return result