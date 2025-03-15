#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, \
    send_from_directory
from flask_login import login_required, current_user
import os
import json
import traceback
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from core.matplotlib_visualizer import MatplotlibVisualizer
from extensions import db, csrf
from models.user import User
from models.project import Project, ProjectData, ProjectResult
from core.model import OilFiltrationModel
from core.carbonate_model import CarbonateModel
from core.visualizer import Visualizer
from core.data_loader import DataLoader
from routes.api import api_bp
from utils.file_handlers import save_uploaded_file, allowed_file

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Личный кабинет пользователя"""
    # Получаем все проекты пользователя
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.updated_at.desc()).all()
    return render_template('dashboard.html', projects=projects)


@main_bp.route('/new_project', methods=['GET', 'POST'])
@login_required
def new_project():
    """Создание нового проекта"""
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        description = request.form.get('description', '')
        model_type = request.form.get('model_type')
        rock_type = request.form.get('rock_type')

        # Проверяем обязательные поля
        if not name or not model_type:
            flash('Необходимо заполнить обязательные поля', 'danger')
            return redirect(url_for('main.new_project'))

        # Создаем новый проект
        project = Project(
            name=name,
            description=description,
            model_type=model_type,
            rock_type=rock_type,
            user_id=current_user.id
        )

        # Добавляем проект в базу данных
        db.session.add(project)
        db.session.commit()

        # Обрабатываем параметры модели
        model_params = {}
        param_limits = current_app.config['PARAM_LIMITS']

        for param, limits in param_limits.items():
            if param in request.form:
                try:
                    value = float(request.form.get(param))
                    # Проверяем, что значение находится в допустимых пределах
                    if limits['min'] <= value <= limits['max']:
                        model_params[param] = value
                except (ValueError, TypeError):
                    pass

        # Обрабатываем загруженные файлы
        uploaded_files = {}
        file_fields = ['rock_properties', 'capillary_pressure', 'relative_perm', 'pvt_data', 'production_data']

        for field in file_fields:
            if field in request.files and request.files[field].filename:
                file = request.files[field]
                if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                    filename, file_path = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'], project.id)
                    if filename:
                        uploaded_files[field] = filename

        # Создаем запись данных проекта
        project_data = ProjectData(
            project_id=project.id,
            model_parameters=json.dumps(model_params)
        )

        # Сохраняем пути к загруженным файлам
        if 'rock_properties' in uploaded_files:
            project_data.rock_properties_file = uploaded_files['rock_properties']
        if 'capillary_pressure' in uploaded_files:
            project_data.capillary_pressure_file = uploaded_files['capillary_pressure']
        if 'relative_perm' in uploaded_files:
            project_data.relative_perm_file = uploaded_files['relative_perm']
        if 'pvt_data' in uploaded_files:
            project_data.pvt_data_file = uploaded_files['pvt_data']
        if 'production_data' in uploaded_files:
            project_data.production_data_file = uploaded_files['production_data']

        # Добавляем данные проекта в базу данных
        db.session.add(project_data)
        db.session.commit()

        flash('Проект успешно создан', 'success')
        return redirect(url_for('main.project_details', project_id=project.id))

    # GET-запрос для отображения формы создания проекта
    param_limits = current_app.config['PARAM_LIMITS']
    rock_presets = current_app.config['ROCK_TYPE_PRESETS']
    return render_template('new_project.html', param_limits=param_limits, rock_presets=rock_presets)


@main_bp.route('/project/<int:project_id>')
@login_required
def project_details(project_id):
    """Страница деталей проекта"""
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        flash('У вас нет доступа к этому проекту', 'danger')
        return redirect(url_for('main.dashboard'))

    # Исправляем файлы визуализаций
    fix_all_visualization_files(project_id)

    # Получаем параметры модели
    model_params = project.get_model_parameters()

    # Получаем последний результат моделирования
    results = project.results.order_by(ProjectResult.created_at.desc()).first()

    return render_template('project_details.html', project=project, model_params=model_params, results=results)


@main_bp.route('/project/<int:project_id>/run', methods=['POST'])
@login_required
def run_project(project_id):
    """Запуск моделирования для проекта"""
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        flash('У вас нет доступа к этому проекту', 'danger')
        return redirect(url_for('main.dashboard'))

    # Получаем параметры из формы, если они были изменены
    model_params = {}
    if request.form:
        param_limits = current_app.config['PARAM_LIMITS']
        for param, limits in param_limits.items():
            if param in request.form:
                try:
                    value = float(request.form.get(param))
                    if limits['min'] <= value <= limits['max']:
                        model_params[param] = value
                except (ValueError, TypeError):
                    pass
    else:
        # Используем сохраненные параметры модели
        model_params = project.get_model_parameters()

    # Создаем объект результата
    result = ProjectResult(project_id=project.id)
    db.session.add(result)
    db.session.commit()

    try:
        start_time = time.time()

        # Загружаем данные из файлов, если они есть
        if project.data:
            data_files = project.data.get_uploaded_files()
            data_loader = DataLoader(data_dir=current_app.config['UPLOAD_FOLDER'])

            # Определяем пути к файлам
            rock_file = data_files.get('rock_properties')
            cap_file = data_files.get('capillary_pressure')
            perm_file = data_files.get('relative_perm')
            pvt_file = data_files.get('pvt_data')
            prod_file = data_files.get('production_data')

            # Загружаем данные
            data_loader.load_all_data(rock_file, cap_file, perm_file, pvt_file, prod_file)

            # Извлекаем параметры из данных, если они не были указаны пользователем
            data_params = data_loader.extract_model_parameters(project.rock_type)

            # Объединяем параметры
            for key, value in data_params.items():
                if key not in model_params:
                    model_params[key] = value

        # Выбираем тип модели в зависимости от проекта
        if project.model_type == 'carbonate':
            model = CarbonateModel(model_params)
            # Запускаем моделирование с двойной пористостью
            model.run_dual_porosity_simulation()
        else:
            model = OilFiltrationModel(model_params)
            # Запускаем обычное моделирование
            model.run_simulation()

        # Извлекаем результаты
        results_data = model.extract_results()

        # Создаем визуализатор Plotly для JSON-представлений (для фронтенда)
        visualizer = Visualizer(
            model,
            output_dir=current_app.config['RESULTS_FOLDER'],
            image_output_dir=current_app.config['IMAGES_FOLDER']
        )

        # Добавляем визуализации к результатам
        results_data['visualizations'] = {
            'saturation_profiles': True,
            'saturation_difference': True,
            'recovery_factor': True,
            'breakthrough_time': True,
            'saturation_evolution': True,
            'capillary_pressure': True,
            'fractional_flow': True,
            'relative_permeability': True
        }

        # Сохраняем JSON-визуализации для веб-интерфейса
        visualizer.save_visualizations(project_id)

        # Используем MatplotlibVisualizer для создания и сохранения изображений
        try:
                        # Создаем экземпляр MatplotlibVisualizer
            mpl_visualizer = MatplotlibVisualizer(
                model,
                output_dir=current_app.config['RESULTS_FOLDER'],
                image_output_dir=current_app.config['IMAGES_FOLDER']
            )

            # Сохраняем изображения в форматах PNG и SVG
            image_paths = mpl_visualizer.save_visualizations_as_images(
                project_id,
                user_id=current_user.id,
                formats=['png', 'svg']
            )

            # Добавляем информацию о сохраненных изображениях в результаты
            results_data['image_paths'] = {
                format_type: {name: os.path.relpath(path, current_app.config['IMAGES_FOLDER'])
                              for name, path in paths.items()}
                for format_type, paths in image_paths.items()
            }

            print(f"Сохранено изображений: PNG - {len(image_paths['png'])}, SVG - {len(image_paths['svg'])}")

        except Exception as e:
            print(f"ОШИБКА при сохранении изображений: {str(e)}")
            traceback.print_exc()
            # Обеспечиваем, чтобы в результатах была пустая структура даже в случае ошибки
            results_data['image_paths'] = {'png': {}, 'svg': {}}

        # Рассчитываем время выполнения
        end_time = time.time()
        runtime = end_time - start_time

        # Сохраняем результаты
        result.save_results(results_data, runtime)

        flash('Моделирование успешно выполнено', 'success')
    except Exception as e:
        # Обрабатываем ошибку
        error_message = str(e)
        traceback_str = traceback.format_exc()

        result.status = 'error'
        result.error_message = f"{error_message}\n\n{traceback_str}"
        db.session.commit()

        flash(f'Ошибка при моделировании: {error_message}', 'danger')

    return redirect(url_for('main.project_details', project_id=project_id))


@main_bp.route('/project/<int:project_id>/results/<int:result_id>')
@login_required
def view_results(project_id, result_id):
    """Просмотр результатов моделирования"""
    project = Project.query.get_or_404(project_id)
    result = ProjectResult.query.get_or_404(result_id)

    # Проверяем, что проект принадлежит текущему пользователю и результат принадлежит проекту
    if project.user_id != current_user.id or result.project_id != project_id:
        flash('У вас нет доступа к этим результатам', 'danger')
        return redirect(url_for('main.dashboard'))

    # Исправляем файлы визуализаций
    fix_all_visualization_files(project_id)

    # Получаем данные результатов
    results_data = result.get_results()

    return render_template('results.html', project=project, result=result, results_data=results_data)


@main_bp.route('/project/<int:project_id>/visualization/<name>')
@login_required
def get_visualization(project_id, name):
    """Получение JSON-данных визуализации"""
    print(f"=== Запрос визуализации: project_id={project_id}, name={name} ===")

    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        print(f"Доступ запрещен: проект принадлежит пользователю {project.user_id}, а запрос от {current_user.id}")
        return jsonify({'error': 'Access denied'}), 403

    # Исправляем файл визуализации перед чтением
    fix_visualization_file(project_id, name)

    # Путь к файлу визуализации
    file_path = os.path.join(current_app.config['RESULTS_FOLDER'], str(project_id), f'{name}.json')
    print(f"Путь к файлу визуализации: {file_path}")

    if not os.path.exists(file_path):
        print(f"Файл визуализации не найден по пути: {file_path}")
        return jsonify({'error': 'Visualization not found'}), 404

    # Читаем JSON-данные визуализации
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            visualization_data = json.load(f)
            print(f"Файл визуализации успешно загружен, размер данных: {len(str(visualization_data))} символов")

            # Проверяем структуру данных
            if 'data' not in visualization_data:
                print(f"ОШИБКА: В данных визуализации отсутствует ключ 'data'")
                # Создаем базовую структуру
                visualization_data = {'data': [], 'layout': {}}
            elif not isinstance(visualization_data['data'], list):
                print(f"ОШИБКА: visualization_data['data'] не является списком: {type(visualization_data['data'])}")
                # Корректируем тип данных
                visualization_data['data'] = []
            else:
                print(f"visualization_data['data'] содержит {len(visualization_data['data'])} элементов")

            if 'layout' not in visualization_data:
                print(f"ОШИБКА: В данных визуализации отсутствует ключ 'layout'")
                visualization_data['layout'] = {}

            # Улучшаем стиль графиков
            if 'layout' in visualization_data:
                layout = visualization_data['layout']

                # Добавляем отступы, если их нет
                if 'margin' not in layout:
                    layout['margin'] = {'l': 60, 'r': 40, 't': 60, 'b': 60}

                # Устанавливаем шрифт
                if 'font' not in layout:
                    layout['font'] = {'family': 'Roboto, sans-serif', 'size': 14}

                # Устанавливаем цвет фона
                if 'plot_bgcolor' not in layout:
                    layout['plot_bgcolor'] = '#f8f8f8'
                if 'paper_bgcolor' not in layout:
                    layout['paper_bgcolor'] = '#ffffff'

            return jsonify(visualization_data)
    except Exception as e:
        print(f"ОШИБКА при чтении файла визуализации: {str(e)}")
        return jsonify({'error': f'Error reading visualization: {str(e)}'}), 500


@main_bp.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Редактирование проекта"""
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        flash('У вас нет доступа к этому проекту', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        description = request.form.get('description', '')
        rock_type = request.form.get('rock_type')

        # Проверяем обязательные поля
        if not name:
            flash('Необходимо заполнить название проекта', 'danger')
            return redirect(url_for('main.edit_project', project_id=project_id))

        # Обновляем данные проекта
        project.name = name
        project.description = description
        project.rock_type = rock_type

        # Обрабатываем параметры модели
        model_params = {}
        param_limits = current_app.config['PARAM_LIMITS']

        for param, limits in param_limits.items():
            if param in request.form:
                try:
                    value = float(request.form.get(param))
                    # Проверяем, что значение находится в допустимых пределах
                    if limits['min'] <= value <= limits['max']:
                        model_params[param] = value
                except (ValueError, TypeError):
                    pass

        # Обрабатываем загруженные файлы
        file_fields = ['rock_properties', 'capillary_pressure', 'relative_perm', 'pvt_data', 'production_data']

        for field in file_fields:
            if field in request.files and request.files[field].filename:
                file = request.files[field]
                if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                    filename = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'], project.id)
                    if filename:
                        # Обновляем путь к файлу
                        if project.data:
                            setattr(project.data, f'{field}_file', filename)

        # Обновляем параметры модели
        if project.data:
            project.data.model_parameters = json.dumps(model_params)
        else:
            # Создаем запись данных проекта, если ее еще нет
            project_data = ProjectData(
                project_id=project.id,
                model_parameters=json.dumps(model_params)
            )
            db.session.add(project_data)

        # Сохраняем изменения
        db.session.commit()

        flash('Проект успешно обновлен', 'success')
        return redirect(url_for('main.project_details', project_id=project_id))

    # GET-запрос для отображения формы редактирования проекта
    param_limits = current_app.config['PARAM_LIMITS']
    rock_presets = current_app.config['ROCK_TYPE_PRESETS']
    model_params = project.get_model_parameters()

    return render_template(
        'edit_project.html',
        project=project,
        param_limits=param_limits,
        rock_presets=rock_presets,
        model_params=model_params
    )


@main_bp.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Удаление проекта"""
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        flash('У вас нет доступа к этому проекту', 'danger')
        return redirect(url_for('main.dashboard'))

    # Удаляем файлы проекта
    project_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(project_id))
    project_results_dir = os.path.join(current_app.config['RESULTS_FOLDER'], str(project_id))

    try:
        if os.path.exists(project_upload_dir):
            for file in os.listdir(project_upload_dir):
                os.remove(os.path.join(project_upload_dir, file))
            os.rmdir(project_upload_dir)

        if os.path.exists(project_results_dir):
            for file in os.listdir(project_results_dir):
                os.remove(os.path.join(project_results_dir, file))
            os.rmdir(project_results_dir)
    except Exception as e:
        flash(f'Ошибка при удалении файлов проекта: {str(e)}', 'warning')

    # Удаляем проект из базы данных
    db.session.delete(project)
    db.session.commit()

    flash('Проект успешно удален', 'success')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/help')
def help_page():
    """Страница справки и инструкций по использованию"""
    return render_template('help.html')


@main_bp.route('/about')
def about():
    """Страница о проекте"""
    return render_template('about.html')


def fix_visualization_file(project_id, viz_name):
    """Исправление структуры конкретного файла визуализации"""
    results_folder = current_app.config['RESULTS_FOLDER']
    file_path = os.path.join(results_folder, str(project_id), f'{viz_name}.json')

    if not os.path.exists(file_path):
        print(f"Файл визуализации не найден: {file_path}")
        return False

    try:
        print(f"Проверка файла визуализации: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Проверяем структуру
        fixed = False

        # Создаем правильную структуру данных
        corrected_data = {
            "data": [],
            "layout": {}
        }

        # Проверяем наличие данных и наполняем структуру
        if 'data' in json_data and isinstance(json_data['data'], list):
            corrected_data["data"] = json_data["data"]
        elif 'traces' in json_data and isinstance(json_data['traces'], list):
            corrected_data["data"] = json_data["traces"]
        elif 'frames' in json_data and isinstance(json_data['frames'], list) and len(json_data['frames']) > 0:
            if 'data' in json_data['frames'][0] and isinstance(json_data['frames'][0]['data'], list):
                corrected_data["data"] = json_data["frames"][0]["data"]

        # Проверяем макет
        if 'layout' in json_data and isinstance(json_data['layout'], dict):
            corrected_data["layout"] = json_data["layout"]

        # Исправляем данные трасс
        for i, trace in enumerate(corrected_data["data"]):
            # Обработка координат x, y, z
            for key in ['x', 'y', 'z']:
                if key in trace and isinstance(trace[key], dict):
                    # Преобразуем объекты с бинарными данными в обычные массивы
                    if 'data' in trace[key] and isinstance(trace[key]['data'], list):
                        corrected_data["data"][i][key] = trace[key]['data']
                    elif 'original' in trace[key] and isinstance(trace[key]['original'], list):
                        corrected_data["data"][i][key] = trace[key]['original']
                    # Сохраняем ссылку на бинарные данные, если других нет
                    elif 'bdata' in trace[key] and not corrected_data["data"][i][key]:
                        # Просто оставим объект как есть, JavaScript-код попытается его обработать
                        pass

            # Убеждаемся, что trace имеет тип
            if 'type' not in trace:
                if 'mode' in trace and 'markers' in trace['mode']:
                    corrected_data["data"][i]['type'] = 'scatter'
                elif 'z' in trace and isinstance(trace['z'], list):
                    corrected_data["data"][i]['type'] = 'contour'
                else:
                    corrected_data["data"][i]['type'] = 'scatter'

        # Определяем, были ли внесены изменения
        if corrected_data != json_data:
            fixed = True
            # Сохраняем исправленный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(corrected_data, f, indent=2)
            print(f"Файл визуализации исправлен и сохранен: {viz_name}")

        return fixed
    except Exception as e:
        print(f"ОШИБКА при обработке файла визуализации {viz_name}: {str(e)}")
        import traceback
        traceback.print_exc()

        # В случае ошибки создаем минимальный рабочий JSON
        try:
            minimal_data = {
                "data": [{
                    "type": "scatter",
                    "mode": "lines",
                    "x": [0, 1, 2, 3, 4, 5],
                    "y": [0, 1, 0, 1, 0, 1],
                    "name": "Данные недоступны"
                }],
                "layout": {
                    "title": f"Ошибка загрузки: {viz_name}",
                    "xaxis": {"title": "X"},
                    "yaxis": {"title": "Y"}
                }
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(minimal_data, f, indent=2)
            print(f"Создан минимальный файл визуализации для {viz_name}")
            return True
        except:
            return False


def fix_all_visualization_files(project_id=None):
    """Исправление всех файлов визуализации в директории результатов"""
    results_folder = current_app.config['RESULTS_FOLDER']

    if not os.path.exists(results_folder):
        print(f"Директория результатов не найдена: {results_folder}")
        return

    print(f"Сканирование директории результатов: {results_folder}")

    # Если указан конкретный проект, проверяем только его
    if project_id:
        project_dirs = [str(project_id)]
    else:
        # Сканируем все поддиректории проектов
        project_dirs = [d for d in os.listdir(results_folder) if os.path.isdir(os.path.join(results_folder, d))]

    print(f"Найдено {len(project_dirs)} директорий проектов")

    for project_dir in project_dirs:
        project_path = os.path.join(results_folder, project_dir)
        try:
            json_files = [f for f in os.listdir(project_path) if f.endswith('.json')]
            print(f"Проект {project_dir}: найдено {len(json_files)} JSON-файлов")

            for json_file in json_files:
                viz_name = json_file.replace('.json', '')
                fix_visualization_file(project_dir, viz_name)
        except Exception as e:
            print(f"Ошибка при сканировании проекта {project_dir}: {str(e)}")


@main_bp.route('/project/<int:project_id>/image/<path:image_path>')
@login_required
def get_project_image(project_id, image_path):
    """
    Получение изображения визуализации для проекта

    Args:
        project_id (int): ID проекта
        image_path (str): Относительный путь к изображению
    """
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        flash('У вас нет доступа к этому проекту', 'danger')
        return redirect(url_for('main.dashboard'))

    print(f"Запрос изображения для проекта {project_id}, путь: {image_path}")

    # Получаем только имя файла без путей
    filename = os.path.basename(image_path)
    print(f"Имя файла: {filename}")

    # Путь к папке пользователя
    user_project_path = os.path.join(
        current_app.config['IMAGES_FOLDER'],
        f"user_{current_user.id}",
        f"project_{project_id}"
    )

    # Путь к файлу в папке пользователя
    file_path = os.path.join(user_project_path, filename)
    print(f"Ищем файл: {file_path}")

    if os.path.exists(file_path):
        print(f"Файл найден: {file_path}")
        return send_from_directory(user_project_path, filename)

    # Проверяем общую папку проекта
    project_path = os.path.join(
        current_app.config['IMAGES_FOLDER'],
        f"project_{project_id}"
    )

    file_path = os.path.join(project_path, filename)
    print(f"Ищем файл в общей директории: {file_path}")

    if os.path.exists(file_path):
        print(f"Файл найден: {file_path}")
        return send_from_directory(project_path, filename)

    print(f"Файл не найден")
    return jsonify({'error': 'Image not found'}), 404




@main_bp.route('/project/<int:project_id>/download/image/<image_type>/<image_name>')
@login_required
def download_project_image(project_id, image_type, image_name):
    """
    Скачивание конкретного изображения визуализации

    Args:
        project_id (int): ID проекта
        image_type (str): Тип изображения ('png' или 'svg')
        image_name (str): Имя изображения
    """
    project = Project.query.get_or_404(project_id)

    # Проверяем, что проект принадлежит текущему пользователю
    if project.user_id != current_user.id:
        flash('У вас нет доступа к этому проекту', 'danger')
        return redirect(url_for('main.dashboard'))

    # Проверяем корректность типа изображения
    if image_type not in ['png', 'svg']:
        return jsonify({'error': 'Invalid image type'}), 400

    # Строим путь к изображению для конкретного пользователя и проекта
    user_project_path = os.path.join(
        current_app.config['IMAGES_FOLDER'],
        f"user_{current_user.id}",
        f"project_{project_id}"
    )

    # Если директории нет или изображения нет в папке пользователя, ищем в общей папке проекта
    file_path = os.path.join(user_project_path, f"{image_name}.{image_type}")
    if not os.path.exists(file_path):
        user_project_path = os.path.join(
            current_app.config['IMAGES_FOLDER'],
            f"project_{project_id}"
        )
        file_path = os.path.join(user_project_path, f"{image_name}.{image_type}")

    # Проверяем существование файла
    if not os.path.exists(file_path):
        return jsonify({'error': 'Image not found'}), 404

    # Более понятное имя файла для скачивания
    download_name = f"{project.name}_{image_name}.{image_type}"

    # Возвращаем изображение для скачивания с attachment_filename
    return send_from_directory(
        user_project_path,
        f"{image_name}.{image_type}",
        as_attachment=True,
        download_name=download_name
    )