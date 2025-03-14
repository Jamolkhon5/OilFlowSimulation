#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np


def allowed_file(filename, allowed_extensions):
    """
    Проверяет, что расширение файла разрешено

    Args:
        filename (str): Имя файла
        allowed_extensions (set): Набор разрешенных расширений

    Returns:
        bool: True, если расширение файла разрешено, иначе False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder, project_id):
    """
    Сохраняет загруженный файл в указанную директорию

    Args:
        file (FileStorage): Объект загруженного файла
        upload_folder (str): Путь к директории для сохранения
        project_id (int): ID проекта

    Returns:
        tuple: (str, str) - (Имя сохраненного файла, полный путь) или (None, None) в случае ошибки
    """
    try:
        print(f"Сохранение файла {file.filename} в папку {upload_folder}")

        # Проверка существования директории
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            print(f"Создана директория: {upload_folder}")

        # Получаем безопасное имя файла
        filename = secure_filename(file.filename)

        # Добавляем уникальный идентификатор к имени файла
        unique_id = str(uuid.uuid4())[:8]
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{unique_id}{ext}"

        # Создаем папку для проекта, если она не существует
        project_folder = os.path.join(upload_folder, str(project_id))
        os.makedirs(project_folder, exist_ok=True)
        print(f"Проверка существования директории проекта: {os.path.exists(project_folder)}")

        # Полный путь к файлу
        file_path = os.path.join(project_folder, unique_filename)

        # Проверка на доступность пути для записи
        try:
            with open(file_path, 'wb') as f:
                f.write(b'test')
            os.remove(file_path)
            print(f"Путь {file_path} доступен для записи")
        except Exception as e:
            print(f"Ошибка при проверке доступности пути: {str(e)}")
            # Пробуем альтернативный путь в текущей директории
            current_dir = os.getcwd()
            file_path = os.path.join(current_dir, 'temp_uploads', unique_filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            print(f"Используем альтернативный путь: {file_path}")

        # Сохраняем файл
        print(f"Попытка сохранения файла по пути: {file_path}")
        file.save(file_path)

        # Проверяем, что файл сохранен и существует
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"Файл успешно сохранен по пути: {file_path}. Размер: {file_size} байт")
            # Выводим содержимое директории для отладки
            dir_path = os.path.dirname(file_path)
            print(f"Содержимое директории {dir_path}: {os.listdir(dir_path)}")
        else:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: Файл не был сохранен по пути {file_path}")
            return None, None

        return unique_filename, file_path
    except Exception as e:
        import traceback
        print(f"Ошибка при сохранении файла: {str(e)}")
        traceback.print_exc()
        return None, None


def read_csv_file(file_path, encoding='utf-8'):
    """
    Читает CSV-файл и возвращает DataFrame

    Args:
        file_path (str): Путь к файлу
        encoding (str, optional): Кодировка файла. Defaults to 'utf-8'.

    Returns:
        pandas.DataFrame: DataFrame с данными из файла или None в случае ошибки
    """
    try:
        print(f"Попытка чтения CSV файла: {file_path}")

        # Проверяем, существует ли файл
        if not os.path.exists(file_path):
            print(f"Ошибка: файл не существует по пути {file_path}")
            return None

        # Пробуем различные варианты чтения CSV
        encodings = ['utf-8', 'cp1251', 'cp1252', 'latin1']
        separators = [',', ';', '\t']

        for enc in encodings:
            for sep in separators:
                try:
                    print(f"Пробуем прочитать с кодировкой {enc} и разделителем '{sep}'")
                    df = pd.read_csv(file_path, encoding=enc, sep=sep, quotechar='"', escapechar='\\')

                    # Проверяем, что данные прочитаны корректно (более 1 столбца)
                    if len(df.columns) > 1:
                        print(f"Успешно прочитан файл с кодировкой {enc} и разделителем '{sep}'")
                        print(f"Размер данных: {df.shape}, колонки: {list(df.columns)}")
                        return df
                    else:
                        print(f"Прочитан только один столбец, вероятно, неверный разделитель")
                except Exception as e:
                    print(f"Ошибка чтения с кодировкой {enc} и разделителем '{sep}': {str(e)}")
                    continue

        # Если не удалось прочитать как CSV, пробуем прочитать как текстовый файл
        print("Не удалось прочитать как CSV, пробуем прочитать как текстовый файл")
        with open(file_path, 'rb') as f:
            content = f.read(1024)  # Читаем первые 1024 байта

        # Определяем кодировку
        detected_encoding = 'utf-8'  # По умолчанию
        try:
            import chardet
            result = chardet.detect(content)
            detected_encoding = result['encoding']
            print(f"Обнаружена кодировка: {detected_encoding} с уверенностью {result['confidence']}")
        except ImportError:
            print("Модуль chardet не установлен, используем стандартную кодировку")

        # Выводим первые строки файла для диагностики
        try:
            with open(file_path, 'r', encoding=detected_encoding, errors='replace') as f:
                first_lines = [next(f) for _ in range(5)]
            print(f"Первые 5 строк файла:")
            for line in first_lines:
                print(line.strip())

            # Пробуем определить разделитель
            possible_seps = [sep for sep in separators if any(sep in line for line in first_lines)]
            print(f"Возможные разделители: {possible_seps}")

        except Exception as e:
            print(f"Ошибка при чтении первых строк файла: {str(e)}")

        print("Не удалось прочитать файл как CSV")
        return None

    except Exception as e:
        print(f"Неожиданная ошибка при чтении файла {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def read_excel_file(file_path):
    """
    Читает Excel-файл и возвращает DataFrame

    Args:
        file_path (str): Путь к файлу

    Returns:
        pandas.DataFrame: DataFrame с данными из файла или None в случае ошибки
    """
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {str(e)}")
        return None


def save_dataframe_to_csv(df, file_path, encoding='utf-8'):
    """
    Сохраняет DataFrame в CSV-файл

    Args:
        df (pandas.DataFrame): DataFrame для сохранения
        file_path (str): Путь для сохранения файла
        encoding (str, optional): Кодировка файла. Defaults to 'utf-8'.

    Returns:
        bool: True, если сохранение прошло успешно, иначе False
    """
    try:
        df.to_csv(file_path, index=False, encoding=encoding)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении DataFrame в файл {file_path}: {str(e)}")
        return False


def extract_data_from_file(file_path, file_type):
    """
    Извлекает данные из файла в зависимости от его типа

    Args:
        file_path (str): Путь к файлу
        file_type (str): Тип файла ('rock_properties', 'capillary_pressure', etc.)

    Returns:
        dict: Словарь с извлеченными данными или None в случае ошибки
    """
    try:
        # Определяем расширение файла
        ext = os.path.splitext(file_path)[1].lower()

        # Читаем файл в зависимости от расширения
        if ext == '.csv':
            df = read_csv_file(file_path)
        elif ext in ['.xlsx', '.xls']:
            df = read_excel_file(file_path)
        else:
            print(f"Неподдерживаемое расширение файла: {ext}")
            return None

        if df is None:
            return None

        # Проверим и преобразуем колонки, если нужно
        if file_type == 'rock_properties':
            # Проверяем наличие обязательных колонок или близких к ним вариантов
            required_columns = ['ID_Sample', 'Porosity_fr', 'Permeability_mD', 'Rock_Type']
            column_mapping = {}

            for req_col in required_columns:
                if req_col in df.columns:
                    column_mapping[req_col] = req_col
                else:
                    # Ищем похожие колонки
                    for col in df.columns:
                        if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                            column_mapping[req_col] = col
                            break

            # Если не нашли соответствия для обязательных колонок
            missing_cols = [col for col in required_columns if col not in column_mapping]
            if missing_cols:
                print(f"В файле отсутствуют обязательные колонки: {missing_cols}")
                return None

            # Переименовываем колонки, если нужно
            if column_mapping:
                reversed_mapping = {v: k for k, v in column_mapping.items() if v != k}
                if reversed_mapping:
                    df = df.rename(columns=reversed_mapping)

            # Извлекаем средние значения по каждому типу породы
            rock_types = df['Rock_Type'].unique()
            data = {}

            for rock_type in rock_types:
                rock_data = df[df['Rock_Type'] == rock_type]
                data[rock_type] = {
                    'porosity': float(rock_data['Porosity_fr'].mean()),
                    'permeability': float(rock_data['Permeability_mD'].mean())
                }

                # Добавляем смачиваемость, если она есть
                if 'Wettability_Index' in df.columns:
                    data[rock_type]['wettability_index'] = float(rock_data['Wettability_Index'].mean())

            return data

        elif file_type == 'capillary_pressure':
            # Проверяем наличие обязательных колонок или их вариантов
            required_columns = ['ID_Sample', 'Water_Saturation', 'Pc_Drainage_MPa']
            column_mapping = {}

            for req_col in required_columns:
                if req_col in df.columns:
                    column_mapping[req_col] = req_col
                else:
                    # Ищем похожие колонки
                    for col in df.columns:
                        if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                            column_mapping[req_col] = col
                            break

            # Если не нашли соответствия для обязательных колонок
            missing_cols = [col for col in required_columns if col not in column_mapping]
            if missing_cols:
                print(f"В файле отсутствуют обязательные колонки: {missing_cols}")
                return None

            # Переименовываем колонки, если нужно
            if column_mapping:
                reversed_mapping = {v: k for k, v in column_mapping.items() if v != k}
                if reversed_mapping:
                    df = df.rename(columns=reversed_mapping)

            # Группируем данные по образцам
            samples = df['ID_Sample'].unique()
            data = {}

            for sample in samples:
                sample_data = df[df['ID_Sample'] == sample]
                # Преобразуем в числовой формат, если нужно
                sw_values = pd.to_numeric(sample_data['Water_Saturation'], errors='coerce')
                pc_values = pd.to_numeric(sample_data['Pc_Drainage_MPa'], errors='coerce')

                # Пропускаем образцы с неполными данными
                if sw_values.isna().any() or pc_values.isna().any():
                    print(f"Пропускаем образец {sample} из-за неполных данных")
                    continue

                data[sample] = {
                    'Sw': sw_values.tolist(),
                    'Pc': pc_values.tolist()
                }

            return data

        elif file_type == 'relative_perm':
            # Проверяем наличие обязательных колонок или их вариантов
            required_columns = ['ID_Sample', 'Water_Saturation', 'Krw_Drainage', 'Kro_Drainage']
            column_mapping = {}

            for req_col in required_columns:
                if req_col in df.columns:
                    column_mapping[req_col] = req_col
                else:
                    # Ищем похожие колонки
                    for col in df.columns:
                        if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                            column_mapping[req_col] = col
                            break

            # Если не нашли соответствия для обязательных колонок
            missing_cols = [col for col in required_columns if col not in column_mapping]
            if missing_cols:
                print(f"В файле отсутствуют обязательные колонки: {missing_cols}")
                return None

            # Переименовываем колонки, если нужно
            if column_mapping:
                reversed_mapping = {v: k for k, v in column_mapping.items() if v != k}
                if reversed_mapping:
                    df = df.rename(columns=reversed_mapping)

            # Группируем данные по образцам
            samples = df['ID_Sample'].unique()
            data = {}

            for sample in samples:
                sample_data = df[df['ID_Sample'] == sample]
                # Преобразуем в числовой формат, если нужно
                sw_values = pd.to_numeric(sample_data['Water_Saturation'], errors='coerce')
                krw_values = pd.to_numeric(sample_data['Krw_Drainage'], errors='coerce')
                kro_values = pd.to_numeric(sample_data['Kro_Drainage'], errors='coerce')

                # Пропускаем образцы с неполными данными
                if sw_values.isna().any() or krw_values.isna().any() or kro_values.isna().any():
                    print(f"Пропускаем образец {sample} из-за неполных данных")
                    continue

                data[sample] = {
                    'Sw': sw_values.tolist(),
                    'Krw': krw_values.tolist(),
                    'Kro': kro_values.tolist()
                }

            return data

        elif file_type == 'pvt_data':
            # Проверяем наличие обязательных колонок или их вариантов
            required_columns = ['Pressure_MPa', 'Oil_Viscosity_cP']
            column_mapping = {}

            for req_col in required_columns:
                if req_col in df.columns:
                    column_mapping[req_col] = req_col
                else:
                    # Ищем похожие колонки
                    for col in df.columns:
                        if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                            column_mapping[req_col] = col
                            break

            # Если не нашли соответствия для обязательных колонок
            missing_cols = [col for col in required_columns if col not in column_mapping]
            if missing_cols:
                print(f"В файле отсутствуют обязательные колонки: {missing_cols}")
                return None

            # Переименовываем колонки, если нужно
            if column_mapping:
                reversed_mapping = {v: k for k, v in column_mapping.items() if v != k}
                if reversed_mapping:
                    df = df.rename(columns=reversed_mapping)

            # Преобразуем колонки в числовой формат
            for col in required_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Отбрасываем строки с отсутствующими значениями
            df = df.dropna(subset=required_columns)

            # Извлекаем данные
            data = {
                'Pressure': df['Pressure_MPa'].tolist(),
                'Oil_Viscosity': df['Oil_Viscosity_cP'].tolist()
            }

            # Добавляем плотность нефти и газа, если они есть
            if 'Oil_Density_kg_m3' in df.columns:
                data['Oil_Density'] = pd.to_numeric(df['Oil_Density_kg_m3'], errors='coerce').dropna().tolist()
            if 'Gas_Density_kg_m3' in df.columns:
                data['Gas_Density'] = pd.to_numeric(df['Gas_Density_kg_m3'], errors='coerce').dropna().tolist()

            return data

        elif file_type == 'production_data':
            # Проверяем наличие обязательных колонок или их вариантов
            required_columns = ['Date', 'Oil_Rate_m3_day', 'Water_Rate_m3_day']
            column_mapping = {}

            for req_col in required_columns:
                if req_col in df.columns:
                    column_mapping[req_col] = req_col
                else:
                    # Ищем похожие колонки
                    for col in df.columns:
                        if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                            column_mapping[req_col] = col
                            break

            # Если не нашли соответствия для обязательных колонок
            missing_cols = [col for col in required_columns if col not in column_mapping]
            if missing_cols:
                print(f"В файле отсутствуют обязательные колонки: {missing_cols}")
                return None

            # Переименовываем колонки, если нужно
            if column_mapping:
                reversed_mapping = {v: k for k, v in column_mapping.items() if v != k}
                if reversed_mapping:
                    df = df.rename(columns=reversed_mapping)

            # Преобразуем числовые колонки в правильный формат
            numeric_cols = ['Oil_Rate_m3_day', 'Water_Rate_m3_day']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Пытаемся преобразовать дату в правильный формат
            try:
                df['Date'] = pd.to_datetime(df['Date'])
                date_list = df['Date'].dt.strftime('%Y-%m-%d').tolist()
            except Exception as e:
                print(f"Ошибка при преобразовании дат: {str(e)}")
                date_list = df['Date'].tolist()

            # Отбрасываем строки с отсутствующими значениями
            df = df.dropna(subset=numeric_cols)

            # Извлекаем данные
            data = {
                'Date': date_list,
                'Oil_Rate': df['Oil_Rate_m3_day'].tolist(),
                'Water_Rate': df['Water_Rate_m3_day'].tolist()
            }

            # Добавляем дополнительные данные, если они есть
            if 'Gas_Rate_m3_day' in df.columns:
                data['Gas_Rate'] = pd.to_numeric(df['Gas_Rate_m3_day'], errors='coerce').dropna().tolist()
            if 'Bottom_Hole_Pressure_MPa' in df.columns:
                data['BHP'] = pd.to_numeric(df['Bottom_Hole_Pressure_MPa'], errors='coerce').dropna().tolist()

            return data

        else:
            print(f"Неизвестный тип файла: {file_type}")
            return None

    except Exception as e:
        print(f"Ошибка при извлечении данных из файла {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None