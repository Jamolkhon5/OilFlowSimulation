#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import timedelta


class Config:
    # Базовые настройки приложения
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gazprom-neft-super-secret-key'
    DEBUG = False

    # Настройки базы данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///oil_filtration.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки загрузки файлов
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploads')
    RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'results')
    TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'temp')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB макс. размер файла

    # Настройки сессии
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Настройки моделирования
    DEFAULT_SIMULATION_DAYS = 100
    DEFAULT_TIME_STEP = 0.05
    DEFAULT_GRID_SIZE = 100

    # Ограничения параметров для пользовательского ввода
    PARAM_LIMITS = {
        'length': {'min': 10.0, 'max': 1000.0, 'default': 100.0, 'step': 10.0, 'unit': 'м'},
        'porosity': {'min': 0.05, 'max': 0.4, 'default': 0.2, 'step': 0.01, 'unit': 'д.ед.'},
        'mu_oil': {'min': 0.5, 'max': 50.0, 'default': 5.0, 'step': 0.5, 'unit': 'мПа·с'},
        'mu_water': {'min': 0.2, 'max': 5.0, 'default': 1.0, 'step': 0.1, 'unit': 'мПа·с'},
        'initial_water_saturation': {'min': 0.0, 'max': 0.5, 'default': 0.2, 'step': 0.05, 'unit': 'д.ед.'},
        'residual_oil_saturation': {'min': 0.0, 'max': 0.5, 'default': 0.2, 'step': 0.05, 'unit': 'д.ед.'},
        'entry_pressure': {'min': 0.1, 'max': 5.0, 'default': 1.0, 'step': 0.1, 'unit': 'МПа'},
        'pore_distribution_index': {'min': 0.5, 'max': 5.0, 'default': 1.5, 'step': 0.1, 'unit': 'отн.ед.'},
        'wettability_factor': {'min': 0.0, 'max': 1.0, 'default': 0.6, 'step': 0.05, 'unit': 'отн.ед.'},
        'fracture_porosity': {'min': 0.0, 'max': 0.1, 'default': 0.01, 'step': 0.005, 'unit': 'д.ед.'},
        'matrix_permeability': {'min': 0.01, 'max': 10.0, 'default': 0.1, 'step': 0.01, 'unit': 'мД'},
        'fracture_permeability': {'min': 10.0, 'max': 1000.0, 'default': 100.0, 'step': 10.0, 'unit': 'мД'},
        'shape_factor': {'min': 0.01, 'max': 1.0, 'default': 0.1, 'step': 0.01, 'unit': 'отн.ед.'}
    }

    # Параметры для разных типов пород
    ROCK_TYPE_PRESETS = {
        'Песчаник': {
            'porosity': 0.25,
            'entry_pressure': 0.5,
            'pore_distribution_index': 2.0,
            'wettability_factor': 0.7
        },
        'Известняк': {
            'porosity': 0.15,
            'entry_pressure': 1.2,
            'pore_distribution_index': 1.5,
            'wettability_factor': 0.5
        },
        'Доломит': {
            'porosity': 0.12,
            'entry_pressure': 1.5,
            'pore_distribution_index': 1.2,
            'wettability_factor': 0.4
        },
        'Трещиноватый известняк': {
            'porosity': 0.18,
            'fracture_porosity': 0.02,
            'matrix_permeability': 0.1,
            'fracture_permeability': 200.0,
            'entry_pressure': 1.3,
            'pore_distribution_index': 1.4,
            'wettability_factor': 0.45,
            'shape_factor': 0.15
        }
    }


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # В продакшене настройки могут отличаться
    # SECRET_KEY должен быть обязательно изменен
    # SQLALCHEMY_DATABASE_URI должен указывать на продакшен-БД