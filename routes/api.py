#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db, csrf  # Добавьте импорт csrf отсюда
import os
import json
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np

from models.project import Project, ProjectData, ProjectResult
from core.data_loader import DataLoader
from utils.file_handlers import allowed_file, save_uploaded_file

api_bp = Blueprint('api', __name__)


@api_bp.route('/rock_presets/<rock_type>')
@login_required
def get_rock_preset(rock_type):
    """Получение параметров выбранного типа породы"""
    rock_presets = current_app.config['ROCK_TYPE_PRESETS']

    if rock_type in rock_presets:
        return jsonify(rock_presets[rock_type])
    else:
        return jsonify({'error': 'Тип породы не найден'}), 404


@api_bp.route('/model_parameters/<int:project_id>')
@login_required
def get_model_parameters(project_id):
    """Получение параметров модели для проекта"""
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    model_params = project.get_model_parameters()
    return jsonify(model_params)


@api_bp.route('/results/<int:project_id>/latest')
@login_required
def get_latest_results(project_id):
    """Получение данных последнего результата моделирования"""
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    # Получаем последний результат моделирования
    result = project.results.order_by(ProjectResult.created_at.desc()).first()

    if not result:
        return jsonify({'error': 'No results found'}), 404

    results_data = result.get_results()
    return jsonify({
        'result_id': result.id,
        'run_date': result.run_date.isoformat(),
        'runtime': result.runtime,
        'status': result.status,
        'data': results_data
    })


@api_bp.route('/file/validate', methods=['POST'])
@login_required
def validate_file():
    """Валидация загруженного файла CSV"""
    try:
        print("=== Начало обработки запроса /api/file/validate ===")

        if 'file' not in request.files:
            print("Ошибка: поле 'file' отсутствует в запросе")
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        # Получаем тип файла из формы
        file_type = request.form.get('file_type', '')
        print(f"Тип файла из запроса: '{file_type}'")
        print(f"Имя файла: '{file.filename}'")

        if file.filename == '':
            print("Ошибка: пустое имя файла")
            return jsonify({'error': 'No selected file'}), 400

        # Проверяем расширение файла
        if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            print(f"Ошибка: недопустимое расширение файла {file.filename}")
            return jsonify({'error': 'File extension not allowed'}), 400

        # Вместо сохранения файла, читаем его содержимое напрямую
        file_content = file.read()
        print(f"Прочитано {len(file_content)} байт из файла")

        # Определяем кодировку
        try:
            import chardet
            result = chardet.detect(file_content)
            detected_encoding = result['encoding'] or 'utf-8'
            confidence = result['confidence']
            print(f"Определена кодировка: {detected_encoding} с уверенностью {confidence}")
        except ImportError:
            detected_encoding = 'utf-8'  # По умолчанию
            print("Модуль chardet не установлен, используем кодировку по умолчанию")

        # Пробуем разные кодировки для декодирования
        encodings = [detected_encoding, 'utf-8', 'cp1251', 'latin1', 'windows-1252']
        separators = [',', ';', '\t']

        df = None
        success_info = ""

        for encoding in encodings:
            for sep in separators:
                try:
                    print(f"Пробуем прочитать с кодировкой {encoding} и разделителем '{sep}'")
                    # Преобразуем байты в строку и используем StringIO
                    from io import StringIO
                    decoded_content = file_content.decode(encoding)
                    df = pd.read_csv(StringIO(decoded_content), sep=sep, engine='python')

                    if len(df.columns) > 1:
                        success_info = f"Файл успешно прочитан с кодировкой {encoding} и разделителем '{sep}'"
                        print(success_info)
                        print(f"Колонки: {list(df.columns)}")
                        break
                except Exception as e:
                    print(f"Ошибка при чтении с кодировкой {encoding} и разделителем '{sep}': {str(e)}")
                    continue

            if df is not None and len(df.columns) > 1:
                break

        # Определяем требуемые колонки в зависимости от типа файла
        required_columns = {
            'rock_properties': ['ID_Sample', 'Porosity_fr', 'Permeability_mD', 'Rock_Type'],
            'capillary_pressure': ['ID_Sample', 'Water_Saturation', 'Pc_Drainage_MPa'],
            'relative_perm': ['ID_Sample', 'Water_Saturation', 'Krw_Drainage', 'Kro_Drainage'],
            'pvt_data': ['Pressure_MPa', 'Oil_Viscosity_cP'],
            'production_data': ['Date', 'Oil_Rate_m3_day', 'Water_Rate_m3_day']
        }

        # Проверяем, есть ли указанный тип файла в списке допустимых типов
        columns = required_columns.get(file_type, [])

        if df is None:
            return jsonify({
                'valid': False,
                'message': "Не удалось прочитать файл. Проверьте формат и кодировку файла."
            })

        # Проверяем наличие необходимых колонок
        missing_columns = [col for col in columns if col not in df.columns]

        if missing_columns:
            return jsonify({
                'valid': False,
                'message': f"В файле отсутствуют следующие обязательные колонки: {', '.join(missing_columns)}. Доступные колонки: {', '.join(df.columns)}"
            })

        return jsonify({
            'valid': True,
            'message': f"Файл соответствует требованиям. {success_info}"
        })

    except Exception as e:
        import traceback
        print(f"КРИТИЧЕСКАЯ ОШИБКА при валидации файла: {str(e)}")
        print(traceback.format_exc())

        # Возвращаем подробную ошибку клиенту
        return jsonify({
            'valid': False,
            'message': f"Ошибка обработки файла: {str(e)}"
        }), 500

