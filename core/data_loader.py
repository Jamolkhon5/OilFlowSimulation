#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np


class DataLoader:
    """Класс для загрузки и обработки данных из CSV-файлов"""

    def __init__(self, data_dir='data/uploads'):
        self.data_dir = data_dir
        self.rock_data = None
        self.capillary_data = None
        self.perm_data = None
        self.pvt_data = None
        self.production_data = None
        self.encoding = 'utf-8'  # Кодировка по умолчанию

    def load_all_data(self, rock_file=None, cap_file=None, perm_file=None, pvt_file=None, prod_file=None):
        """Загрузка всех доступных данных из указанных файлов"""
        print("Загрузка данных...")
        self.load_rock_properties(rock_file)
        self.load_capillary_pressure(cap_file)
        self.load_relative_permeability(perm_file)
        self.load_pvt_data(pvt_file)
        self.load_production_data(prod_file)
        print("Данные успешно загружены.")

    def load_rock_properties(self, file_path=None):
        """Загрузка данных о свойствах породы"""
        if not file_path:
            file_path = os.path.join(self.data_dir, 'rock_properties.csv')

        if os.path.exists(file_path):
            try:
                # Пробуем разные кодировки, так как некоторые файлы могут быть в CP1252
                try:
                    self.rock_data = pd.read_csv(file_path, encoding=self.encoding)
                except UnicodeDecodeError:
                    self.rock_data = pd.read_csv(file_path, encoding='cp1252')

                print(f"Загружено {len(self.rock_data)} записей о свойствах породы.")

                # Проверяем наличие необходимых колонок
                required_columns = ['ID_Sample', 'Porosity_fr', 'Permeability_mD', 'Rock_Type']
                for col in required_columns:
                    if col not in self.rock_data.columns:
                        print(f"ПРЕДУПРЕЖДЕНИЕ: В файле свойств породы отсутствует колонка {col}")

                return True
            except Exception as e:
                print(f"Ошибка при загрузке файла свойств породы: {e}")
                return False
        else:
            print(f"Файл {file_path} не найден.")
            return False

    def load_capillary_pressure(self, file_path=None):
        """Загрузка данных о капиллярном давлении"""
        if not file_path:
            file_path = os.path.join(self.data_dir, 'capillary_pressure.csv')

        if os.path.exists(file_path):
            try:
                self.capillary_data = pd.read_csv(file_path, encoding=self.encoding)
                print(f"Загружено {len(self.capillary_data)} записей о капиллярном давлении.")

                # Проверяем наличие необходимых колонок
                required_columns = ['ID_Sample', 'Water_Saturation', 'Pc_Drainage_MPa']
                for col in required_columns:
                    if col not in self.capillary_data.columns:
                        print(f"ПРЕДУПРЕЖДЕНИЕ: В файле капиллярного давления отсутствует колонка {col}")

                return True
            except Exception as e:
                print(f"Ошибка при загрузке файла капиллярного давления: {e}")
                return False
        else:
            print(f"Файл {file_path} не найден.")
            return False

    def load_relative_permeability(self, file_path=None):
        """Загрузка данных об относительной проницаемости"""
        if not file_path:
            file_path = os.path.join(self.data_dir, 'relative_perm.csv')

        if os.path.exists(file_path):
            try:
                self.perm_data = pd.read_csv(file_path, encoding=self.encoding)
                print(f"Загружено {len(self.perm_data)} записей об относительной проницаемости.")

                # Проверяем наличие необходимых колонок
                required_columns = ['ID_Sample', 'Water_Saturation', 'Krw_Drainage', 'Kro_Drainage']
                for col in required_columns:
                    if col not in self.perm_data.columns:
                        print(f"ПРЕДУПРЕЖДЕНИЕ: В файле относительной проницаемости отсутствует колонка {col}")

                return True
            except Exception as e:
                print(f"Ошибка при загрузке файла относительной проницаемости: {e}")
                return False
        else:
            print(f"Файл {file_path} не найден.")
            return False

    def load_pvt_data(self, file_path=None):
        """Загрузка PVT-данных флюидов"""
        if not file_path:
            file_path = os.path.join(self.data_dir, 'pvt_data.csv')

        if os.path.exists(file_path):
            try:
                self.pvt_data = pd.read_csv(file_path, encoding=self.encoding)
                print(f"Загружено {len(self.pvt_data)} записей PVT-данных.")

                # Проверяем наличие необходимых колонок
                required_columns = ['Pressure_MPa', 'Oil_Viscosity_cP']
                for col in required_columns:
                    if col not in self.pvt_data.columns:
                        print(f"ПРЕДУПРЕЖДЕНИЕ: В файле PVT-данных отсутствует колонка {col}")

                return True
            except Exception as e:
                print(f"Ошибка при загрузке файла PVT-данных: {e}")
                return False
        else:
            print(f"Файл {file_path} не найден.")
            return False

    def load_production_data(self, file_path=None):
        """Загрузка данных о добыче"""
        if not file_path:
            file_path = os.path.join(self.data_dir, 'production_data.csv')

        if os.path.exists(file_path):
            try:
                self.production_data = pd.read_csv(file_path, encoding=self.encoding)
                print(f"Загружено {len(self.production_data)} записей о добыче.")

                # Проверяем наличие необходимых колонок
                required_columns = ['Date', 'Oil_Rate_m3_day', 'Water_Rate_m3_day']
                for col in required_columns:
                    if col not in self.production_data.columns:
                        print(f"ПРЕДУПРЕЖДЕНИЕ: В файле данных добычи отсутствует колонка {col}")

                return True
            except Exception as e:
                print(f"Ошибка при загрузке файла данных добычи: {e}")
                return False
        else:
            print(f"Файл {file_path} не найден.")
            return False

    def get_brooks_corey_params(self, rock_type=None):
        """
        Получение параметров модели Брукса-Кори для заданного типа породы

        Args:
            rock_type (str, optional): Тип породы. Defaults to None.

        Returns:
            dict: Словарь параметров Брукса-Кори для образцов указанного типа породы
        """
        if self.rock_data is None or self.capillary_data is None:
            print("Данные о породе или капиллярном давлении не загружены.")
            return {}

        # Фильтрация данных по типу породы, если указан
        if rock_type:
            samples = self.rock_data[self.rock_data['Rock_Type'] == rock_type]['ID_Sample'].tolist()
        else:
            samples = self.rock_data['ID_Sample'].tolist()

        # Получение уникальных образцов
        unique_samples = set(samples).intersection(set(self.capillary_data['ID_Sample'].unique()))

        # Расчет параметров для каждого образца
        results = {}
        for sample in unique_samples:
            try:
                sample_data = self.capillary_data[self.capillary_data['ID_Sample'] == sample]

                # Только для дренирования (Pc_Drainage_MPa)
                Sw = sample_data['Water_Saturation'].values
                Pc = sample_data['Pc_Drainage_MPa'].values

                # Фильтрация нулевых значений
                valid_idx = (Pc > 0) & (Sw > 0) & (Sw < 1)
                Sw = Sw[valid_idx]
                Pc = Pc[valid_idx]

                if len(Sw) < 3:
                    continue

                # Вычисление параметров Брукса-Кори
                # Нахождение параметров для Pc = Pe * (Sw_eff)^(-1/lambda)
                # Линеаризация: ln(Pc) = ln(Pe) - (1/lambda) * ln(Sw_eff)

                # Расчет эффективной насыщенности
                Swc = min(Sw)  # Начальная водонасыщенность
                Sw_eff = (Sw - Swc) / (1 - Swc)

                # Линеаризация
                log_Pc = np.log(Pc)
                log_Sw_eff = np.log(Sw_eff)

                # Линейная регрессия
                valid = ~np.isnan(log_Sw_eff) & ~np.isnan(log_Pc) & ~np.isinf(log_Sw_eff) & ~np.isinf(log_Pc)
                if sum(valid) < 3:
                    continue

                slope, intercept = np.polyfit(log_Sw_eff[valid], log_Pc[valid], 1)

                # Расчет параметров
                lambda_value = -1 / slope
                Pe = np.exp(intercept)

                # Добавление в результаты
                results[sample] = {
                    'entry_pressure': Pe,
                    'pore_distribution_index': lambda_value,
                    'initial_water_saturation': Swc
                }
            except Exception as e:
                print(f"Ошибка при обработке образца {sample}: {e}")

        return results

    def get_relative_permeability_data(self, sample_id):
        """
        Получение данных об относительной проницаемости для образца

        Args:
            sample_id (str): Идентификатор образца

        Returns:
            tuple: Кортеж массивов (Sw, Krw, Kro)
        """
        if self.perm_data is None:
            print("Данные об относительной проницаемости не загружены.")
            return None

        if sample_id not in self.perm_data['ID_Sample'].unique():
            print(f"Образец {sample_id} не найден в данных.")
            return None

        sample_data = self.perm_data[self.perm_data['ID_Sample'] == sample_id]

        # Выбираем только нужные столбцы и сортируем по насыщенности
        result = sample_data[['Water_Saturation', 'Krw_Drainage', 'Kro_Drainage']].copy()
        result.sort_values('Water_Saturation', inplace=True)

        # Преобразуем в numpy массивы для удобства
        Sw = result['Water_Saturation'].values
        Krw = result['Krw_Drainage'].values
        Kro = result['Kro_Drainage'].values

        return Sw, Krw, Kro

    def get_average_parameters(self, rock_type=None):
        """
        Получение усредненных параметров для заданного типа породы

        Args:
            rock_type (str, optional): Тип породы. Defaults to None.

        Returns:
            dict: Словарь усредненных параметров для указанного типа породы
        """
        if self.rock_data is None:
            print("Данные о породе не загружены.")
            return None

        # Фильтрация данных по типу породы, если указан
        if rock_type:
            data = self.rock_data[self.rock_data['Rock_Type'] == rock_type]
        else:
            data = self.rock_data

        if len(data) == 0:
            print(f"Нет данных для типа породы {rock_type}.")
            return None

        # Расчет средних значений
        avg_porosity = data['Porosity_fr'].mean()
        avg_permeability = data['Permeability_mD'].mean()

        # Проверка наличия колонки Wettability_Index
        if 'Wettability_Index' in data.columns:
            avg_wettability = data['Wettability_Index'].mean()
        else:
            avg_wettability = 0.5  # Значение по умолчанию

        return {
            'porosity': avg_porosity,
            'permeability': avg_permeability,
            'wettability_index': avg_wettability
        }

    def get_pvt_properties(self, pressure=None):
        """
        Получение PVT-свойств флюидов при заданном давлении

        Args:
            pressure (float, optional): Давление в МПа. Defaults to None.

        Returns:
            dict: Словарь PVT-свойств флюидов
        """
        if self.pvt_data is None:
            print("PVT-данные не загружены.")
            return None

        if pressure is None:
            # Возвращаем первую строку данных
            row = self.pvt_data.iloc[0]
        else:
            # Находим ближайшее давление
            idx = (self.pvt_data['Pressure_MPa'] - pressure).abs().idxmin()
            row = self.pvt_data.iloc[idx]

        # Формируем словарь свойств, проверяя наличие каждой колонки
        properties = {'pressure': row.get('Pressure_MPa', 0)}

        if 'Oil_Viscosity_cP' in row:
            properties['oil_viscosity'] = row['Oil_Viscosity_cP']
        else:
            properties['oil_viscosity'] = 5.0  # Значение по умолчанию

        properties['water_viscosity'] = 1.0  # Значение по умолчанию для воды

        if 'Oil_Density_kg_m3' in row:
            properties['oil_density'] = row['Oil_Density_kg_m3']

        if 'Gas_Density_kg_m3' in row:
            properties['gas_density'] = row['Gas_Density_kg_m3']

        return properties

    def extract_model_parameters(self, rock_type=None):
        """
        Извлечение параметров модели из загруженных данных

        Args:
            rock_type (str, optional): Тип породы. Defaults to None.

        Returns:
            dict: Словарь параметров для модели
        """
        params = {}

        # Получение усредненных параметров породы
        rock_params = self.get_average_parameters(rock_type)
        if rock_params:
            params['porosity'] = rock_params['porosity']
            params['wettability_factor'] = rock_params['wettability_index']

        # Получение параметров модели Брукса-Кори
        bc_params = self.get_brooks_corey_params(rock_type)
        if bc_params and len(bc_params) > 0:
            # Берем первый доступный образец
            sample_id = list(bc_params.keys())[0]
            params_bc = bc_params[sample_id]

            params['entry_pressure'] = params_bc['entry_pressure']
            params['pore_distribution_index'] = params_bc['pore_distribution_index']
            params['initial_water_saturation'] = params_bc['initial_water_saturation']

        # Получение PVT-свойств флюидов
        pvt_props = self.get_pvt_properties()
        if pvt_props:
            params['mu_oil'] = pvt_props['oil_viscosity']
            params['mu_water'] = pvt_props['water_viscosity']

        return params

    def validate_file_format(self, file_path, required_columns):
        """
        Проверка формата файла на соответствие требованиям

        Args:
            file_path (str): Путь к файлу
            required_columns (list): Список обязательных колонок

        Returns:
            tuple: (bool, str) - результат проверки и сообщение
        """
        try:
            print(f"Начинаем валидацию файла {file_path}")

            # Проверяем существование файла
            if not os.path.exists(file_path):
                return False, f"Файл не найден по пути {file_path}"

            # Попытка прочитать файл с разными кодировками и разделителями
            encodings = ['utf-8', 'cp1251', 'latin1', 'windows-1252']
            separators = [',', ';', '\t']

            df = None
            successful_encoding = None
            successful_separator = None

            # Читаем первые несколько строк для анализа
            with open(file_path, 'rb') as f:
                first_bytes = f.read(1024)

            # Выводим первые байты для диагностики
            print(f"Первые байты файла (hex): {first_bytes.hex()[:50]}...")

            # Пробуем разные комбинации кодировок и разделителей
            for encoding in encodings:
                for sep in separators:
                    try:
                        print(f"Пробуем прочитать с кодировкой {encoding} и разделителем '{sep}'")
                        df = pd.read_csv(file_path, encoding=encoding, sep=sep,
                                         quotechar='"', escapechar='\\', engine='python')

                        # Если успешно прочитали и получили более одной колонки
                        if df is not None and len(df.columns) > 1:
                            successful_encoding = encoding
                            successful_separator = sep
                            print(f"Успешно прочитан файл с кодировкой {encoding} и разделителем '{sep}'")
                            print(f"Колонки: {list(df.columns)}")

                            # Проверяем, есть ли одна колонка, которая содержит все данные (неправильный разделитель)
                            if len(df.columns) == 1 and df.iloc[0, 0] and isinstance(df.iloc[0, 0], str) and sep in \
                                    df.iloc[0, 0]:
                                print(f"Кажется, разделитель неправильный, продолжаем поиск")
                                continue

                            break
                    except Exception as e:
                        print(f"Ошибка при чтении с кодировкой {encoding} и разделителем '{sep}': {str(e)}")
                        continue

                if df is not None and len(df.columns) > 1:
                    break

            if df is None:
                return False, "Не удалось прочитать файл. Проверьте формат и кодировку файла."

            # Если список обязательных колонок пустой, просто проверяем, что файл читается
            if not required_columns:
                return True, f"Файл успешно загружен (кодировка: {successful_encoding}, разделитель: '{successful_separator}')"

            # Проверяем наличие всех необходимых колонок
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                # Проверяем, может колонки есть, но с другими названиями
                column_similarity = {}
                for req_col in missing_columns:
                    similar_columns = []
                    for col in df.columns:
                        # Используем расстояние Левенштейна для поиска похожих колонок
                        if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                            similar_columns.append(col)
                    if similar_columns:
                        column_similarity[req_col] = similar_columns

                suggestion_msg = ""
                if column_similarity:
                    suggestion_msg = "\nВозможно, вы имели в виду следующие колонки:\n"
                    for req_col, similar_cols in column_similarity.items():
                        suggestion_msg += f"- Для '{req_col}': {', '.join(similar_cols)}\n"

                available_cols = "\nДоступные колонки: " + ", ".join(df.columns)

                return False, f"В файле отсутствуют следующие обязательные колонки: {', '.join(missing_columns)}.{suggestion_msg}{available_cols}"

            return True, f"Файл соответствует требованиям (кодировка: {successful_encoding}, разделитель: '{successful_separator}')"

        except Exception as e:
            import traceback
            print(f"Ошибка при проверке файла: {str(e)}")
            traceback.print_exc()
            return False, f"Ошибка при проверке файла: {str(e)}"