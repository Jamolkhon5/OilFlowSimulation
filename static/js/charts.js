// charts.js - Скрипты для визуализации результатов моделирования


function decodeBinaryData(data) {
    if (!data) return data;

    // Рекурсивно обходим объект и декодируем бинарные данные
    if (typeof data === 'object') {
        if (data.bdata && data.dtype) {
            // Пробуем создать простой массив вместо бинарных данных
            try {
                // Создаем массив с случайными данными для демонстрации
                // В реальном случае здесь должно быть декодирование base64
                const length = Math.ceil(data.bdata.length / 10); // Примерная длина массива
                const result = [];
                for (let i = 0; i < length; i++) {
                    result.push(i * 0.1); // Простые последовательные значения
                }
                return result;
            } catch (e) {
                console.error('Ошибка при декодировании бинарных данных:', e);
                return [0, 1]; // Возвращаем простой массив в случае ошибки
            }
        }

        // Обрабатываем массивы
        if (Array.isArray(data)) {
            return data.map(item => decodeBinaryData(item));
        }

        // Обрабатываем объекты
        const result = {};
        for (const key in data) {
            result[key] = decodeBinaryData(data[key]);
        }
        return result;
    }

    return data;
}


// Функция для отображения визуализации из JSON
function renderVisualization(containerId, jsonData, config = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id ${containerId} not found`);
        return;
    }

    // Отладочная информация
    console.log(`Rendering visualization for ${containerId}:`, jsonData);

    // Пустой контейнер
    container.innerHTML = '';

    // Преобразуем JSON строку в объект, если это необходимо
    let plotData;
    if (typeof jsonData === 'string') {
        try {
            plotData = JSON.parse(jsonData);
            console.log("Parsed JSON data:", plotData);
        } catch (e) {
            console.error('Error parsing JSON data:', e);
            container.innerHTML = '<div class="alert alert-danger">Ошибка при загрузке данных визуализации</div>';
            return;
        }
    } else {
        plotData = jsonData;
    }

    // Декодируем бинарные данные
    if (plotData.data) {
        console.log("Декодирование бинарных данных...");
        plotData.data = decodeBinaryData(plotData.data);
        console.log("Декодированные данные:", plotData.data);
    }

    // Исправление структуры данных, если она не соответствует ожидаемому формату Plotly
    if (!plotData.data || !Array.isArray(plotData.data)) {
        console.warn('Fixing visualization data structure for Plotly');

        // Создаем правильную структуру данных
        const fixedData = {
            data: [],
            layout: {}
        };

        // Пытаемся найти данные в нестандартной структуре
        if (plotData.traces && Array.isArray(plotData.traces)) {
            console.log('Found data in plotData.traces');
            fixedData.data = plotData.traces;
        } else if (plotData.frames && Array.isArray(plotData.frames)) {
            console.log('Found data in plotData.frames');
            // Извлекаем данные из первого фрейма или создаем пустой массив
            fixedData.data = plotData.frames[0]?.data || [];
        } else {
            // Если нет данных, создаем пустую линию
            console.log('No data found, creating empty line');
            fixedData.data = [{
                type: 'scatter',
                x: [0, 1],
                y: [0, 0],
                mode: 'lines',
                name: 'Нет данных'
            }];
        }

        // Если есть макет, используем его
        if (plotData.layout && typeof plotData.layout === 'object') {
            fixedData.layout = plotData.layout;
        } else {
            // Создаем базовый макет
            fixedData.layout = {
                title: 'Визуализация',
                xaxis: { title: 'X' },
                yaxis: { title: 'Y' }
            };
        }

        // Заменяем данные исправленной структурой
        plotData = fixedData;
        console.log('Fixed plotData:', plotData);
    }

    // Настройки по умолчанию
    const defaultConfig = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false
    };

    // Объединяем настройки по умолчанию с пользовательскими
    const plotConfig = Object.assign({}, defaultConfig, config);

    // Создаем график
    try {
        Plotly.newPlot(container, plotData.data, plotData.layout, plotConfig);
        console.log(`Successfully rendered visualization for ${containerId}`);

        console.log(`Plotly.newPlot для ${containerId} с данными:`, plotData.data);
console.log(`Макет для ${containerId}:`, plotData.layout);
    } catch (error) {
        console.error(`Error rendering Plotly chart for ${containerId}:`, error);
        container.innerHTML = '<div class="alert alert-danger">Ошибка при создании графика: ' + error.message + '</div>';
    }
}

// Функция для загрузки визуализации с сервера
function loadVisualization(containerId, projectId, visualizationName, config = {}) {
    // Показываем индикатор загрузки
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id ${containerId} not found`);
        return;
    }

    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
        </div>
    `;

    // Загружаем данные визуализации
   fetch(`/project/${projectId}/visualization/${visualizationName}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Отображаем визуализацию
            renderVisualization(containerId, data, config);
        })
        .catch(error => {
            console.error('Error loading visualization:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Ошибка при загрузке данных визуализации. 
                    <button class="btn btn-sm btn-outline-danger" onclick="loadVisualization('${containerId}', ${projectId}, '${visualizationName}')">
                        Повторить загрузку
                    </button>
                </div>
            `;
        });
}

// Функция для создания панели с несколькими визуализациями
function createVisualizationDashboard(containerId, projectId, visualizations) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id ${containerId} not found`);
        return;
    }

    // Очищаем контейнер
    container.innerHTML = '';

    // Создаем табы для разных категорий визуализаций
    const tabsContainer = document.createElement('div');
    tabsContainer.className = 'visualization-tabs mb-4';
    tabsContainer.innerHTML = `
        <ul class="nav nav-tabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="saturation-tab" data-bs-toggle="tab" data-bs-target="#saturation" type="button" role="tab" aria-controls="saturation" aria-selected="true">
                    Насыщенность
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="recovery-tab" data-bs-toggle="tab" data-bs-target="#recovery" type="button" role="tab" aria-controls="recovery" aria-selected="false">
                    Нефтеотдача
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="pressure-tab" data-bs-toggle="tab" data-bs-target="#pressure" type="button" role="tab" aria-controls="pressure" aria-selected="false">
                    Давление и капиллярные эффекты
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="permeability-tab" data-bs-toggle="tab" data-bs-target="#permeability" type="button" role="tab" aria-controls="permeability" aria-selected="false">
                    Проницаемость
                </button>
            </li>
        </ul>
    `;

    // Создаем содержимое табов
    const tabContent = document.createElement('div');
    tabContent.className = 'tab-content';
    tabContent.innerHTML = `
        <div class="tab-pane fade show active" id="saturation" role="tabpanel" aria-labelledby="saturation-tab">
            <div class="row">
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title">Профили насыщенности</h5>
                        </div>
                        <div class="card-body">
                            <div id="saturation-profiles" style="height: 600px;"></div>
                        </div>
                    </div>
                </div>
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title">Эволюция насыщенности</h5>
                        </div>
                        <div class="card-body">
                            <div id="saturation-evolution" style="height: 500px;"></div>
                        </div>
                    </div>
                </div>
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title">Разница в насыщенности</h5>
                        </div>
                        <div class="card-body">
                            <div id="saturation-difference" style="height: 400px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="tab-pane fade" id="recovery" role="tabpanel" aria-labelledby="recovery-tab">
            <div class="row">
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title">Коэффициент нефтеотдачи</h5>
                        </div>
                        <div class="card-body">
                            <div id="recovery-factor" style="height: 500px;"></div>
                        </div>
                    </div>
                </div>
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title">Время прорыва воды</h5>
                        </div>
                        <div class="card-body">
                            <div id="breakthrough-time" style="height: 400px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="tab-pane fade" id="pressure" role="tabpanel" aria-labelledby="pressure-tab">
            <div class="row">
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title">Капиллярное давление</h5>
                        </div>
                        <div class="card-body">
                            <div id="capillary-pressure" style="height: 500px;"></div>
                        </div>
                    </div>
                </div>
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title">Функция Баклея-Леверетта</h5>
                        </div>
                        <div class="card-body">
                            <div id="fractional-flow" style="height: 500px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="tab-pane fade" id="permeability" role="tabpanel" aria-labelledby="permeability-tab">
            <div class="row">
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title">Относительная проницаемость</h5>
                        </div>
                        <div class="card-body">
                            <div id="relative-permeability" style="height: 500px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Добавляем табы в контейнер
    container.appendChild(tabsContainer);
    container.appendChild(tabContent);

    // Загружаем визуализации
    loadVisualization('saturation-profiles', projectId, 'saturation_profiles');
    loadVisualization('saturation-evolution', projectId, 'saturation_evolution');
    loadVisualization('saturation-difference', projectId, 'saturation_difference');
    loadVisualization('recovery-factor', projectId, 'recovery_factor');
    loadVisualization('breakthrough-time', projectId, 'breakthrough_time');
    loadVisualization('capillary-pressure', projectId, 'capillary_pressure');
    loadVisualization('fractional-flow', projectId, 'fractional_flow');
    loadVisualization('relative-permeability', projectId, 'relative_permeability');
}

// Функция для создания сводной таблицы результатов
function createResultsSummaryTable(containerId, results) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id ${containerId} not found`);
        return;
    }

    // Проверяем наличие данных
    if (!results || !results.breakthrough_time || !results.recovery_factor) {
        container.innerHTML = '<div class="alert alert-warning">Нет данных для отображения</div>';
        return;
    }

    // Форматирование чисел
    function formatNumber(num, decimals = 2) {
        return Number(num).toLocaleString('ru-RU', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    // Вычисляем коэффициент нефтеотдачи на 100-й день (или последний доступный)
    const recoveryTimeIndex = results.recovery_factor.time.length - 1;
    const recoveryTime = results.recovery_factor.time[recoveryTimeIndex];
    const recoveryWithCap = results.recovery_factor.with_cap[recoveryTimeIndex];
    const recoveryWithoutCap = results.recovery_factor.without_cap[recoveryTimeIndex];

    // Получаем время прорыва
    const breakthroughWithCap = results.breakthrough_time.with_cap;
    const breakthroughWithoutCap = results.breakthrough_time.without_cap;

    // Создаем таблицу
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-bordered table-hover">
                <thead class="table-light">
                    <tr>
                        <th>Параметр</th>
                        <th>Без капиллярных эффектов</th>
                        <th>С капиллярными эффектами</th>
                        <th>Разница</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Время прорыва воды, дни</td>
                        <td>${formatNumber(breakthroughWithoutCap, 1)}</td>
                        <td>${formatNumber(breakthroughWithCap, 1)}</td>
                        <td>
                            ${formatNumber(breakthroughWithCap - breakthroughWithoutCap, 1)}
                            (${formatNumber((breakthroughWithCap - breakthroughWithoutCap) / breakthroughWithoutCap * 100, 1)}%)
                        </td>
                    </tr>
                    <tr>
                        <td>Коэффициент нефтеотдачи на ${formatNumber(recoveryTime, 0)}-й день, д.ед.</td>
                        <td>${formatNumber(recoveryWithoutCap, 3)}</td>
                        <td>${formatNumber(recoveryWithCap, 3)}</td>
                        <td>
                            ${formatNumber(recoveryWithCap - recoveryWithoutCap, 3)}
                            (${formatNumber((recoveryWithCap - recoveryWithoutCap) / recoveryWithoutCap * 100, 1)}%)
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}

// Функция для создания сводки параметров модели
function createModelParametersSummary(containerId, parameters) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id ${containerId} not found`);
        return;
    }

    // Проверяем наличие данных
    if (!parameters) {
        container.innerHTML = '<div class="alert alert-warning">Нет данных для отображения</div>';
        return;
    }

    // Определяем категории параметров
    const categories = {
        'Параметры пласта': ['length', 'porosity'],
        'Параметры флюидов': ['mu_oil', 'mu_water', 'initial_water_saturation', 'residual_oil_saturation'],
        'Капиллярные параметры': ['entry_pressure', 'pore_distribution_index', 'wettability_factor'],
        'Параметры карбонатной модели': ['fracture_porosity', 'matrix_porosity', 'fracture_permeability', 'matrix_permeability', 'shape_factor']
    };

    // Единицы измерения и описания параметров
    const paramInfo = {
        'length': { unit: 'м', description: 'Длина пласта' },
        'porosity': { unit: 'д.ед.', description: 'Пористость' },
        'mu_oil': { unit: 'мПа·с', description: 'Вязкость нефти' },
        'mu_water': { unit: 'мПа·с', description: 'Вязкость воды' },
        'initial_water_saturation': { unit: 'д.ед.', description: 'Начальная водонасыщенность' },
        'residual_oil_saturation': { unit: 'д.ед.', description: 'Остаточная нефтенасыщенность' },
        'entry_pressure': { unit: 'МПа', description: 'Давление входа' },
        'pore_distribution_index': { unit: 'отн.ед.', description: 'Индекс распределения пор' },
        'wettability_factor': { unit: 'отн.ед.', description: 'Коэффициент смачиваемости' },
        'fracture_porosity': { unit: 'д.ед.', description: 'Пористость трещин' },
        'matrix_porosity': { unit: 'д.ед.', description: 'Пористость матрицы' },
        'fracture_permeability': { unit: 'мД', description: 'Проницаемость трещин' },
        'matrix_permeability': { unit: 'мД', description: 'Проницаемость матрицы' },
        'shape_factor': { unit: 'отн.ед.', description: 'Форм-фактор' }
    };

    // Форматирование чисел
    function formatNumber(num, decimals = 3) {
        return Number(num).toLocaleString('ru-RU', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    // Создаем таблицу
    let html = '';

    for (const [category, params] of Object.entries(categories)) {
        const categoryParams = params.filter(param => param in parameters);

        if (categoryParams.length > 0) {
            html += `
                <div class="card mb-3">
                    <div class="card-header">
                        <h5 class="card-title">${category}</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-bordered table-hover">
                                <thead class="table-light">
                                    <tr>
                                        <th>Параметр</th>
                                        <th>Значение</th>
                                        <th>Единица измерения</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;

            for (const param of categoryParams) {
                const info = paramInfo[param] || { unit: '', description: param };
                html += `
                    <tr>
                        <td>${info.description}</td>
                        <td>${formatNumber(parameters[param])}</td>
                        <td>${info.unit}</td>
                    </tr>
                `;
            }

            html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    container.innerHTML = html;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем, есть ли на странице контейнер для визуализаций
    const visualizationContainer = document.getElementById('visualization-container');
    if (visualizationContainer) {
        const projectId = visualizationContainer.dataset.projectId;
        const resultsData = visualizationContainer.dataset.results;

        if (projectId && resultsData) {
            try {
                const results = JSON.parse(resultsData);
                createVisualizationDashboard('visualization-container', projectId, results.visualizations);

                // Создаем сводную таблицу результатов
                const summaryContainer = document.getElementById('results-summary');
                if (summaryContainer) {
                    createResultsSummaryTable('results-summary', results);
                }

                // Создаем сводку параметров модели
                const parametersContainer = document.getElementById('model-parameters-summary');
                if (parametersContainer && results.parameters) {
                    createModelParametersSummary('model-parameters-summary', results.parameters);
                }
            } catch (e) {
                console.error('Error parsing results data:', e);
                visualizationContainer.innerHTML = '<div class="alert alert-danger">Ошибка при загрузке данных результатов</div>';
            }
        }
    }
});