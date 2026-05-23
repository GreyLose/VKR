# utils/sequence_io.py
"""
Модуль для сохранения и загрузки числовых последовательностей.
Поддерживает форматы: TXT, CSV, BIN, JSON.
"""

import json
import csv
from pathlib import Path
from typing import List, Union, Literal

FormatType = Literal["txt", "csv", "bin", "json"]

def save_sequence(
    sequence: List[int],
    filepath: Union[str, Path],
    format: FormatType = "txt",
    bits_only: bool = False
) -> Path:
    """
    Сохраняет последовательность в файл.
    
    :param sequence: Список целых чисел
    :param filepath: Путь к файлу
    :param format: Формат файла (txt/csv/bin/json)
    :param bits_only: Если True, сохраняются только младшие биты (0/1)
    :return: Путь к сохранённому файлу
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Преобразование в биты при необходимости
    data = [x & 1 for x in sequence] if bits_only else sequence
    
    if format == "txt":
        # Простой текстовый формат: одно число в строке
        with open(filepath, "w", encoding="utf-8") as f:
            for num in data:
                f.write(f"{num}\n")
                
    elif format == "csv":
        # CSV с метаданными в первой строке
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["# sequence_length", len(data)])
            writer.writerow(["# format", "integers" if not bits_only else "bits"])
            writer.writerow(["# data"])
            for num in data:
                writer.writerow([num])
                
    elif format == "bin":
        # Бинарный формат (4 байта на число, little-endian)
        with open(filepath, "wb") as f:
            for num in data:
                f.write(num.to_bytes(4, byteorder="little", signed=False))
                
    elif format == "json":
        # JSON с метаданными
        output = {
            "metadata": {
                "length": len(data),
                "type": "integers" if not bits_only else "bits",
                "min": min(data) if data else None,
                "max": max(data) if data else None
            },
            "data": data
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
    
    return filepath


def load_sequence(
    filepath: Union[str, Path],
    format: FormatType = None
) -> List[int]:
    """
    Загружает последовательность из файла.
    
    :param filepath: Путь к файлу
    :param format: Формат файла (если None, определяется по расширению)
    :return: Список целых чисел
    """
    filepath = Path(filepath)
    
    if format is None:
        format = filepath.suffix.lstrip(".").lower()
        if format == "":
            format = "txt"  # default
    
    if format == "txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return [int(line.strip()) for line in f if line.strip() and not line.startswith("#")]
            
    elif format == "csv":
        data = []
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].startswith("#"):
                    continue
                if row:
                    data.append(int(row[0]))
        return data
        
    elif format == "bin":
        data = []
        with open(filepath, "rb") as f:
            while chunk := f.read(4):
                if len(chunk) == 4:
                    data.append(int.from_bytes(chunk, byteorder="little", signed=False))
        return data
        
    elif format == "json":
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
            return content.get("data", content if isinstance(content, list) else [])
    
    raise ValueError(f"Неподдерживаемый формат: {format}")


def get_sequence_info(sequence: List[int]) -> dict:
    """
    Возвращает статистику по последовательности.
    """
    if not sequence:
        return {"error": "Пустая последовательность"}
    
    bits = [x & 1 for x in sequence]
    return {
        "length": len(sequence),
        "min": min(sequence),
        "max": max(sequence),
        "mean": sum(sequence) / len(sequence),
        "bits_ones_ratio": sum(bits) / len(bits),
        "unique_values": len(set(sequence)),
        "first_10": sequence[:10],
        "last_10": sequence[-10:]
    }