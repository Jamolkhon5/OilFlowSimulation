#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import json
from extensions import db


class Project(db.Model):
    """Модель проекта для хранения пользовательских проектов моделирования"""

    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    model_type = db.Column(db.String(64), nullable=False)  # 'basic' или 'carbonate'
    rock_type = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Отношение один-к-одному с данными проекта
    data = db.relationship('ProjectData', backref='project', uselist=False, cascade='all, delete-orphan')

    # Отношение один-ко-многим с результатами
    results = db.relationship('ProjectResult', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    def get_model_parameters(self):
        """Возвращает параметры модели в виде словаря"""
        if self.data and self.data.model_parameters:
            return json.loads(self.data.model_parameters)
        return {}

    def get_results_data(self):
        """Возвращает данные последнего результата моделирования"""
        results = self.results.order_by(ProjectResult.created_at.desc()).first()
        if results and results.result_data:
            return json.loads(results.result_data)
        return None

    def __repr__(self):
        return f'<Project {self.name}>'


class ProjectData(db.Model):
    """Модель для хранения данных проекта"""

    __tablename__ = 'project_data'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, unique=True)
    model_parameters = db.Column(db.Text)  # JSON-строка с параметрами модели
    rock_properties_file = db.Column(db.String(255))  # путь к файлу свойств породы
    capillary_pressure_file = db.Column(db.String(255))  # путь к файлу капиллярного давления
    relative_perm_file = db.Column(db.String(255))  # путь к файлу относительной проницаемости
    pvt_data_file = db.Column(db.String(255))  # путь к файлу PVT-данных
    production_data_file = db.Column(db.String(255))  # путь к файлу данных добычи
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_uploaded_files(self):
        """Возвращает список загруженных файлов"""
        files = {}
        if self.rock_properties_file:
            files['rock_properties'] = self.rock_properties_file
        if self.capillary_pressure_file:
            files['capillary_pressure'] = self.capillary_pressure_file
        if self.relative_perm_file:
            files['relative_perm'] = self.relative_perm_file
        if self.pvt_data_file:
            files['pvt_data'] = self.pvt_data_file
        if self.production_data_file:
            files['production_data'] = self.production_data_file
        return files

    def __repr__(self):
        return f'<ProjectData for project_id={self.project_id}>'


class ProjectResult(db.Model):
    """Модель для хранения результатов моделирования"""

    __tablename__ = 'project_results'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    run_date = db.Column(db.DateTime, default=datetime.utcnow)
    result_data = db.Column(db.Text)  # JSON-строка с данными результатов
    runtime = db.Column(db.Float)  # время выполнения в секундах
    status = db.Column(db.String(64), default='success')  # success, error, warning
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def save_results(self, results_dict, runtime):
        """Сохраняет результаты моделирования"""
        self.result_data = json.dumps(results_dict)
        self.runtime = runtime
        db.session.commit()

    def get_results(self):
        """Возвращает результаты моделирования в виде словаря"""
        if self.result_data:
            try:
                result_data = json.loads(self.result_data)

                # Проверяем наличие ключа visualizations и корректируем если нужно
                if 'visualizations' not in result_data or not result_data['visualizations']:
                    # Добавляем все возможные визуализации
                    result_data['visualizations'] = {
                        'saturation_profiles': True,
                        'saturation_difference': True,
                        'recovery_factor': True,
                        'breakthrough_time': True,
                        'saturation_evolution': True,
                        'capillary_pressure': True,
                        'fractional_flow': True,
                        'relative_permeability': True
                    }

                # Убеждаемся, что у нас есть параметры модели
                if 'parameters' not in result_data or not result_data['parameters']:
                    # Получаем параметры из проекта
                    project = Project.query.get(self.project_id)
                    if project and project.data and project.data.model_parameters:
                        try:
                            result_data['parameters'] = json.loads(project.data.model_parameters)
                        except:
                            pass

                return result_data
            except Exception as e:
                print(f"Ошибка при обработке JSON результатов: {e}")

                # Возвращаем простую структуру, чтобы избежать ошибок
                return {
                    'error': str(e),
                    'visualizations': {}
                }
        return {}

    def __repr__(self):
        return f'<ProjectResult {self.id} for project_id={self.project_id}>'