#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import traceback

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json


class Visualizer:
    """Класс для визуализации результатов моделирования"""

    def __init__(self, model, output_dir=None, image_output_dir=None):
        self.model = model
        self.output_dir = output_dir or 'data/results'
        # Новый параметр для директории сохранения изображений
        self.image_output_dir = image_output_dir or 'data/images'
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_output_dir, exist_ok=True)

    def create_saturation_profiles_figure(self, days=[10, 50, 100]):
        """Создание графика профилей насыщенности"""
        # Создаем фигуру с подграфиками
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Профиль насыщенности без учета капиллярных эффектов',
                'Профиль насыщенности с учетом капиллярных эффектов'
            ),
            shared_xaxes=True
        )

        # Добавляем линии для каждого дня
        colors = ['blue', 'green', 'red']
        for i, day in enumerate(days):
            if day > self.model.days:
                continue

            time_index = int(day / self.model.dt)

            # Получаем данные из модели через метод get_saturation_profile
            with_cap_data, without_cap_data = self.get_saturation_profile(time_index)

            # График насыщенности без учета капиллярных эффектов
            fig.add_trace(
                go.Scatter(
                    x=self.model.x,
                    y=without_cap_data,  # Используем полученные данные
                    mode='lines',
                    name=f'День {day} (без кап. эффектов)',
                    line=dict(color=colors[i % len(colors)])
                ),
                row=1, col=1
            )

            # График насыщенности с учетом капиллярных эффектов
            fig.add_trace(
                go.Scatter(
                    x=self.model.x,
                    y=with_cap_data,  # Используем полученные данные
                    mode='lines',
                    name=f'День {day} (с кап. эффектами)',
                    line=dict(color=colors[i % len(colors)])
                ),
                row=2, col=1
            )

        # Настройка осей и заголовка
        fig.update_xaxes(title_text='Расстояние, м', row=2, col=1)
        fig.update_yaxes(title_text='Водонасыщенность, д.ед.', row=1, col=1)
        fig.update_yaxes(title_text='Водонасыщенность, д.ед.', row=2, col=1)
        fig.update_layout(
            title_text='Профили насыщенности',
            height=800,
            legend_title='Время',
            hovermode='closest'
        )

        return fig

    def get_saturation_profile(self, time_index):
        """Получение профилей насыщенности для заданного момента времени"""
        # Если используется карбонатная модель
        if hasattr(self.model, 'Sw_matrix') and hasattr(self.model, 'Sw_fracture'):
            # Рассчитываем насыщенность с учетом капиллярных эффектов
            matrix_volume = self.model.matrix_porosity / self.model.porosity
            fracture_volume = self.model.fracture_porosity / self.model.porosity
            with_cap_data = matrix_volume * self.model.Sw_matrix[time_index,
                                            :] + fracture_volume * self.model.Sw_fracture[time_index, :]

            # Для данных без учета капиллярных эффектов используем имеющийся массив
            without_cap_data = self.model.Sw_without_cap[time_index, :]
        else:
            # Для обычной модели используем имеющиеся массивы
            with_cap_data = self.model.Sw_with_cap[time_index, :]
            without_cap_data = self.model.Sw_without_cap[time_index, :]

        return with_cap_data, without_cap_data

    def create_saturation_difference_figure(self, days=[10, 50, 100]):
        """Создание графика разницы насыщенностей"""
        # Создаем фигуру
        fig = go.Figure()

        # Добавляем линии для каждого дня
        colors = ['blue', 'green', 'red']
        for i, day in enumerate(days):
            if day > self.model.days:
                continue

            time_index = int(day / self.model.dt)

            # Получаем данные из модели через метод get_saturation_profile
            with_cap_data, without_cap_data = self.get_saturation_profile(time_index)

            # Вычисляем разницу насыщенностей
            diff = with_cap_data - without_cap_data

            # Добавляем график разницы
            fig.add_trace(
                go.Scatter(
                    x=self.model.x,
                    y=diff,
                    mode='lines',
                    name=f'День {day}',
                    line=dict(color=colors[i % len(colors)])
                )
            )

        # Добавляем нулевую линию
        fig.add_hline(y=0, line_dash='dash', line_color='black', line_width=1)

        # Настройка осей и заголовка
        fig.update_xaxes(title_text='Расстояние, м')
        fig.update_yaxes(title_text='Разница водонасыщенности, д.ед.')
        fig.update_layout(
            title_text='Разница водонасыщенности (с учетом - без учета капиллярных эффектов)',
            height=500,
            legend_title='Время',
            hovermode='closest'
        )

        return fig


    def create_recovery_factor_figure(self):
        """Создание графика коэффициента нефтеотдачи"""
        # Получаем данные о коэффициенте нефтеотдачи
        recovery_with_cap, recovery_without_cap = self.model.calculate_recovery_factor()

        # Создаем фигуру
        fig = go.Figure()

        # Добавляем графики
        fig.add_trace(
            go.Scatter(
                x=self.model.t,
                y=recovery_without_cap,
                mode='lines',
                name='Без капиллярных эффектов',
                line=dict(color='blue')
            )
        )

        fig.add_trace(
            go.Scatter(
                x=self.model.t,
                y=recovery_with_cap,
                mode='lines',
                name='С капиллярными эффектами',
                line=dict(color='red')
            )
        )

        # Настройка осей и заголовка
        fig.update_xaxes(title_text='Время, дни')
        fig.update_yaxes(title_text='Коэффициент нефтеотдачи, д.ед.')
        fig.update_layout(
            title_text='Динамика коэффициента нефтеотдачи',
            height=500,
            legend_title='Модель',
            hovermode='closest'
        )

        return fig

    def create_breakthrough_time_figure(self):
        """Создание графика времени прорыва воды"""
        # Получаем время прорыва
        breakthrough_with_cap, breakthrough_without_cap = self.model.get_breakthrough_time()

        # Создаем фигуру с гистограммой
        fig = go.Figure()

        categories = ['Без капиллярных эффектов', 'С капиллярными эффектами']
        values = [breakthrough_without_cap, breakthrough_with_cap]
        colors = ['blue', 'red']

        fig.add_trace(
            go.Bar(
                x=categories,
                y=values,
                text=values,
                textposition='auto',
                marker_color=colors
            )
        )

        # Настройка осей и заголовка
        fig.update_yaxes(title_text='Время, дни')
        fig.update_layout(
            title_text='Время прорыва воды',
            height=500,
            hovermode='closest'
        )

        return fig

    def create_saturation_evolution_figure(self):
        """Создание контурного графика эволюции насыщенности"""
        # Создаем сетку времени и пространства
        X, T = np.meshgrid(self.model.x, self.model.t)

        # Создаем фигуру с подграфиками
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                'Эволюция насыщенности без учета капиллярных эффектов',
                'Эволюция насыщенности с учетом капиллярных эффектов'
            )
        )

        # Добавляем контурные графики
        fig.add_trace(
            go.Contour(
                z=self.model.Sw_without_cap,
                x=self.model.x,
                y=self.model.t,
                colorscale='Viridis',
                colorbar=dict(title='Водонасыщенность, д.ед.', x=-0.07),
                contours=dict(
                    start=0,
                    end=1,
                    size=0.05
                )
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Contour(
                z=self.model.Sw_with_cap,
                x=self.model.x,
                y=self.model.t,
                colorscale='Viridis',
                colorbar=dict(title='Водонасыщенность, д.ед.', x=1.07),
                contours=dict(
                    start=0,
                    end=1,
                    size=0.05
                )
            ),
            row=1, col=2
        )

        # Настройка осей и заголовка
        fig.update_xaxes(title_text='Расстояние, м', row=1, col=1)
        fig.update_xaxes(title_text='Расстояние, м', row=1, col=2)
        fig.update_yaxes(title_text='Время, дни', row=1, col=1)
        fig.update_yaxes(title_text='Время, дни', row=1, col=2)
        fig.update_layout(
            title_text='Эволюция насыщенности во времени и пространстве',
            height=600,
            hovermode='closest'
        )

        return fig

    def create_capillary_pressure_curve(self):
        """Создание графика кривой капиллярного давления"""
        # Создаем массив насыщенностей (больше точек для плавной кривой)
        sw_values = np.linspace(0.0, 1.0, 150)
        pc_values = np.zeros_like(sw_values)

        # Вычисляем капиллярное давление для каждой насыщенности
        for i, sw in enumerate(sw_values):
            pc_values[i] = self.model.capillary_pressure(sw)

        # Создаем фигуру
        fig = go.Figure()

        # Добавляем график
        fig.add_trace(
            go.Scatter(
                x=sw_values.tolist(),
                y=pc_values.tolist(),
                mode='lines',
                line=dict(color='blue', width=3),
                name='Капиллярное давление'
            )
        )

        # Добавляем нулевую линию
        fig.add_shape(
            type="line",
            x0=0, y0=0, x1=1, y1=0,
            line=dict(color="black", width=1, dash="dash"),
        )

        # Настройка осей и заголовка
        fig.update_layout(
            title='Кривая капиллярного давления',
            title_font_size=20,
            xaxis_title='Водонасыщенность, д.ед.',
            yaxis_title='Капиллярное давление, МПа',
            xaxis_range=[0, 1],
            plot_bgcolor='#f8f9fa',
            width=800,
            height=600,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#cccccc'
            )
        )

        return fig

    def create_relative_permeability_curves(self):
        """Создание графика кривых относительной проницаемости"""
        # Создаем массив насыщенностей (100 РАВНОМЕРНЫХ точек)
        sw_values = np.linspace(0.0, 1.0, 100)
        krw_values = np.zeros_like(sw_values)
        kro_values = np.zeros_like(sw_values)

        # Вычисляем относительные проницаемости для каждой насыщенности
        for i, sw in enumerate(sw_values):
            krw_values[i] = self.model.relative_permeability_water(sw)
            kro_values[i] = self.model.relative_permeability_oil(sw)

        # Создаем фигуру
        fig = go.Figure()

        # Добавляем графики напрямую как массивы (без любых сложных преобразований)
        fig.add_trace(
            go.Scatter(
                x=sw_values.tolist(),  # Явно преобразуем в список Python
                y=krw_values.tolist(),  # Явно преобразуем в список Python
                mode='lines',
                line=dict(color='blue', width=3),
                name='Krw (вода)'
            )
        )

        fig.add_trace(
            go.Scatter(
                x=sw_values.tolist(),  # Явно преобразуем в список Python
                y=kro_values.tolist(),  # Явно преобразуем в список Python
                mode='lines',
                line=dict(color='green', width=3),
                name='Kro (нефть)'
            )
        )

        # Настройка осей и заголовка
        fig.update_layout(
            title='Кривые относительной проницаемости',
            title_font_size=20,
            xaxis_title='Водонасыщенность, д.ед.',
            yaxis_title='Относительная проницаемость, д.ед.',
            xaxis_range=[0, 1],  # Устанавливаем диапазон значений по X от 0 до 1
            yaxis_range=[0, 1],  # Устанавливаем диапазон значений по Y от 0 до 1
            plot_bgcolor='#f8f9fa',
            width=800,
            height=600,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#cccccc'
            )
        )

        return fig

    def create_fractional_flow_curve(self):
        """Создание графика функции Баклея-Леверетта"""
        # Создаем массив насыщенностей
        sw_values = np.linspace(0.0, 1.0, 100)
        f_values = np.zeros_like(sw_values)

        # Вычисляем функцию Баклея-Леверетта для каждой насыщенности
        for i, sw in enumerate(sw_values):
            f_values[i] = self.model.fractional_flow(sw)

        # Создаем фигуру
        fig = go.Figure()

        # Добавляем график
        fig.add_trace(
            go.Scatter(
                x=sw_values,
                y=f_values,
                mode='lines',
                line=dict(color='purple'),
                name='Функция Баклея-Леверетта'
            )
        )

        # Настройка осей и заголовка
        fig.update_xaxes(title_text='Водонасыщенность, д.ед.')
        fig.update_yaxes(title_text='Доля потока воды, д.ед.')
        fig.update_layout(
            title_text='Функция Баклея-Леверетта',
            height=500,
            hovermode='closest'
        )

        return fig

    def create_visualizations(self):
        """Создание всех визуализаций и возврат словаря с JSON-представлениями графиков"""
        days = [10, 50, 100]
        days = [day for day in days if day <= self.model.days]

        print("Создание визуализаций...")

        visualizations = {}
        try:
            # Профили насыщенности
            fig = self.create_saturation_profiles_figure(days)
            visualizations['saturation_profiles'] = fig.to_json()

            # Разница насыщенностей
            fig = self.create_saturation_difference_figure(days)
            visualizations['saturation_difference'] = fig.to_json()

            # Фактор восстановления
            fig = self.create_recovery_factor_figure()
            visualizations['recovery_factor'] = fig.to_json()

            # Время прорыва
            fig = self.create_breakthrough_time_figure()
            visualizations['breakthrough_time'] = fig.to_json()

            # Эволюция насыщенности
            fig = self.create_saturation_evolution_figure()
            visualizations['saturation_evolution'] = fig.to_json()

            # Капиллярное давление
            fig = self.create_capillary_pressure_curve()
            visualizations['capillary_pressure'] = fig.to_json()

            # Относительная проницаемость
            fig = self.create_relative_permeability_curves()
            visualizations['relative_permeability'] = fig.to_json()

            # Fractional flow
            fig = self.create_fractional_flow_curve()
            visualizations['fractional_flow'] = fig.to_json()

            # Добавление оригинальных данных для каждой визуализации
            for key, json_data in visualizations.items():
                try:
                    # Преобразуем JSON в словарь
                    data = json.loads(json_data)

                    # Если data содержит бинарные данные, добавляем оригинальные данные
                    if 'data' in data:
                        for trace in data['data']:
                            if 'x' in trace and isinstance(trace['x'], dict) and 'bdata' in trace['x']:
                                # Сохраняем оригинальные данные x
                                if isinstance(trace['x'].get('original'), list):
                                    pass  # Уже есть оригинальные данные
                                elif 'original' not in trace['x'] and 'data' in trace['x']:
                                    trace['x']['original'] = trace['x']['data']

                            if 'y' in trace and isinstance(trace['y'], dict) and 'bdata' in trace['y']:
                                # Сохраняем оригинальные данные y
                                if isinstance(trace['y'].get('original'), list):
                                    pass  # Уже есть оригинальные данные
                                elif 'original' not in trace['y'] and 'data' in trace['y']:
                                    trace['y']['original'] = trace['y']['data']

                    # Сохраняем обновленный JSON
                    visualizations[key] = json.dumps(data)
                except Exception as e:
                    print(f"Ошибка при обработке JSON для {key}: {e}")

        except Exception as e:
            print(f"ОШИБКА при создании визуализаций: {str(e)}")
            traceback.print_exc()

        print(f"Создано {len(visualizations)} визуализаций")
        return visualizations

    def save_visualizations(self, project_id):
        """Сохранение всех визуализаций в формате JSON"""
        project_dir = os.path.join(self.output_dir, str(project_id))
        os.makedirs(project_dir, exist_ok=True)

        visualizations = {}

        # ВАЖНОЕ ИЗМЕНЕНИЕ: используем простую сериализацию данных
        print(f"Создание визуализаций для проекта {project_id}...")

        # Создаем визуализации
        figs = {
            'saturation_profiles': self.create_saturation_profiles_figure([10, 50, 100]),
            'saturation_difference': self.create_saturation_difference_figure([10, 50, 100]),
            'recovery_factor': self.create_recovery_factor_figure(),
            'breakthrough_time': self.create_breakthrough_time_figure(),
            'saturation_evolution': self.create_saturation_evolution_figure(),
            'capillary_pressure': self.create_capillary_pressure_curve(),
            'fractional_flow': self.create_fractional_flow_curve(),
            'relative_permeability': self.create_relative_permeability_curves()
        }

        for name, fig in figs.items():
            file_path = os.path.join(project_dir, f'{name}.json')

            try:
                # Используем стандартную сериализацию без сложных структур
                json_data = fig.to_json()

                # Проверяем валидность JSON перед сохранением
                data = json.loads(json_data)

                # Удаляем любые бинарные данные, если они есть
                if 'data' in data:
                    for trace in data['data']:
                        for key in ['x', 'y', 'z']:
                            if key in trace and isinstance(trace[key], dict) and 'bdata' in trace[key]:
                                # Заменяем бинарные данные обычными массивами
                                if 'data' in trace[key] and isinstance(trace[key]['data'], list):
                                    trace[key] = trace[key]['data']

                # Сохраняем чистый JSON
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f)

                visualizations[name] = json_data
                print(f"Успешно сохранена визуализация: {name}")

            except Exception as e:
                print(f"ОШИБКА при сохранении визуализации {name}: {str(e)}")

        return visualizations

    def convert_to_plotly_format(fig, title=None):
        """Конвертирует график Matplotlib в формат Plotly JSON"""
        # Получаем данные из графика
        data = []

        for line in fig.axes[0].lines:
            trace = {
                'type': 'scatter',
                'mode': 'lines',
                'x': line.get_xdata().tolist(),
                'y': line.get_ydata().tolist(),
                'name': line.get_label() or None,
                'line': {
                    'width': line.get_linewidth(),
                    'color': line.get_color()
                }
            }
            data.append(trace)

        # Создаем layout
        layout = {
            'title': title or fig.axes[0].get_title(),
            'xaxis': {
                'title': fig.axes[0].get_xlabel(),
                'autorange': True
            },
            'yaxis': {
                'title': fig.axes[0].get_ylabel(),
                'autorange': True
            },
            'autosize': True,
            'showlegend': True,
            'font': {
                'family': 'Roboto, sans-serif',
                'size': 14
            },
            'plot_bgcolor': '#f8f8f8',
            'paper_bgcolor': '#ffffff'
        }

        # Объединяем все в один объект
        plotly_data = {'data': data, 'layout': layout}
        return plotly_data


    def check_visualization_data(self, viz_name, json_str):
        """Проверка корректности JSON-данных визуализации"""
        try:
            data = json.loads(json_str)
            print(f"Проверка визуализации {viz_name}:")
            print(f"  - Тип данных: {type(data)}")
            if 'data' not in data:
                print(f"  - ОШИБКА: Ключ 'data' отсутствует")
            elif not isinstance(data['data'], list):
                print(f"  - ОШИБКА: data['data'] не является списком: {type(data['data'])}")
            else:
                print(f"  - data['data'] содержит {len(data['data'])} элементов")

            if 'layout' not in data:
                print(f"  - ОШИБКА: Ключ 'layout' отсутствует")

            # Проверяем, что выходные данные содержат все необходимые поля для Plotly
            if 'data' in data and isinstance(data['data'], list) and 'layout' in data:
                print(f"  - Данные визуализации корректны для Plotly")
                return True
            else:
                print(f"  - Данные визуализации некорректны для Plotly")

                # Реконструируем правильную структуру
                corrected = {
                    "data": data.get('data', []) if isinstance(data.get('data', []), list) else [],
                    "layout": data.get('layout', {}) if isinstance(data.get('layout', {}), dict) else {}
                }
                return corrected

            return False
        except Exception as e:
            print(f"  - ОШИБКА при проверке данных визуализации: {str(e)}")
            return False

    def check_visualization_files(self, project_id):
        """Проверка файлов визуализации проекта"""
        project_dir = os.path.join(self.output_dir, str(project_id))

        if not os.path.exists(project_dir):
            print(f"Директория проекта не найдена: {project_dir}")
            return

        print(f"Проверка файлов визуализации в директории: {project_dir}")
        json_files = [f for f in os.listdir(project_dir) if f.endswith('.json')]

        if not json_files:
            print(f"Файлы визуализаций не найдены в директории: {project_dir}")
            return

        print(f"Найдено {len(json_files)} JSON-файлов: {', '.join(json_files)}")

        for json_file in json_files:
            file_path = os.path.join(project_dir, json_file)
            print(f"Проверка файла: {json_file}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)

                print(f"  - Размер файла: {os.path.getsize(file_path)} байт")
                print(f"  - Ключи верхнего уровня: {', '.join(json_data.keys())}")

                if 'data' not in json_data:
                    print(f"  - ОШИБКА: Ключ 'data' отсутствует!")

                    # Исправляем файл
                    corrected_data = {
                        "data": [],
                        "layout": {}
                    }

                    # Ищем массив данных в JSON
                    if 'traces' in json_data:
                        corrected_data["data"] = json_data["traces"]
                    elif 'frames' in json_data:
                        corrected_data["data"] = []

                    # Ищем макет в JSON
                    if 'layout' in json_data:
                        corrected_data["layout"] = json_data["layout"]

                    # Сохраняем исправленный файл
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(corrected_data, f)
                    print(f"  - Файл исправлен и сохранен.")
                elif not isinstance(json_data['data'], list):
                    print(f"  - ОШИБКА: json_data['data'] не является списком: {type(json_data['data'])}")
                else:
                    print(f"  - json_data['data'] содержит {len(json_data['data'])} элементов")

                if 'layout' not in json_data:
                    print(f"  - ОШИБКА: Ключ 'layout' отсутствует!")
            except Exception as e:
                print(f"  - ОШИБКА при чтении/анализе файла: {str(e)}")

    def save_visualizations_as_images(self, project_id, user_id=None, format='png'):
        """
        Сохранение визуализаций в виде изображений

        Args:
            project_id (int): ID проекта
            user_id (int, optional): ID пользователя. Defaults to None.
            format (str, optional): Формат сохранения ('png', 'svg', 'pdf', 'jpeg'). Defaults to 'png'.

        Returns:
            dict: Словарь с путями к сохраненным изображениям
        """
        # Создаем структуру директорий
        if user_id:
            # Если указан ID пользователя, сохраняем в папке пользователя/проекта
            image_dir = os.path.join(self.image_output_dir, f"user_{user_id}", f"project_{project_id}")
        else:
            # Иначе сохраняем только в папке проекта
            image_dir = os.path.join(self.image_output_dir, f"project_{project_id}")

        os.makedirs(image_dir, exist_ok=True)

        print(f"Сохранение визуализаций в формате {format} в директорию: {image_dir}")

        # Проверяем установлена ли библиотека kaleido
        try:
            import kaleido
            print("Библиотека kaleido найдена. Продолжаем сохранение изображений...")
        except ImportError:
            print("ВНИМАНИЕ: Библиотека kaleido не установлена. Устанавливаем...")
            try:
                import subprocess
                subprocess.check_call(['pip', 'install', 'kaleido'])
                print("Kaleido успешно установлена.")
            except Exception as e:
                print(f"Не удалось установить kaleido: {e}")
                print("Пробуем альтернативный метод сохранения...")

        # Словарь для хранения путей к файлам
        image_paths = {}

        # Список визуализаций для сохранения
        visualizations = {
            'saturation_profiles': self.create_saturation_profiles_figure([10, 50, 100]),
            'saturation_difference': self.create_saturation_difference_figure([10, 50, 100]),
            'recovery_factor': self.create_recovery_factor_figure(),
            'breakthrough_time': self.create_breakthrough_time_figure(),
            'saturation_evolution': self.create_saturation_evolution_figure(),
            'capillary_pressure': self.create_capillary_pressure_curve(),
            'relative_permeability': self.create_relative_permeability_curves(),
            'fractional_flow': self.create_fractional_flow_curve()
        }

        # Сохраняем каждую визуализацию
        for name, fig in visualizations.items():
            try:
                file_path = os.path.join(image_dir, f"{name}.{format}")
                print(f"Попытка сохранения {name} в формате {format} по пути: {file_path}")

                try:
                    # Сначала пытаемся с kaleido (стандартный метод Plotly)
                    if format == 'svg':
                        fig.write_image(file_path, width=1200, height=800)
                    else:
                        fig.write_image(file_path, width=1200, height=800, scale=2)
                except Exception as e:
                    print(f"Ошибка при использовании стандартного метода: {e}")
                    print("Пробуем альтернативный метод...")

                    # Альтернативный метод: сохраняем HTML и конвертируем с помощью браузера
                    html_path = os.path.join(image_dir, f"{name}_temp.html")
                    fig.write_html(html_path, include_plotlyjs='cdn')

                    try:
                        # Пытаемся использовать selenium для рендеринга
                        from selenium import webdriver
                        from selenium.webdriver.chrome.options import Options

                        print("Используем Selenium для рендеринга...")
                        chrome_options = Options()
                        chrome_options.add_argument("--headless")
                        chrome_options.add_argument("--disable-gpu")
                        chrome_options.add_argument("--no-sandbox")

                        driver = webdriver.Chrome(options=chrome_options)
                        driver.get('file://' + os.path.abspath(html_path))
                        # Даем время для полной загрузки
                        import time
                        time.sleep(2)

                        # Получаем размеры элемента с графиком
                        plot_div = driver.find_element_by_xpath("//div[contains(@class, 'plotly-graph-div')]")
                        driver.set_window_size(1200, 800)

                        # Делаем скриншот
                        driver.save_screenshot(file_path)
                        driver.quit()

                        # Удаляем временный HTML файл
                        os.remove(html_path)
                    except Exception as selenium_error:
                        print(f"Ошибка при использовании Selenium: {selenium_error}")

                        # Если и Selenium не сработал, просто сообщаем об ошибке
                        print("Все методы сохранения изображений не удались.")
                        continue

                # Проверяем, что файл действительно создан
                if os.path.exists(file_path):
                    image_paths[name] = file_path
                    file_size = os.path.getsize(file_path)
                    print(f"Сохранено изображение: {file_path} (размер: {file_size} байт)")
                else:
                    print(f"ОШИБКА: Файл не был создан по пути {file_path}, хотя ошибок не возникло")
            except Exception as e:
                print(f"ОШИБКА при сохранении изображения {name}: {str(e)}")
                import traceback
                traceback.print_exc()

        print(f"Всего сохранено изображений: {len(image_paths)}")
        return image_paths

    def save_all_visualization_formats(self, project_id, user_id=None):
        """
        Сохранение визуализаций во всех форматах (JSON, PNG, SVG)

        Args:
            project_id (int): ID проекта
            user_id (int, optional): ID пользователя. Defaults to None.

        Returns:
            dict: Словарь с информацией о сохраненных файлах
        """
        results = {
            'json': {},
            'png': {},
            'svg': {}
        }

        # Сохраняем JSON визуализации
        try:
            json_results = self.save_visualizations(project_id)
            results['json'] = {name: True for name in json_results}
        except Exception as e:
            print(f"ОШИБКА при сохранении JSON-визуализаций: {str(e)}")
            traceback.print_exc()

        # Сохраняем PNG изображения
        try:
            png_paths = self.save_visualizations_as_images(project_id, user_id, format='png')
            results['png'] = {name: path for name, path in png_paths.items()}
        except Exception as e:
            print(f"ОШИБКА при сохранении PNG-изображений: {str(e)}")
            traceback.print_exc()

        # Сохраняем SVG изображения
        try:
            svg_paths = self.save_visualizations_as_images(project_id, user_id, format='svg')
            results['svg'] = {name: path for name, path in svg_paths.items()}
        except Exception as e:
            print(f"ОШИБКА при сохранении SVG-изображений: {str(e)}")
            traceback.print_exc()

        return results