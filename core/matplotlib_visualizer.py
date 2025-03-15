#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
import matplotlib.colors as mcolors
from matplotlib import cm

# Настраиваем стиль для графиков
plt.style.use('default')
plt.rcParams['axes.grid'] = True
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12


class MatplotlibVisualizer:
    """Класс для визуализации результатов моделирования с использованием matplotlib"""

    def __init__(self, model, output_dir=None, image_output_dir=None):
        self.model = model
        self.output_dir = output_dir or 'data/results'
        self.image_output_dir = image_output_dir or 'data/images'
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_output_dir, exist_ok=True)

    def save_visualizations_as_images(self, project_id, user_id=None, formats=None):
        """
        Сохранение визуализаций в виде изображений

        Args:
            project_id (int): ID проекта
            user_id (int, optional): ID пользователя. Defaults to None.
            formats (list, optional): Форматы сохранения. Defaults to ['png', 'svg'].

        Returns:
            dict: Словарь с путями к сохраненным изображениям
        """
        if formats is None:
            formats = ['png', 'svg']

        # Создаем структуру директорий
        if user_id:
            # Если указан ID пользователя, сохраняем в папке пользователя/проекта
            image_dir = os.path.join(self.image_output_dir, f"user_{user_id}", f"project_{project_id}")
        else:
            # Иначе сохраняем только в папке проекта
            image_dir = os.path.join(self.image_output_dir, f"project_{project_id}")

        os.makedirs(image_dir, exist_ok=True)

        print(f"Сохранение визуализаций в форматах {formats} в директорию: {image_dir}")

        # Словарь для хранения путей к файлам
        image_paths = {fmt: {} for fmt in formats}

        # Строим и сохраняем все визуализации
        visualization_functions = {
            'saturation_profiles': self.create_saturation_profiles,
            'saturation_difference': self.create_saturation_difference,
            'recovery_factor': self.create_recovery_factor,
            'breakthrough_time': self.create_breakthrough_time,
            'saturation_evolution': self.create_saturation_evolution,
            'capillary_pressure': self.create_capillary_pressure,
            'relative_permeability': self.create_relative_permeability,
            'fractional_flow': self.create_fractional_flow
        }

        # Создаем и сохраняем каждую визуализацию
        for name, func in visualization_functions.items():
            try:
                print(f"Создание визуализации: {name}")
                fig = func()

                for fmt in formats:
                    file_path = os.path.join(image_dir, f"{name}.{fmt}")
                    fig.savefig(file_path, dpi=300, bbox_inches='tight')
                    print(f"Сохранено изображение: {file_path}")
                    image_paths[fmt][name] = file_path

                plt.close(fig)  # Важно закрывать фигуры после сохранения
            except Exception as e:
                print(f"ОШИБКА при создании/сохранении визуализации {name}: {str(e)}")
                import traceback
                traceback.print_exc()

        print(f"Всего сохранено изображений: {sum(len(paths) for paths in image_paths.values())}")
        return image_paths

    def create_saturation_profiles(self, days=None):
        """
        Создание графика профилей насыщенности

        Returns:
            matplotlib.figure.Figure: Фигура с графиком
        """
        if days is None:
            days = [10, 50, 100]

        # Отфильтруем дни, которые превышают время моделирования
        days = [day for day in days if day <= self.model.days]

        # Создаем фигуру с подграфиками
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14), sharex=True)

        linestyles = ['-', '--', '-.']
        colors = ['blue', 'green', 'red']

        for i, day in enumerate(days):
            time_index = int(day / self.model.dt)

            # Получаем данные насыщенности
            with_cap_data, without_cap_data = self.get_saturation_profile(time_index)

            # Верхний график - без капиллярных эффектов
            ax1.plot(self.model.x, without_cap_data, linestyle=linestyles[i % len(linestyles)],
                     color=colors[i % len(colors)], linewidth=3, label=f'День {day}')

            # Нижний график - с капиллярными эффектами
            ax2.plot(self.model.x, with_cap_data, linestyle=linestyles[i % len(linestyles)],
                     color=colors[i % len(colors)], linewidth=3, label=f'День {day}')

        ax1.set_title('Профиль насыщенности без учета капиллярных эффектов', fontsize=18)
        ax1.set_ylabel('Водонасыщенность Sw, д.ед.', fontsize=16)
        ax1.legend(fontsize=14)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.set_ylim(0, 1)

        ax2.set_title('Профиль насыщенности с учетом капиллярных эффектов', fontsize=18)
        ax2.set_xlabel('Расстояние, м', fontsize=16)
        ax2.set_ylabel('Водонасыщенность Sw, д.ед.', fontsize=16)
        ax2.legend(fontsize=14)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.set_ylim(0, 1)

        plt.tight_layout()
        return fig

    def create_saturation_difference(self, days=None):
        """
        Создание графика разницы насыщенностей

        Returns:
            matplotlib.figure.Figure: Фигура с графиком
        """
        if days is None:
            days = [10, 50, 100]

        # Отфильтруем дни, которые превышают время моделирования
        days = [day for day in days if day <= self.model.days]

        # Создаем фигуру
        fig, axs = plt.subplots(len(days), 1, figsize=(12, 4 * len(days)), sharex=True)

        # Если только один день, превращаем axs в список для единообразия
        if len(days) == 1:
            axs = [axs]

        for i, day in enumerate(days):
            time_index = int(day / self.model.dt)

            # Получаем данные насыщенности
            with_cap_data, without_cap_data = self.get_saturation_profile(time_index)

            # Вычисляем разницу
            diff = with_cap_data - without_cap_data

            # Строим график разницы
            axs[i].plot(self.model.x, diff, linewidth=3, color='purple')
            axs[i].axhline(y=0, color='k', linestyle='--', alpha=0.7)
            axs[i].set_title(f'Разница в насыщенности (с кап. - без кап.), день {day}', fontsize=16)
            axs[i].set_ylabel('Разница Sw, д.ед.', fontsize=14)
            axs[i].grid(True, linestyle='--', alpha=0.7)

            # Добавляем выделение зон капиллярного противотока
            positive_mask = diff > 0.005
            negative_mask = diff < -0.005

            if positive_mask.any():
                axs[i].fill_between(self.model.x, diff, 0, where=positive_mask,
                                    color='green', alpha=0.3, label='Зона повышенной насыщенности')
            if negative_mask.any():
                axs[i].fill_between(self.model.x, diff, 0, where=negative_mask,
                                    color='red', alpha=0.3, label='Зона пониженной насыщенности')

            # Добавляем легенду, если есть выделенные зоны
            if positive_mask.any() or negative_mask.any():
                axs[i].legend(fontsize=12)

        axs[-1].set_xlabel('Расстояние, м', fontsize=16)
        plt.tight_layout()
        return fig

    def create_recovery_factor(self):
        """
        Создание графика коэффициента нефтеотдачи

        Returns:
            matplotlib.figure.Figure: Фигура с графиком
        """
        # Получаем данные о коэффициенте нефтеотдачи
        recovery_with_cap, recovery_without_cap = self.model.calculate_recovery_factor()

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(12, 8))

        # Строим графики
        ax.plot(self.model.t, recovery_without_cap, linewidth=3, color='blue',
                label='Без капиллярных эффектов')
        ax.plot(self.model.t, recovery_with_cap, linewidth=3, color='red',
                label='С капиллярными эффектами')

        # Добавляем аннотации с разницей в ключевых точках
        time_points = [10, 30, 50, 70, 100]
        for day in time_points:
            if day <= self.model.days:
                time_index = int(day / self.model.dt)
                diff = recovery_with_cap[time_index] - recovery_without_cap[time_index]
                average_recovery = (recovery_with_cap[time_index] + recovery_without_cap[time_index]) / 2

                ax.annotate(f"{diff:.3f}",
                            xy=(day, average_recovery),
                            xytext=(5, 0),
                            textcoords="offset points",
                            ha='left', va='center',
                            fontsize=12,
                            arrowprops=dict(arrowstyle="->", color='black'))

        ax.set_xlabel('Время, дни', fontsize=16)
        ax.set_ylabel('Коэффициент нефтеотдачи, д.ед.', fontsize=16)
        ax.set_title('Динамика коэффициента нефтеотдачи', fontsize=18)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(fontsize=14)

        plt.tight_layout()
        return fig

    def create_breakthrough_time(self):
        """
        Создание графика времени прорыва воды

        Returns:
            matplotlib.figure.Figure: Фигура с графиком
        """
        # Получаем время прорыва
        breakthrough_with_cap, breakthrough_without_cap = self.model.get_breakthrough_time()

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(10, 8))

        # Строим столбцы гистограммы
        categories = ['Без капиллярных\nэффектов', 'С капиллярными\nэффектами']
        values = [breakthrough_without_cap, breakthrough_with_cap]

        bars = ax.bar(categories, values, color=['blue', 'red'], width=0.6)

        # Добавляем значения над столбцами
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 1,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=14)

        # Добавляем процентное изменение
        percent_change = ((breakthrough_with_cap - breakthrough_without_cap) /
                          breakthrough_without_cap * 100)
        ax.text(1.5, max(values) * 0.5,
                f"Изменение:\n{percent_change:.1f}%",
                ha='center', va='center', fontsize=14,
                bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))

        ax.set_ylabel('Время, дни', fontsize=16)
        ax.set_title('Время прорыва воды', fontsize=18)
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')

        plt.tight_layout()
        return fig

    def create_saturation_evolution(self):
        """
        Создание контурного графика эволюции насыщенности

        Returns:
            matplotlib.figure.Figure: Фигура с графиком
        """
        # Создаем фигуру с подграфиками
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), sharey=True)

        # Создаем сетку X и T для контурного графика
        X, T = np.meshgrid(self.model.x, self.model.t)

        # Контурный график для модели без капиллярных эффектов
        contour1 = ax1.contourf(X, T, self.model.Sw_without_cap, levels=20, cmap='viridis')
        ax1.set_xlabel('Расстояние, м', fontsize=14)
        ax1.set_ylabel('Время, дни', fontsize=14)
        ax1.set_title('Эволюция насыщенности без учета капиллярных эффектов', fontsize=16)
        fig.colorbar(contour1, ax=ax1, label='Водонасыщенность, д.ед.')

        # Контурный график для модели с капиллярными эффектами
        contour2 = ax2.contourf(X, T, self.model.Sw_with_cap, levels=20, cmap='viridis')
        ax2.set_xlabel('Расстояние, м', fontsize=14)
        ax2.set_title('Эволюция насыщенности с учетом капиллярных эффектов', fontsize=16)
        fig.colorbar(contour2, ax=ax2, label='Водонасыщенность, д.ед.')

        plt.tight_layout()
        return fig

    def create_capillary_pressure(self):
        """
        Создание графика кривой капиллярного давления

        Returns:
            matplotlib.figure.Figure: Фигура с графиком
        """
        # Создаем массив насыщенностей
        sw_values = np.linspace(0.0, 1.0, 100)
        pc_values = np.zeros_like(sw_values)

        # Вычисляем капиллярное давление для каждого значения насыщенности
        for i, sw in enumerate(sw_values):
            pc_values[i] = self.model.capillary_pressure(sw)

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(12, 8))

        # Строим график
        ax.plot(sw_values, pc_values, 'o-', linewidth=3, color='blue')

        # Добавляем нулевую линию
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.7)

        # Находим границы зон смачиваемости
        swc = self.model.initial_water_saturation
        sor = self.model.residual_oil_saturation

        # Выделяем зоны
        ax.fill_between(sw_values[sw_values <= 0.3], pc_values[sw_values <= 0.3],
                        alpha=0.3, color='red', label='Гидрофобная зона')
        ax.fill_between(sw_values[(sw_values > 0.3) & (sw_values < 0.8)],
                        pc_values[(sw_values > 0.3) & (sw_values < 0.8)],
                        alpha=0.3, color='purple', label='Переходная зона')
        ax.fill_between(sw_values[sw_values >= 0.8], pc_values[sw_values >= 0.8],
                        alpha=0.3, color='green', label='Гидрофильная зона')

        ax.set_xlabel('Водонасыщенность Sw, д.ед.', fontsize=16)
        ax.set_ylabel('Капиллярное давление Pc, МПа', fontsize=16)
        ax.set_title('Кривая капиллярного давления', fontsize=20)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(fontsize=14)

        plt.tight_layout()
        return fig

    def create_relative_permeability(self):
        """
        Создание графика кривых относительной проницаемости

        Returns:
            matplotlib.figure.Figure: Фигура с графиком
        """
        # Создаем массив насыщенностей
        sw_values = np.linspace(0.0, 1.0, 100)
        krw_values = np.zeros_like(sw_values)
        kro_values = np.zeros_like(sw_values)

        # Вычисляем относительные проницаемости
        for i, sw in enumerate(sw_values):
            krw_values[i] = self.model.relative_permeability_water(sw)
            kro_values[i] = self.model.relative_permeability_oil(sw)

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(12, 8))

        # Строим графики
        ax.plot(sw_values, krw_values, 'o-', linewidth=3, color='blue', label='Krw (вода)')
        ax.plot(sw_values, kro_values, 'o-', linewidth=3, color='green', label='Kro (нефть)')

        # Находим критические точки
        swc = self.model.initial_water_saturation
        sor = self.model.residual_oil_saturation

        # Находим точку пересечения
        intersection_idx = np.argmin(np.abs(krw_values - kro_values))
        sw_intersection = sw_values[intersection_idx]
        kr_intersection = krw_values[intersection_idx]

        # Добавляем вертикальные линии в критических точках
        ax.axvline(x=swc, color='blue', linestyle='--', alpha=0.7, label=f'Swc = {swc:.2f}')
        ax.axvline(x=1 - sor, color='green', linestyle='--', alpha=0.7, label=f'1-Sor = {1 - sor:.2f}')
        ax.plot(sw_intersection, kr_intersection, 'ro', markersize=10,
                label=f'Пересечение при Sw = {sw_intersection:.2f}')

        ax.set_xlabel('Водонасыщенность Sw, д.ед.', fontsize=16)
        ax.set_ylabel('Относительная проницаемость Kr, д.ед.', fontsize=16)
        ax.set_title('Кривые относительной проницаемости', fontsize=20)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        plt.tight_layout()
        return fig

    def create_fractional_flow(self):
        """
        Создание графика функции Баклея-Леверетта

        Returns:
            matplotlib.figure.Figure: Фигура с графиком
        """
        # Создаем массив насыщенностей
        sw_values = np.linspace(0.0, 1.0, 100)
        f_values = np.zeros_like(sw_values)

        # Вычисляем функцию Баклея-Леверетта
        for i, sw in enumerate(sw_values):
            f_values[i] = self.model.fractional_flow(sw)

        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(12, 8))

        # Строим график
        ax.plot(sw_values, f_values, linewidth=3, color='purple')

        # Находим производную функции Баклея-Леверетта
        df_values = np.gradient(f_values, sw_values)

        # Находим точку максимума производной (фронтальная насыщенность)
        front_idx = np.argmax(df_values)
        front_sw = sw_values[front_idx]
        front_f = f_values[front_idx]

        # Добавляем эту точку на график
        ax.plot(front_sw, front_f, 'ro', markersize=10,
                label=f'Фронтальная насыщенность Sw = {front_sw:.2f}')

        # Добавляем касательную в этой точке
        tangent_x = np.array([0, front_sw])
        tangent_y = np.array([front_f - front_sw * df_values[front_idx], front_f])
        ax.plot(tangent_x, tangent_y, 'r--', linewidth=2, label='Касательная (скорость фронта)')

        ax.set_xlabel('Водонасыщенность Sw, д.ед.', fontsize=16)
        ax.set_ylabel('Доля потока воды f(Sw), д.ед.', fontsize=16)
        ax.set_title('Функция Баклея-Леверетта', fontsize=18)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        plt.tight_layout()
        return fig

    def get_saturation_profile(self, time_index):
        """
        Получение профилей насыщенности для заданного момента времени

        Args:
            time_index (int): Индекс времени

        Returns:
            tuple: (with_cap_data, without_cap_data) - профили насыщенности
        """
        # Если используется карбонатная модель
        if hasattr(self.model, 'Sw_matrix') and hasattr(self.model, 'Sw_fracture'):
            # Рассчитываем насыщенность с учетом капиллярных эффектов как взвешенное среднее
            matrix_volume = self.model.matrix_porosity / self.model.porosity
            fracture_volume = self.model.fracture_porosity / self.model.porosity
            with_cap_data = matrix_volume * self.model.Sw_matrix[time_index, :] + \
                            fracture_volume * self.model.Sw_fracture[time_index, :]

            # Для данных без учета капиллярных эффектов используем имеющийся массив
            without_cap_data = self.model.Sw_without_cap[time_index, :]
        else:
            # Для базовой модели используем имеющиеся массивы
            with_cap_data = self.model.Sw_with_cap[time_index, :]
            without_cap_data = self.model.Sw_without_cap[time_index, :]

        return with_cap_data, without_cap_data