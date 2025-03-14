#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from core.model import OilFiltrationModel


class CarbonateModel(OilFiltrationModel):
    """
    Расширенная модель для карбонатных коллекторов с учетом
    двойной пористости и детального моделирования капиллярных эффектов
    """

    def __init__(self, params=None):
        # Инициализация базовой модели
        super().__init__(params)

        # Дополнительные параметры для карбонатных коллекторов
        self.fracture_porosity = 0.01  # Пористость трещин
        self.matrix_porosity = self.porosity - self.fracture_porosity  # Пористость матрицы
        self.fracture_permeability = 100.0  # Проницаемость трещин, мД
        self.matrix_permeability = 0.1  # Проницаемость матрицы, мД

        # Параметры для моделирования двойной пористости
        self.shape_factor = 0.1  # Форм-фактор для обмена между трещинами и матрицей

        # Если переданы пользовательские параметры, обновляем значения
        if params:
            for key, value in params.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, float(value))

        # Пересчитываем зависимые параметры
        self.matrix_porosity = self.porosity - self.fracture_porosity

        # Массивы для хранения результатов для матрицы и трещин
        self.Sw_matrix = np.ones((self.nt, self.nx + 1)) * self.initial_water_saturation
        self.Sw_fracture = np.ones((self.nt, self.nx + 1)) * self.initial_water_saturation

        # Устанавливаем граничные условия
        self.Sw_matrix[:, 0] = 0.8
        self.Sw_fracture[:, 0] = 0.8

    def run_dual_porosity_simulation(self):
        """Запуск моделирования с учетом двойной пористости"""
        print("Запуск моделирования карбонатного коллектора с двойной пористостью...")

        # Моделирование течения в трещинах (быстрое течение)
        for n in range(self.nt - 1):
            for i in range(1, self.nx):
                # Апвинд схема для конвективного члена в трещинах
                f_i = self.fractional_flow(self.Sw_fracture[n, i])
                f_im1 = self.fractional_flow(self.Sw_fracture[n, i - 1])

                # Схема апвинд для трещин (без капиллярных эффектов в трещинах)
                self.Sw_fracture[n + 1, i] = self.Sw_fracture[n, i] - \
                                             (self.dt / self.dx) * (f_i - f_im1) + \
                                             self.dt * self.transfer_term(n, i)

            # Граничное условие на правом конце
            self.Sw_fracture[n + 1, -1] = self.Sw_fracture[n + 1, -2]

        # Моделирование течения в матрице (медленное течение с капиллярными эффектами)
        for n in range(self.nt - 1):
            for i in range(1, self.nx):
                # Капиллярное давление в матрице
                pc_gradient = self.matrix_capillary_gradient(n, i)

                # Обновление насыщенности в матрице
                self.Sw_matrix[n + 1, i] = self.Sw_matrix[n, i] + \
                                           self.dt * pc_gradient - \
                                           self.dt * self.transfer_term(n, i)

            # Граничное условие на правом конце
            self.Sw_matrix[n + 1, -1] = self.Sw_matrix[n + 1, -2]

        # Вычисление итоговой насыщенности как взвешенного среднего
        matrix_volume = self.matrix_porosity / self.porosity
        fracture_volume = self.fracture_porosity / self.porosity

        self.Sw_with_cap = matrix_volume * self.Sw_matrix + fracture_volume * self.Sw_fracture

        # Запускаем обычное моделирование для сравнения (без капиллярных эффектов)
        super().run_simulation()

        print("Моделирование карбонатного коллектора завершено.")

    def transfer_term(self, n, i):
        """Расчет обмена флюидами между трещинами и матрицей"""
        # Разница в капиллярном давлении
        pc_matrix = self.capillary_pressure(self.Sw_matrix[n, i])
        pc_fracture = 0  # В трещинах капиллярное давление принимаем равным нулю

        # Скорость обмена пропорциональна разнице давлений и коэффициенту обмена
        exchange_rate = self.shape_factor * (pc_fracture - pc_matrix)

        return exchange_rate

    def matrix_capillary_gradient(self, n, i):
        """Расчет градиента капиллярного давления в матрице"""
        # Рассчитываем градиент капиллярного давления
        if i == 0:
            # Граничное условие слева
            pc_grad = (self.capillary_pressure(self.Sw_matrix[n, i + 1]) -
                       self.capillary_pressure(self.Sw_matrix[n, i])) / self.dx
        elif i == self.nx:
            # Граничное условие справа
            pc_grad = (self.capillary_pressure(self.Sw_matrix[n, i]) -
                       self.capillary_pressure(self.Sw_matrix[n, i - 1])) / self.dx
        else:
            # Внутренние точки
            pc_grad = (self.capillary_pressure(self.Sw_matrix[n, i + 1]) -
                       self.capillary_pressure(self.Sw_matrix[n, i - 1])) / (2 * self.dx)

        # Коэффициент мобильности
        mobility = self.matrix_permeability / (self.mu_water * self.matrix_porosity)

        return mobility * pc_grad

    def calculate_recovery_factor(self):
        """Расчет коэффициента нефтеотдачи с учетом двойной пористости"""
        initial_oil = 1 - self.initial_water_saturation

        recovery_with_cap = np.zeros(self.nt)
        recovery_without_cap = np.zeros(self.nt)

        # Вычисляем взвешенное среднее для матрицы и трещин
        matrix_volume = self.matrix_porosity / self.porosity
        fracture_volume = self.fracture_porosity / self.porosity

        for n in range(self.nt):
            # Средняя нефтенасыщенность для двойной пористости
            avg_oil_matrix = 1 - np.mean(self.Sw_matrix[n, :])
            avg_oil_fracture = 1 - np.mean(self.Sw_fracture[n, :])
            avg_oil_with_cap = matrix_volume * avg_oil_matrix + fracture_volume * avg_oil_fracture

            # Средняя нефтенасыщенность без учета капиллярных эффектов
            avg_oil_without_cap = 1 - np.mean(self.Sw_without_cap[n, :])

            # Коэффициент нефтеотдачи
            recovery_with_cap[n] = (initial_oil - avg_oil_with_cap) / initial_oil
            recovery_without_cap[n] = (initial_oil - avg_oil_without_cap) / initial_oil

        return recovery_with_cap, recovery_without_cap

    def extract_results(self):
        """Извлечение результатов для сохранения и передачи на фронтенд"""
        # Получаем базовые результаты
        results = super().extract_results()

        # Добавляем специфичные для карбонатной модели параметры
        results['parameters'].update({
            'fracture_porosity': self.fracture_porosity,
            'matrix_porosity': self.matrix_porosity,
            'fracture_permeability': self.fracture_permeability,
            'matrix_permeability': self.matrix_permeability,
            'shape_factor': self.shape_factor
        })

        # Добавляем данные о насыщенности в матрице и трещинах
        time_points = [10, 50, 100]
        matrix_fracture_profiles = {}

        for day in time_points:
            if day <= self.days:
                time_index = int(day / self.dt)
                matrix_fracture_profiles[day] = {
                    'distance': self.x.tolist(),
                    'matrix': self.Sw_matrix[time_index, :].tolist(),
                    'fracture': self.Sw_fracture[time_index, :].tolist()
                }

        results['matrix_fracture_profiles'] = matrix_fracture_profiles

        return results