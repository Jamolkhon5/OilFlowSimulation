#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import pandas as pd
import numpy as np
from flask import current_app


def validate_email(email):
    """
    Проверяет корректность email-адреса

    Args:
        email (str): Email-адрес для проверки

    Returns:
        bool: True, если email корректный, иначе False
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username):
    """
    Проверяет корректность имени пользователя

    Args:
        username (str): Имя пользователя для проверки

    Returns:
        bool: True, если имя пользователя корректное, иначе False
    """
    pattern = r'^[a-zA-Z0-9_-]{3,20}$'
    return bool(re.match(pattern, username))


def validate_password(password):
    """
    Проверяет сложность пароля

    Args:
        password (str): Пароль для проверки

    Returns:
        tuple: (bool, str) - результат проверки и сообщение
    """
    # Проверяем длину пароля
    if len(password) < 8:
        return False, "Пароль должен содержать не менее 8 символов"

    # Проверяем наличие букв в нижнем регистре
    if not re.search(r'[a-z]', password):
        return False, "Пароль должен содержать хотя бы одну букву в нижнем регистре"

    # Проверяем наличие букв в верхнем регистре
    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать хотя бы одну букву в верхнем регистре"

    # Проверяем наличие цифр
    if not re.search(r'\d', password):
        return False, "Пароль должен содержать хотя бы одну цифру"

    return True, "Пароль соответствует требованиям"


def validate_model_parameters(parameters, model_type=None):
    """
    Проверяет корректность параметров модели

    Args:
        parameters (dict): Словарь параметров модели
        model_type (str, optional): Тип модели ('basic' или 'carbonate'). Defaults to None.

    Returns:
        tuple: (bool, dict) - результат проверки и словарь с ошибками
    """
    errors = {}
    param_limits = current_app.config['PARAM_LIMITS']

    # Проверяем каждый параметр
    for param, value in parameters.items():
        if param in param_limits:
            try:
                float_value = float(value)

                # Проверяем, что значение в допустимых пределах
                if float_value < param_limits[param]['min']:
                    errors[
                        param] = f"Значение меньше минимально допустимого: {param_limits[param]['min']} {param_limits[param]['unit']}"
                elif float_value > param_limits[param]['max']:
                    errors[
                        param] = f"Значение больше максимально допустимого: {param_limits[param]['max']} {param_limits[param]['unit']}"
            except ValueError:
                errors[param] = "Значение должно быть числом"

    # Проверяем обязательные параметры для выбранного типа модели
    if model_type == 'basic':
        required_params = ['length', 'porosity', 'mu_oil', 'mu_water', 'initial_water_saturation',
                           'residual_oil_saturation', 'entry_pressure', 'pore_distribution_index',
                           'wettability_factor']

        for param in required_params:
            if param not in parameters:
                errors[param] = "Обязательный параметр не указан"

    elif model_type == 'carbonate':
        required_params = ['length', 'porosity', 'mu_oil', 'mu_water', 'initial_water_saturation',
                           'residual_oil_saturation', 'entry_pressure', 'pore_distribution_index',
                           'wettability_factor', 'fracture_porosity', 'matrix_permeability',
                           'fracture_permeability', 'shape_factor']

        for param in required_params:
            if param not in parameters:
                errors[param] = "Обязательный параметр не указан"

    return len(errors) == 0, errors


def validate_rock_properties_file(file_path):
    """
    Проверяет корректность файла свойств породы

    Args:
        file_path (str): Путь к файлу

    Returns:
        tuple: (bool, str) - результат проверки и сообщение
    """
    try:
        df = pd.read_csv(file_path)

        # Проверяем наличие обязательных колонок
        required_columns = ['ID_Sample', 'Porosity_fr', 'Permeability_mD', 'Rock_Type']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return False, f"В файле отсутствуют следующие обязательные колонки: {', '.join(missing_columns)}"

        # Проверяем типы данных
        if not pd.api.types.is_numeric_dtype(df['Porosity_fr']):
            return False, "Колонка 'Porosity_fr' должна содержать числовые значения"

        if not pd.api.types.is_numeric_dtype(df['Permeability_mD']):
            return False, "Колонка 'Permeability_mD' должна содержать числовые значения"

        # Проверяем диапазон значений
        if df['Porosity_fr'].min() < 0 or df['Porosity_fr'].max() > 1:
            return False, "Значения в колонке 'Porosity_fr' должны быть в диапазоне от 0 до 1"

        if df['Permeability_mD'].min() < 0:
            return False, "Значения в колонке 'Permeability_mD' должны быть неотрицательными"

        return True, "Файл соответствует требованиям"
    except Exception as e:
        return False, f"Ошибка при проверке файла: {str(e)}"


def validate_capillary_pressure_file(file_path):
    """
    Проверяет корректность файла капиллярного давления

    Args:
        file_path (str): Путь к файлу

    Returns:
        tuple: (bool, str) - результат проверки и сообщение
    """
    try:
        df = pd.read_csv(file_path)

        # Проверяем наличие обязательных колонок
        required_columns = ['ID_Sample', 'Water_Saturation', 'Pc_Drainage_MPa']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return False, f"В файле отсутствуют следующие обязательные колонки: {', '.join(missing_columns)}"

        # Проверяем типы данных
        if not pd.api.types.is_numeric_dtype(df['Water_Saturation']):
            return False, "Колонка 'Water_Saturation' должна содержать числовые значения"

        if not pd.api.types.is_numeric_dtype(df['Pc_Drainage_MPa']):
            return False, "Колонка 'Pc_Drainage_MPa' должна содержать числовые значения"

        # Проверяем диапазон значений
        if df['Water_Saturation'].min() < 0 or df['Water_Saturation'].max() > 1:
            return False, "Значения в колонке 'Water_Saturation' должны быть в диапазоне от 0 до 1"

        # Проверяем, что для каждого образца есть не менее 3 точек
        samples = df['ID_Sample'].unique()
        for sample in samples:
            sample_data = df[df['ID_Sample'] == sample]
            if len(sample_data) < 3:
                return False, f"Для образца {sample} требуется не менее 3 точек"

        return True, "Файл соответствует требованиям"
    except Exception as e:
        return False, f"Ошибка при проверке файла: {str(e)}"


def validate_relative_perm_file(file_path):
    """
    Проверяет корректность файла относительной проницаемости

    Args:
        file_path (str): Путь к файлу

    Returns:
        tuple: (bool, str) - результат проверки и сообщение
    """
    try:
        df = pd.read_csv(file_path)

        # Проверяем наличие обязательных колонок
        required_columns = ['ID_Sample', 'Water_Saturation', 'Krw_Drainage', 'Kro_Drainage']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return False, f"В файле отсутствуют следующие обязательные колонки: {', '.join(missing_columns)}"

        # Проверяем типы данных
        for col in ['Water_Saturation', 'Krw_Drainage', 'Kro_Drainage']:
            if not pd.api.types.is_numeric_dtype(df[col]):
                return False, f"Колонка '{col}' должна содержать числовые значения"

        # Проверяем диапазон значений
        if df['Water_Saturation'].min() < 0 or df['Water_Saturation'].max() > 1:
            return False, "Значения в колонке 'Water_Saturation' должны быть в диапазоне от 0 до 1"

        if df['Krw_Drainage'].min() < 0 or df['Krw_Drainage'].max() > 1:
            return False, "Значения в колонке 'Krw_Drainage' должны быть в диапазоне от 0 до 1"

        if df['Kro_Drainage'].min() < 0 or df['Kro_Drainage'].max() > 1:
            return False, "Значения в колонке 'Kro_Drainage' должны быть в диапазоне от 0 до 1"

        # Проверяем, что для каждого образца есть не менее 3 точек
        samples = df['ID_Sample'].unique()
        for sample in samples:
            sample_data = df[df['ID_Sample'] == sample]
            if len(sample_data) < 3:
                return False, f"Для образца {sample} требуется не менее 3 точек"

        return True, "Файл соответствует требованиям"
    except Exception as e:
        return False, f"Ошибка при проверке файла: {str(e)}"


def validate_pvt_data_file(file_path):
    """
    Проверяет корректность файла PVT-данных

    Args:
        file_path (str): Путь к файлу

    Returns:
        tuple: (bool, str) - результат проверки и сообщение
    """
    try:
        df = pd.read_csv(file_path)

        # Проверяем наличие обязательных колонок
        required_columns = ['Pressure_MPa', 'Oil_Viscosity_cP']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return False, f"В файле отсутствуют следующие обязательные колонки: {', '.join(missing_columns)}"

        # Проверяем типы данных
        for col in required_columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                return False, f"Колонка '{col}' должна содержать числовые значения"

        # Проверяем диапазон значений
        if df['Pressure_MPa'].min() <= 0:
            return False, "Значения в колонке 'Pressure_MPa' должны быть положительными"

        if df['Oil_Viscosity_cP'].min() <= 0:
            return False, "Значения в колонке 'Oil_Viscosity_cP' должны быть положительными"

        return True, "Файл соответствует требованиям"
    except Exception as e:
        return False, f"Ошибка при проверке файла: {str(e)}"


def validate_production_data_file(file_path):
    """
    Проверяет корректность файла данных добычи

    Args:
        file_path (str): Путь к файлу

    Returns:
        tuple: (bool, str) - результат проверки и сообщение
    """
    try:
        df = pd.read_csv(file_path)

        # Проверяем наличие обязательных колонок
        required_columns = ['Date', 'Oil_Rate_m3_day', 'Water_Rate_m3_day']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return False, f"В файле отсутствуют следующие обязательные колонки: {', '.join(missing_columns)}"

        # Проверяем типы данных
        try:
            # Пробуем преобразовать даты
            pd.to_datetime(df['Date'])
        except:
            return False, "Колонка 'Date' должна содержать даты в формате YYYY-MM-DD"

        for col in ['Oil_Rate_m3_day', 'Water_Rate_m3_day']:
            if not pd.api.types.is_numeric_dtype(df[col]):
                return False, f"Колонка '{col}' должна содержать числовые значения"

        # Проверяем диапазон значений
        if df['Oil_Rate_m3_day'].min() < 0:
            return False, "Значения в колонке 'Oil_Rate_m3_day' должны быть неотрицательными"

        if df['Water_Rate_m3_day'].min() < 0:
            return False, "Значения в колонке 'Water_Rate_m3_day' должны быть неотрицательными"

        return True, "Файл соответствует требованиям"
    except Exception as e:
        return False, f"Ошибка при проверке файла: {str(e)}"