@api_bp.route('/file/preview', methods=['POST'])
@login_required
def preview_file():
    """Предварительный просмотр данных из CSV-файла"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
        return jsonify({'error': 'File extension not allowed'}), 400

    # Сохраняем файл во временную директорию
    temp_filename = save_uploaded_file(file, current_app.config['TEMP_FOLDER'], 'temp')

    if not temp_filename:
        return jsonify({'error': 'Error saving file'}), 500

    # Путь к временному файлу
    file_path = os.path.join(current_app.config['TEMP_FOLDER'], temp_filename)

    try:
        # Читаем данные из файла
        df = pd.read_csv(file_path)

        # Получаем первые 10 строк для предварительного просмотра
        preview_data = df.head(10).to_dict(orient='records')

        # Получаем информацию о колонках
        columns = list(df.columns)

        # Получаем статистику по данным
        stats = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats[col] = {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std()),
                    'type': 'numeric'
                }
            else:
                stats[col] = {
                    'unique': len(df[col].unique()),
                    'type': 'categorical'
                }

        # Удаляем временный файл
        os.remove(file_path)

        return jsonify({
            'columns': columns,
            'preview': preview_data,
            'stats': stats,
            'total_rows': len(df)
        })

    except Exception as e:
        # Удаляем временный файл в случае ошибки
        try:
            os.remove(file_path)
        except:
            pass

        return jsonify({'error': str(e)}), 500


@api_bp.route('/visualization/<int:project_id>/<name>')
@login_required
def get_visualization(project_id, name):
    """Получение данных визуализации"""
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    # Путь к файлу визуализации
    file_path = os.path.join(current_app.config['RESULTS_FOLDER'], str(project_id), f'{name}.json')

    if not os.path.exists(file_path):
        return jsonify({'error': 'Visualization not found'}), 404

    # Читаем JSON-данные визуализации
    with open(file_path, 'r', encoding='utf-8') as f:
        visualization_data = json.load(f)

    return jsonify(visualization_data)


@api_bp.route('/parameters/check', methods=['POST'])
@login_required
@csrf.exempt  # Временно отключаем CSRF для отладки
def check_parameters():
    """Проверка параметров модели на валидность"""
    try:
        print("=== Начало проверки параметров модели ===")

        # Печатаем заголовки запроса
        print("Заголовки запроса:")
        for header, value in request.headers:
            print(f"  {header}: {value}")

        # Печатаем тело запроса
        print("Тело запроса:")
        print(request.get_data(as_text=True))

        # Пытаемся получить JSON
        data = request.get_json(silent=True)
        if data is None:
            # Если JSON не получен, пробуем получить данные из form-data
            data = request.form.to_dict()
            print("Данные получены из form-data")
        else:
            print("Данные получены из JSON")

        print(f"Полученные параметры: {data}")

        if not data:
            print("Ошибка: данные не предоставлены")
            return jsonify({'error': 'No data provided'}), 400

        param_limits = current_app.config['PARAM_LIMITS']
        errors = {}
        warnings = {}

        for param, value in data.items():
            # Проверяем, что параметр определен в ограничениях
            if param in param_limits:
                try:
                    float_value = float(value)
                    print(f"Проверка параметра {param}: значение {float_value}, "
                          f"допустимый диапазон [{param_limits[param]['min']}, {param_limits[param]['max']}]")

                    # Проверяем, что значение в допустимых пределах
                    if float_value < param_limits[param]['min']:
                        error_msg = f"Значение меньше минимально допустимого: {param_limits[param]['min']} {param_limits[param]['unit']}"
                        errors[param] = error_msg
                        print(f"Ошибка для {param}: {error_msg}")
                    elif float_value > param_limits[param]['max']:
                        error_msg = f"Значение больше максимально допустимого: {param_limits[param]['max']} {param_limits[param]['unit']}"
                        errors[param] = error_msg
                        print(f"Ошибка для {param}: {error_msg}")

                    # Проверяем, что значение близко к типичным значениям
                    if 'normal_min' in param_limits[param] and 'normal_max' in param_limits[param]:
                        if float_value < param_limits[param]['normal_min'] or float_value > param_limits[param][
                            'normal_max']:
                            warning_msg = f"Значение выходит за пределы типичного диапазона: {param_limits[param]['normal_min']} - {param_limits[param]['normal_max']} {param_limits[param]['unit']}"
                            warnings[param] = warning_msg
                            print(f"Предупреждение для {param}: {warning_msg}")
                except ValueError as e:
                    error_msg = "Значение должно быть числом"
                    errors[param] = error_msg
                    print(f"Ошибка для {param}: {error_msg} - {str(e)}")
            else:
                print(f"Параметр {param} не найден в списке ограничений")

        result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

        print(f"Результат проверки: {result}")
        print("=== Конец проверки параметров модели ===")

        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"КРИТИЧЕСКАЯ ОШИБКА при проверке параметров: {str(e)}")
        print(traceback.format_exc())

        return jsonify({
            'valid': False,
            'errors': {'general': f"Ошибка при проверке параметров: {str(e)}"},
            'warnings': {}
        }), 400


@api_bp.route('/project/<int:project_id>/export', methods=['GET'])
@login_required
def export_project_data(project_id):
    """Экспорт данных проекта"""
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    # Получаем параметры модели
    model_params = project.get_model_parameters()

    # Получаем последний результат моделирования
    result = project.results.order_by(ProjectResult.created_at.desc()).first()
    results_data = result.get_results() if result else None

    # Формируем данные для экспорта
    export_data = {
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'model_type': project.model_type,
            'rock_type': project.rock_type,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat()
        },
        'parameters': model_params,
        'results': results_data
    }

    return jsonify(export_data)