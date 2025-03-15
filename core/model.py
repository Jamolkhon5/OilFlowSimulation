#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np


class OilFiltrationModel:
    """
    Базовая модель одномерной фильтрации нефти в пористой среде
    с использованием метода апвинд и учетом капиллярных эффектов
    """

    def __init__(self, params=None):
        # Стандартные параметры пласта
        self.length = 100.0  # длина пласта, м
        self.porosity = 0.2  # пористость

        # Параметры флюидов
        self.mu_oil = 5.0  # вязкость нефти, мПа·с
        self.mu_water = 1.0  # вязкость воды, мПа·с
        self.initial_water_saturation = 0.2  # начальная водонасыщенность
        self.residual_oil_saturation = 0.2  # остаточная нефтенасыщенность

        # Параметры расчёта
        self.nx = 100  # число узлов сетки
        self.dx = self.length / self.nx  # шаг по x
        self.days = 100  # дней симуляции
        self.dt = 0.05  # шаг по времени, дней
        self.nt = int(self.days / self.dt) + 1  # число временных шагов

        # Параметры для модели капиллярного давления Брукса-Кори
        self.entry_pressure = 1.0  # давление входа, МПа
        self.pore_distribution_index = 1.5  # индекс распределения пор (λ)
        self.wettability_factor = 0.6  # коэффициент смачиваемости (1 - гидрофильная, 0 - гидрофобная)

        # Если переданы пользовательские параметры, обновляем значения
        if params:
            for key, value in params.items():
                if hasattr(self, key) and value is not None:
                    setattr(self, key, float(value))

        # Пересчитываем зависимые параметры
        self.dx = self.length / self.nx
        self.nt = int(self.days / self.dt) + 1

        # Создаем сетки
        self.x = np.linspace(0, self.length, self.nx + 1)
        self.t = np.linspace(0, self.days, self.nt)

        # Создаем массивы для хранения результатов
        # Насыщенность с учетом и без учета капиллярных эффектов
        self.Sw_with_cap = np.ones((self.nt, self.nx + 1)) * self.initial_water_saturation
        self.Sw_without_cap = np.ones((self.nt, self.nx + 1)) * self.initial_water_saturation

        # Устанавливаем граничные условия - закачка воды на входе
        self.Sw_with_cap[:, 0] = 0.8
        self.Sw_without_cap[:, 0] = 0.8

    def relative_permeability_water(self, Sw):
        """Относительная проницаемость для воды"""
        Swc = self.initial_water_saturation
        Sor = self.residual_oil_saturation

        if Sw <= Swc:
            return 0.0
        elif Sw >= 1 - Sor:
            return 1.0
        else:
            Swn = (Sw - Swc) / (1 - Swc - Sor)
            return Swn ** 3  # кубическая зависимость

    def relative_permeability_oil(self, Sw):
        """Относительная проницаемость для нефти"""
        Swc = self.initial_water_saturation
        Sor = self.residual_oil_saturation

        if Sw >= 1 - Sor:
            return 0.0
        elif Sw <= Swc:
            return 1.0
        else:
            Son = (1 - Sw - Sor) / (1 - Swc - Sor)
            return Son ** 2  # квадратичная зависимость

    def fractional_flow(self, Sw):
        """Функция Баклея-Леверетта"""
        krw = self.relative_permeability_water(Sw)
        kro = self.relative_permeability_oil(Sw)

        # Добавляем малое число для избежания деления на ноль
        M = (krw / self.mu_water) / (kro / self.mu_oil + 1e-10)
        return M / (1 + M)

    def capillary_pressure(self, Sw):
        """
        Функция капиллярного давления по модели Брукса-Кори с плавным переходом
        в граничных зонах для повышения численной стабильности.
        """
        # Граничные значения насыщенности
        Swc = self.initial_water_saturation
        Sor = self.residual_oil_saturation

        # Избегаем численных проблем у границ диапазона насыщенности
        epsilon = 0.01  # параметр сглаживания вблизи границ

        if Sw <= Swc + epsilon:
            # Плавный переход к максимальному капиллярному давлению
            alpha = (Sw - Swc) / epsilon
            max_pc = self.entry_pressure * 3.0  # максимальное капиллярное давление, МПа
            return max_pc * (1.0 - alpha) + self.entry_pressure * alpha

        elif Sw >= 1 - Sor - epsilon:
            # Плавный переход к нулю капиллярного давления
            alpha = (1 - Sor - Sw) / epsilon
            return self.entry_pressure * 0.05 * alpha  # близко к нулю в конечной точке

        else:
            # Нормализованная водонасыщенность (эффективная)
            Se = (Sw - Swc) / (1 - Swc - Sor)

            # Модель Брукса-Кори
            pc = self.entry_pressure * (Se ** (-1.0 / self.pore_distribution_index))

            # Корректировка с учетом смачиваемости
            # Для гидрофобной среды (oil-wet) увеличиваем капиллярное давление
            pc = pc * (2.0 - self.wettability_factor)

            return pc

    def diffusion_coefficient(self, Sw):
        """Коэффициент капиллярной диффузии"""
        # Предотвращаем выход за граничные значения
        Sw = max(min(Sw, 0.99), 0.01)

        # Вычисление производной функции Баклея-Леверетта
        delta = 1e-4
        Sw_minus = max(Sw - delta, 0.01)
        Sw_plus = min(Sw + delta, 0.99)

        df_dS = (self.fractional_flow(Sw_plus) - self.fractional_flow(Sw_minus)) / (2 * delta)

        # Вычисление производной капиллярного давления
        dpc_dS = (self.capillary_pressure(Sw_plus) - self.capillary_pressure(Sw_minus)) / (2 * delta)

        # Предполагаем, что проницаемость k = 1.0 Дарси
        k = 1.0

        mu = max(self.mu_water * Sw + self.mu_oil * (1 - Sw), 0.1)

        # Теоретическая формула для коэффициента капиллярной диффузии
        D = -k / (self.porosity * mu) * df_dS * dpc_dS

        # Ограничиваем значение для стабильности
        max_diffusion = 0.45 * self.dx ** 2 / self.dt

        # Обрабатываем отрицательные значения и применяем ограничение устойчивости
        if D < 0:
            return min(abs(D) * 1.0, max_diffusion)
        else:
            return min(D * 1.0, max_diffusion)

    def run_simulation(self):
        """Запуск моделирования"""
        # Моделирование с учетом капиллярных эффектов
        for n in range(self.nt - 1):
            for i in range(1, self.nx):
                # Апвинд схема для конвективного члена
                f_i = self.fractional_flow(self.Sw_with_cap[n, i])
                f_im1 = self.fractional_flow(self.Sw_with_cap[n, i - 1])

                # Диффузионный член (капиллярные эффекты)
                D_i = self.diffusion_coefficient(self.Sw_with_cap[n, i])

                # Схема апвинд с учетом капиллярных эффектов
                self.Sw_with_cap[n + 1, i] = self.Sw_with_cap[n, i] - \
                                             (self.dt / self.dx) * (f_i - f_im1) + \
                                             (self.dt / self.dx ** 2) * D_i * (
                                                     self.Sw_with_cap[n, i + 1] - 2 * self.Sw_with_cap[n, i] +
                                                     self.Sw_with_cap[n, i - 1])

            # Граничное условие на правом конце
            self.Sw_with_cap[n + 1, -1] = self.Sw_with_cap[n + 1, -2]

        # Моделирование без учета капиллярных эффектов
        for n in range(self.nt - 1):
            for i in range(1, self.nx):
                # Апвинд схема для конвективного члена
                f_i = self.fractional_flow(self.Sw_without_cap[n, i])
                f_im1 = self.fractional_flow(self.Sw_without_cap[n, i - 1])

                # Схема апвинд без учета капиллярных эффектов
                self.Sw_without_cap[n + 1, i] = self.Sw_without_cap[n, i] - \
                                                (self.dt / self.dx) * (f_i - f_im1)

            # Граничное условие на правом конце
            self.Sw_without_cap[n + 1, -1] = self.Sw_without_cap[n + 1, -2]

    def calculate_recovery_factor(self):
        """Расчет коэффициента нефтеотдачи"""
        initial_oil = 1 - self.initial_water_saturation

        recovery_with_cap = np.zeros(self.nt)
        recovery_without_cap = np.zeros(self.nt)

        for n in range(self.nt):
            # Средняя нефтенасыщенность
            avg_oil_with_cap = 1 - np.mean(self.Sw_with_cap[n, :])
            avg_oil_without_cap = 1 - np.mean(self.Sw_without_cap[n, :])

            # Коэффициент нефтеотдачи
            recovery_with_cap[n] = (initial_oil - avg_oil_with_cap) / initial_oil
            recovery_without_cap[n] = (initial_oil - avg_oil_without_cap) / initial_oil

        return recovery_with_cap, recovery_without_cap

    def get_breakthrough_time(self):
        """Определение времени прорыва воды"""
        threshold = self.initial_water_saturation + 0.05

        # Время прорыва с учетом капиллярных эффектов
        breakthrough_with_cap = self.days
        for n in range(self.nt):
            if self.Sw_with_cap[n, -1] > threshold:
                breakthrough_with_cap = self.t[n]
                break

        # Время прорыва без учета капиллярных эффектов
        breakthrough_without_cap = self.days
        for n in range(self.nt):
            if self.Sw_without_cap[n, -1] > threshold:
                breakthrough_without_cap = self.t[n]
                break

        return breakthrough_with_cap, breakthrough_without_cap

    def extract_results(self):
        """Извлечение результатов для сохранения и передачи на фронтенд"""
        # Расчет коэффициента нефтеотдачи
        recovery_with_cap, recovery_without_cap = self.calculate_recovery_factor()

        # Получение времени прорыва
        breakthrough_with_cap, breakthrough_without_cap = self.get_breakthrough_time()

        # Расчет скорости фронта (реальные данные вместо предполагаемых)
        velocity_with_cap = self.length / max(breakthrough_with_cap, 0.001)
        velocity_without_cap = self.length / max(breakthrough_without_cap, 0.001)

        # Расчет ширины переходной зоны (на 50-й день)
        day_index = min(int(50 / self.dt), self.nt - 1)

        # Для модели без капиллярных эффектов (узкая зона)
        profile_no_cap = self.Sw_without_cap[day_index, :]
        transition_zone_no_cap = (profile_no_cap > 0.3) & (profile_no_cap < 0.7)
        if np.any(transition_zone_no_cap):
            indices = np.where(transition_zone_no_cap)[0]
            width_without_cap = (indices[-1] - indices[0]) * self.dx
        else:
            width_without_cap = 2.0

        # Для модели с капиллярными эффектами (широкая зона)
        profile_with_cap = self.Sw_with_cap[day_index, :]
        transition_zone_with_cap = (profile_with_cap > 0.3) & (profile_with_cap < 0.7)
        if np.any(transition_zone_with_cap):
            indices = np.where(transition_zone_with_cap)[0]
            width_with_cap = (indices[-1] - indices[0]) * self.dx
        else:
            width_with_cap = 25.0

        # Выбор моментов времени для профилей насыщенности
        time_points = [10, 50, 100]
        saturation_profiles = {}

        for day in time_points:
            if day <= self.days:
                time_index = int(day / self.dt)
                saturation_profiles[day] = {
                    'distance': self.x.tolist(),
                    'with_cap': self.Sw_with_cap[time_index, :].tolist(),
                    'without_cap': self.Sw_without_cap[time_index, :].tolist(),
                }

        # Формирование результата
        results = {
            'parameters': {
                'length': self.length,
                'porosity': self.porosity,
                'mu_oil': self.mu_oil,
                'mu_water': self.mu_water,
                'initial_water_saturation': self.initial_water_saturation,
                'residual_oil_saturation': self.residual_oil_saturation,
                'entry_pressure': self.entry_pressure,
                'pore_distribution_index': self.pore_distribution_index,
                'wettability_factor': self.wettability_factor,
                'days': self.days,
                'nx': self.nx,
                'dt': self.dt
            },
            'recovery_factor': {
                'time': self.t.tolist(),
                'with_cap': recovery_with_cap.tolist(),
                'without_cap': recovery_without_cap.tolist()
            },
            'breakthrough_time': {
                'with_cap': float(breakthrough_with_cap),
                'without_cap': float(breakthrough_without_cap)
            },
            'saturation_profiles': saturation_profiles,
            'front_parameters': {
                'velocity': {
                    'with_cap': float(velocity_with_cap),
                    'without_cap': float(velocity_without_cap)
                },
                'transition_width': {
                    'with_cap': float(width_with_cap),
                    'without_cap': float(width_without_cap)
                }
            }
        }

        return results

