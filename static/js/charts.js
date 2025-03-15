// charts.js - Скрипты для визуализации результатов моделирования

// Функция для отображения визуализации из JSON
function renderVisualization(containerId, jsonData, config = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Контейнер с id ${containerId} не найден`);
        return;
    }

    // Получаем высоту из data-атрибута или устанавливаем стандартную
    const containerHeight = container.dataset.height || '500px';
    container.style.height = containerHeight;

    // Очищаем контейнер
    container.innerHTML = '';

    // Преобразуем JSON строку в объект, если это необходимо
    let plotData;
    if (typeof jsonData === 'string') {
        try {
            plotData = JSON.parse(jsonData);
        } catch (e) {
            console.error('Ошибка разбора JSON данных:', e);
            container.innerHTML = '<div class="alert alert-danger">Ошибка при загрузке данных визуализации</div>';
            return;
        }
    } else {
        plotData = jsonData;
    }

    // Проверяем структуру данных и восстанавливаем ее при необходимости
    if (!plotData.data || !Array.isArray(plotData.data)) {
        console.warn(`Неверная структура данных для ${containerId}, пытаемся восстановить:`, plotData);
        let correctedData = { data: [], layout: {} };

        // Проверяем различные возможные структуры данных
        if (plotData.traces && Array.isArray(plotData.traces)) {
            correctedData.data = plotData.traces;
        } else if (plotData.frames && Array.isArray(plotData.frames) && plotData.frames.length > 0) {
            if (plotData.frames[0].data && Array.isArray(plotData.frames[0].data)) {
                correctedData.data = plotData.frames[0].data;
            }
        } else if (typeof plotData === 'object') {
            // Создаем базовый график, если не удалось восстановить структуру
            correctedData.data = [
                {
                    type: 'scatter',
                    mode: 'lines',
                    x: [0, 1, 2, 3, 4, 5],
                    y: [0, 1, 0, 1, 0, 1],
                    name: 'Данные не доступны'
                }
            ];

            correctedData.layout = {
                title: 'Не удалось загрузить данные визуализации',
                annotations: [{
                    text: 'Ошибка данных. Пожалуйста, запустите моделирование заново.',
                    showarrow: false,
                    x: 0.5,
                    y: 0.5,
                    xref: 'paper',
                    yref: 'paper'
                }]
            };
        }

        // Используем layout из исходных данных, если он есть
        if (plotData.layout && typeof plotData.layout === 'object') {
            correctedData.layout = plotData.layout;
        }

        plotData = correctedData;
    }

    // Проверяем наличие layout
    if (!plotData.layout || typeof plotData.layout !== 'object') {
        plotData.layout = {};
    }

    // Обработка данных в трассах (traces)
    plotData.data.forEach(trace => {
        // Обработка x, y, z координат
        ['x', 'y', 'z'].forEach(key => {
            if (trace[key] && typeof trace[key] === 'object' && !Array.isArray(trace[key])) {
                // Извлекаем данные из бинарных объектов
                if (trace[key].bdata || trace[key].data || trace[key].original) {
                    if (Array.isArray(trace[key].data)) {
                        trace[key] = trace[key].data;
                    } else if (Array.isArray(trace[key].original)) {
                        trace[key] = trace[key].original;
                    } else if (trace[key].bdata) {
                        // Если у нас только бинарные данные, попробуем восстановить массив
                        try {
                            const decodedData = atob(trace[key].bdata);
                            const values = [];
                            for (let i = 0; i < decodedData.length; i += 8) {
                                const value = new DataView(new ArrayBuffer(8));
                                for (let j = 0; j < 8; j++) {
                                    value.setUint8(j, decodedData.charCodeAt(i + j));
                                }
                                values.push(value.getFloat64(0, true));
                            }
                            trace[key] = values;
                        } catch (e) {
                            console.error(`Ошибка декодирования бинарных данных для ${key}:`, e);
                            trace[key] = [0, 1, 2, 3, 4]; // Заполняем фиктивными данными
                        }
                    }
                }
            }
        });

        // Проверяем тип трассы
        if (!trace.type) {
            if (trace.mode && trace.mode.includes('markers')) {
                trace.type = 'scatter';
            } else if (trace.z && Array.isArray(trace.z)) {
                trace.type = 'contour';
            } else {
                trace.type = 'scatter';
            }
        }

        // Улучшение внешнего вида
        if (!trace.line && (trace.type === 'scatter' && (!trace.mode || trace.mode.includes('lines')))) {
            trace.line = { width: 2 };
        }

        // Добавляем маркеры для лучшей видимости на некоторых точках
        if (trace.type === 'scatter' && (!trace.mode || trace.mode === 'lines') && Array.isArray(trace.x) && trace.x.length < 20) {
            trace.mode = 'lines+markers';
            trace.marker = trace.marker || { size: 6 };
        }
    });

    // Настройки по умолчанию для всех графиков
    const defaultConfig = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false,
        toImageButtonOptions: {
            format: 'png',
            filename: containerId,
            height: 800,
            width: 1200,
            scale: 2
        }
    };

    // Объединяем настройки по умолчанию с пользовательскими
    const plotConfig = Object.assign({}, defaultConfig, config);

    // Улучшаем оформление графика
    const defaultLayout = {
        font: { family: 'Roboto, Arial, sans-serif', size: 14 },
        margin: { l: 60, r: 40, t: 50, b: 60 },
        plot_bgcolor: '#f8f9fa',
        paper_bgcolor: '#ffffff',
        hovermode: 'closest',
        autosize: true,
        showlegend: true,
        legend: { x: 0.02, y: 0.98, bgcolor: 'rgba(255, 255, 255, 0.7)' }
    };

    // Объединяем настройки оформления с существующими в данных
    plotData.layout = Object.assign({}, defaultLayout, plotData.layout);

    // Добавляем сетку к графику, если её нет
    if (!plotData.layout.xaxis) plotData.layout.xaxis = {};
    if (!plotData.layout.yaxis) plotData.layout.yaxis = {};

    // Добавляем сетку
    plotData.layout.xaxis.showgrid = plotData.layout.xaxis.showgrid !== false;
    plotData.layout.yaxis.showgrid = plotData.layout.yaxis.showgrid !== false;
    plotData.layout.xaxis.gridcolor = plotData.layout.xaxis.gridcolor || 'rgba(0,0,0,0.1)';
    plotData.layout.yaxis.gridcolor = plotData.layout.yaxis.gridcolor || 'rgba(0,0,0,0.1)';

    // Особая обработка для графика эволюции насыщенности
    // Специальная обработка для графика эволюции насыщенности
if (containerId === 'saturation-evolution') {
    // Базовые настройки
    container.style.height = '700px';
    plotData.layout.title = '';
    plotData.layout.margin = { l: 100, r: 120, t: 60, b: 80 };

    // Настройки осей как в Python
    plotData.layout.xaxis = {
        title: {
            text: 'Расстояние, м',
            font: { size: 14 },
            standoff: 20
        },
        showgrid: true
    };

    plotData.layout.yaxis = {
        title: {
            text: 'Время, дни',
            font: { size: 14 },
            standoff: 20
        },
        showgrid: true
    };

    // Критическое исправление: настройка отображения данных
    if (plotData.data.length > 0) {
        plotData.data.forEach(trace => {
            if (trace.type === 'contour' || trace.type === 'heatmap') {
                // Заставляем график отображать диапазон, как в Python
                trace.zauto = false;
                trace.zmin = 0.2;    // начальная водонасыщенность
                trace.zmax = 0.8;    // максимальная насыщенность

                // 20 уровней, как в Python
                trace.ncontours = 20;
                trace.autocontour = false;

                // Используем viridis, как в Python
                trace.colorscale = 'Viridis';

                // Настраиваем контурные линии
                trace.contours = {
                    start: 0.2,
                    end: 0.8,
                    size: 0.03,  // шаг между уровнями
                    showlabels: true
                };

                // Настраиваем colorbar, как в Python
                trace.colorbar = {
                    title: {
                        text: 'Водонасыщенность, д.ед.',
                        side: 'right'
                    },
                    thickness: 20,
                    y: 0.5
                };
            }
        });
    }

    // Настройка разделения графиков
    if (plotData.data.length >= 2) {
        plotData.layout.grid = {
            rows: 1,
            columns: 2,
            pattern: 'independent'
        };

        plotData.layout.annotations = [
            {
                text: 'Без учета капиллярных эффектов',
                showarrow: false,
                x: 0.25,
                y: 1.05,
                xref: 'paper',
                yref: 'paper'
            },
            {
                text: 'С учетом капиллярных эффектов',
                showarrow: false,
                x: 0.75,
                y: 1.05,
                xref: 'paper',
                yref: 'paper'
            }
        ];
    }
}


// Специальная обработка для графика относительной проницаемости
if (containerId === 'relative-permeability') {
    // Увеличиваем высоту контейнера
    container.style.height = '650px';

    // Убираем дублирующийся заголовок
    plotData.layout.title = '';

    // Увеличиваем отступы для всех сторон, особенно снизу
    plotData.layout.margin = {
        l: 80,  // левый отступ
        r: 40,  // правый отступ
        t: 40,  // верхний отступ
        b: 120  // увеличенный нижний отступ для оси X
    };

    // Настраиваем оси
    plotData.layout.xaxis = {
        title: {
            text: 'Водонасыщенность Sw, д.ед.',
            font: { size: 14, color: '#333' },
            standoff: 30  // отступ названия от оси
        },
        showgrid: true,
        range: [0, 1],    // фиксируем диапазон от 0 до 1
        automargin: true  // автоматический отступ для меток
    };

    plotData.layout.yaxis = {
        title: {
            text: 'Относительная проницаемость Kr, д.ед.',
            font: { size: 14, color: '#333' },
            standoff: 20
        },
        showgrid: true,
        range: [0, 1],    // фиксируем диапазон от 0 до 1
        automargin: true
    };

    // Улучшаем отображение линий и легенду
    if (plotData.data.length > 0) {
        // Задаем четкие цвета и толщину линий
        const colors = ['blue', 'green'];

        plotData.data.forEach((trace, index) => {
            if (!trace.line) trace.line = {};
            trace.line.width = 3;
            trace.line.color = colors[index % colors.length];

            // Улучшаем внешний вид
            if (trace.type === 'scatter') {
                // Добавляем маркеры для лучшей визуализации
                trace.mode = 'lines+markers';
                trace.marker = {
                    size: 6,
                    color: colors[index % colors.length],
                    symbol: 'circle'
                };
            }
        });

        // Перемещаем легенду в удобное место
        plotData.layout.legend = {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255, 255, 255, 0.8)',
            bordercolor: 'rgba(0, 0, 0, 0.1)',
            borderwidth: 1
        };
    }

    // Добавляем аннотацию для точки пересечения
    if (plotData.data.length >= 2) {
        plotData.layout.annotations = [
            {
                text: 'Точка пересечения',
                showarrow: true,
                arrowhead: 2,
                ax: -40,
                ay: -40,
                x: 0.5,  // примерное значение, может потребоваться корректировка
                y: 0.3,  // примерное значение, может потребоваться корректировка
                font: {
                    size: 12,
                    color: '#333'
                }
            }
        ];
    }
}

   // Для профилей насыщенности делаем специальные улучшения
if (containerId === 'saturation-profiles') {
    // Увеличиваем высоту для полного отображения
    container.style.height = '800px';

    // Увеличиваем отступы для подписей осей
    plotData.layout.margin = { l: 80, r: 150, t: 80, b: 80 };

    // Убираем заголовок с графика, так как он уже есть в карточке
    plotData.layout.title = '';

    // Улучшаем макет для подграфиков
    if (plotData.layout.grid) {
        plotData.layout.grid.rowgap = 0.25; // Увеличиваем промежуток между строками
    }

    // Перемещаем легенду вправо от графика
    plotData.layout.legend = {
        x: 1.05,
        y: 0.5,
        xanchor: 'left',
        yanchor: 'middle',
        orientation: 'vertical',
        bgcolor: 'rgba(255, 255, 255, 0.9)',
        bordercolor: 'rgba(0, 0, 0, 0.1)',
        borderwidth: 1,
        font: { size: 11 }
    };

    // Улучшаем оси для всех подграфиков
    for (let i = 1; i <= 2; i++) {
        const xaxisKey = i === 1 ? 'xaxis' : `xaxis${i}`;
        const yaxisKey = i === 1 ? 'yaxis' : `yaxis${i}`;

        if (!plotData.layout[xaxisKey]) plotData.layout[xaxisKey] = {};
        if (!plotData.layout[yaxisKey]) plotData.layout[yaxisKey] = {};

        plotData.layout[xaxisKey].title = {
            text: 'Расстояние, м',
            font: { size: 14, color: '#333' },
            standoff: 15
        };

        plotData.layout[yaxisKey].title = {
            text: 'Водонасыщенность, д.ед.',
            font: { size: 14, color: '#333' },
            standoff: 15
        };

        // Расширяем диапазон осей, чтобы избежать обрезания
        plotData.layout[xaxisKey].automargin = true;
        plotData.layout[yaxisKey].automargin = true;

        // Устанавливаем диапазоны для осей Y
        plotData.layout[yaxisKey].range = [0, 1.05]; // Увеличиваем верхнюю границу для легенды
    }

    // Улучшаем отображение данных
    plotData.data.forEach((trace, index) => {
        // Цвета для чёткого различия линий
        const colors = ['#1f77b4', '#2ca02c', '#d62728', '#9467bd', '#ff7f0e', '#17becf'];
        const lineStyles = ['solid', 'dash', 'dot', 'dashdot'];

        if (!trace.line) trace.line = {};
        trace.line.width = 2.5; // Толщина линии

        // Задаем цвета для разных дней
        if (trace.name && trace.name.includes('День')) {
            const colorIndex = index % colors.length;
            trace.line.color = colors[colorIndex];

            // Разные стили линий
            const styleIndex = Math.floor(index / colors.length) % lineStyles.length;
            if (styleIndex > 0) {
                trace.line.dash = lineStyles[styleIndex];
            }

            // Уменьшаем размер маркеров, чтобы они не были слишком большими
            if (trace.type === 'scatter') {
                trace.mode = 'lines+markers';
                trace.marker = {
                    size: 5,
                    color: colors[colorIndex]
                };
            }
        }
    });
}
// Специальная обработка для графика капиллярного давления
if (containerId === 'capillary-pressure') {
    // Увеличиваем высоту контейнера
    container.style.height = '650px';

    // Убираем дублирующийся заголовок
    plotData.layout.title = '';

    // Увеличиваем отступы, особенно снизу для оси X
    plotData.layout.margin = {
        l: 80,  // левый отступ
        r: 40,  // правый отступ
        t: 40,  // верхний отступ
        b: 120  // значительно увеличенный нижний отступ для оси X
    };

    // Улучшаем оформление осей
    plotData.layout.xaxis = {
        title: {
            text: 'Водонасыщенность Sw, д.ед.',
            font: { size: 14, color: '#333' },
            standoff: 30  // отступ названия от оси
        },
        showgrid: true,
        range: [0, 1],    // фиксируем диапазон
        automargin: true  // автоматический отступ для меток
    };

    plotData.layout.yaxis = {
        title: {
            text: 'Капиллярное давление, МПа',
            font: { size: 14, color: '#333' },
            standoff: 20
        },
        showgrid: true,
        automargin: true
    };

    // Улучшаем отображение линии
    if (plotData.data.length > 0) {
        plotData.data.forEach(trace => {
            if (!trace.line) trace.line = {};
            trace.line.width = 3;

            // Добавляем точки на линию для лучшей видимости
            if (trace.type === 'scatter') {
                trace.mode = 'lines+markers';
                trace.marker = {
                    size: 6,
                    symbol: 'circle'
                };
            }
        });
    }
}

    // Для разницы в насыщенности
    if (containerId === 'saturation-difference') {
        // Настраиваем цветовые схемы для этого графика
        plotData.data.forEach(trace => {
            if (trace.type === 'contour' || trace.type === 'heatmap') {
                trace.colorscale = 'RdBu';  // Красно-синяя шкала для разницы значений

                if (!trace.colorbar) {
                    trace.colorbar = {
                        title: {
                            text: 'Разница водонасыщенности, д.ед.',
                            side: 'right',
                            font: { size: 14, color: '#333' }
                        }
                    };
                }
            }
        });
    }

    // Создаем график
    try {
        console.log(`Рендеринг графика для ${containerId} с данными:`, plotData);
        Plotly.newPlot(container, plotData.data, plotData.layout, plotConfig);

        // Добавляем обработчик ошибок, чтобы избежать белого экрана
        container.on('plotly_error', function(err) {
            console.error(`Ошибка Plotly для ${containerId}:`, err);
            container.innerHTML = `<div class="alert alert-danger">
                Ошибка при создании графика: ${err.message || 'Неизвестная ошибка'}
                <button class="btn btn-sm btn-outline-danger mt-2" onclick="loadVisualization('${containerId}', ${container.dataset.projectId || 0}, '${container.dataset.vizName || ''}')">
                    Повторить загрузку
                </button>
            </div>`;
        });
    } catch (error) {
        console.error(`Ошибка при рендеринге графика для ${containerId}:`, error);
        container.innerHTML = `<div class="alert alert-danger">
            <p>Ошибка при создании графика: ${error.message}</p>
            <button class="btn btn-sm btn-outline-danger mt-2" onclick="loadVisualization('${containerId}', ${container.dataset.projectId || 0}, '${container.dataset.vizName || ''}')">
                Повторить загрузку
            </button>
        </div>`;
    }
}

// Функция для загрузки визуализации с сервера
function loadVisualization(containerId, projectId, visualizationName, config = {}) {
    // Показываем индикатор загрузки
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Контейнер с id ${containerId} не найден`);
        return;
    }

    // Сохраняем информацию о визуализации в атрибутах контейнера для повторной загрузки при ошибке
    container.dataset.projectId = projectId;
    container.dataset.vizName = visualizationName;

    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
        </div>
    `;

    // Добавляем временную метку для предотвращения кэширования
    const timestamp = new Date().getTime();

    // Загружаем данные визуализации
    fetch(`/project/${projectId}/visualization/${visualizationName}?t=${timestamp}`)
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error(`Визуализация "${visualizationName}" не найдена на сервере`);
                } else {
                    throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}`);
                }
            }
            return response.json().catch(e => {
                throw new Error(`Ошибка формата данных: ${e.message}`);
            });
        })
        .then(data => {
            console.log(`Данные визуализации ${visualizationName} получены:`, data);

            // Проверка на пустые данные
            if (!data || (data.data && data.data.length === 0)) {
                throw new Error('Получены пустые данные визуализации');
            }

            // Отображаем визуализацию
            renderVisualization(containerId, data, config);
        })
        .catch(error => {
            console.error(`Ошибка загрузки визуализации ${visualizationName}:`, error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <p><i class="fas fa-exclamation-triangle"></i> ${error.message || 'Ошибка при загрузке данных визуализации'}</p>
                    <button class="btn btn-sm btn-outline-danger mt-2" onclick="loadVisualization('${containerId}', ${projectId}, '${visualizationName}')">
                        <i class="fas fa-sync"></i> Повторить загрузку
                    </button>
                </div>
            `;
        });
}

// Полностью переработанная функция для создания панели с несколькими визуализациями
function createVisualizationDashboard(containerId, projectId, visualizations) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Контейнер с id ${containerId} не найден`);
        return;
    }

    // Очищаем контейнер
    container.innerHTML = '';

    // Создаем улучшенные табы для разных категорий визуализаций
    const tabsContainer = document.createElement('div');
    tabsContainer.className = 'visualization-tabs mb-4';
    tabsContainer.innerHTML = `
        <ul class="nav nav-tabs nav-fill border-bottom-0" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active rounded-top shadow-sm px-4 py-3" id="saturation-tab" data-bs-toggle="tab" data-bs-target="#saturation" type="button" role="tab" aria-controls="saturation" aria-selected="true">
                    <i class="fas fa-tint me-2"></i>Насыщенность
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link rounded-top shadow-sm px-4 py-3" id="recovery-tab" data-bs-toggle="tab" data-bs-target="#recovery" type="button" role="tab" aria-controls="recovery" aria-selected="false">
                    <i class="fas fa-chart-line me-2"></i>Нефтеотдача
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link rounded-top shadow-sm px-4 py-3" id="pressure-tab" data-bs-toggle="tab" data-bs-target="#pressure" type="button" role="tab" aria-controls="pressure" aria-selected="false">
                    <i class="fas fa-compress-alt me-2"></i>Давление
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link rounded-top shadow-sm px-4 py-3" id="permeability-tab" data-bs-toggle="tab" data-bs-target="#permeability" type="button" role="tab" aria-controls="permeability" aria-selected="false">
                    <i class="fas fa-filter me-2"></i>Проницаемость
                </button>
            </li>
        </ul>
    `;

    // Создаем улучшенное содержимое табов с исправленной структурой
    const tabContent = document.createElement('div');
    tabContent.className = 'tab-content border-top pt-4 bg-light rounded-bottom shadow-sm';
    tabContent.innerHTML = `
        <div class="tab-pane fade show active p-3" id="saturation" role="tabpanel" aria-labelledby="saturation-tab">
            <!-- Профили насыщенности -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white py-3">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-chart-area text-primary me-2"></i>Профили насыщенности
                    </h5>
                </div>
                <div class="card-body p-0">
                    <div id="saturation-profiles" class="visualization-container" data-height="600px"></div>
                </div>
            </div>

            <!-- Эволюция насыщенности -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white py-3">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-chart-line text-primary me-2"></i>Эволюция насыщенности
                    </h5>
                </div>
                <div class="card-body p-0">
                    <div id="saturation-evolution" class="visualization-container" data-height="500px"></div>
                </div>
            </div>

            <!-- Разница в насыщенности -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white py-3">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-chart-bar text-primary me-2"></i>Разница в насыщенности
                    </h5>
                </div>
                <div class="card-body p-0">
                    <div id="saturation-difference" class="visualization-container" data-height="400px"></div>
                </div>
            </div>
        </div>

        <div class="tab-pane fade p-3" id="recovery" role="tabpanel" aria-labelledby="recovery-tab">
            <!-- Коэффициент нефтеотдачи -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white py-3">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-percentage text-success me-2"></i>Коэффициент нефтеотдачи
                    </h5>
                </div>
                <div class="card-body p-0">
                    <div id="recovery-factor" class="visualization-container" data-height="500px"></div>
                </div>
            </div>
            
            <!-- Время прорыва воды -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white py-3">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-clock text-success me-2"></i>Время прорыва воды
                    </h5>
                </div>
                <div class="card-body p-0">
                    <div id="breakthrough-time" class="visualization-container" data-height="400px"></div>
                </div>
            </div>
        </div>

        <div class="tab-pane fade p-3" id="pressure" role="tabpanel" aria-labelledby="pressure-tab">
            <!-- Капиллярное давление -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white py-3">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-tachometer-alt text-danger me-2"></i>Капиллярное давление
                    </h5>
                </div>
                <div class="card-body p-0">
                    <div id="capillary-pressure" class="visualization-container" data-height="500px"></div>
                </div>
            </div>
            
            <!-- Функция Баклея-Леверетта -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white py-3">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-wave-square text-danger me-2"></i>Функция Баклея-Леверетта
                    </h5>
                </div>
                <div class="card-body p-0">
                    <div id="fractional-flow" class="visualization-container" data-height="500px"></div>
                </div>
            </div>
        </div>

        <div class="tab-pane fade p-3" id="permeability" role="tabpanel" aria-labelledby="permeability-tab">
            <!-- Относительная проницаемость -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-white py-3">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-random text-info me-2"></i>Относительная проницаемость
                    </h5>
                </div>
                <div class="card-body p-0">
                    <div id="relative-permeability" class="visualization-container" data-height="500px"></div>
                </div>
            </div>
        </div>
    `;

    // Добавляем стили для улучшения визуального представления
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .visualization-container {
            width: 100%;
            padding: 0;
            overflow: hidden;
            border-radius: 0 0 0.375rem 0.375rem;
        }
        
        .nav-tabs .nav-link {
            border: 1px solid #dee2e6;
            margin-right: 5px;
            transition: all 0.3s;
            font-weight: 500;
            color: #495057;
        }
        
        .nav-tabs .nav-link.active {
            background-color: #f8f9fa;
            border-bottom-color: #f8f9fa;
            color: #007bff;
        }
        
        .nav-tabs .nav-link:hover:not(.active) {
            background-color: #e9ecef;
            border-color: #dee2e6;
        }
        
        .tab-content {
            border: 1px solid #dee2e6;
            border-top: none;
        }
        
        .card {
            border: none;
            transition: all 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
        }
        
        .card-header {
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
        }
        
        .tab-pane {
            animation: fadeIn 0.3s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    `;

    // Добавляем CSS, табы и контент в контейнер
    container.appendChild(styleElement);
    container.appendChild(tabsContainer);
    container.appendChild(tabContent);

    // Расширяем функцию containsVisualization для более надежной проверки
    function enhancedContainsVisualization(visualizations, vizName) {
        if (!visualizations) return false;

        if (typeof visualizations === 'boolean') return visualizations;

        if (typeof visualizations === 'object') {
            return (
                visualizations[vizName] === true ||
                visualizations[vizName] === 1 ||
                visualizations[vizName] === "true" ||
                Object.keys(visualizations).includes(vizName)
            );
        }

        return false;
    }

    // Загружаем доступные визуализации
    console.log("Загрузка визуализаций для проекта:", projectId);
    console.log("Доступные визуализации:", visualizations);

    // Определяем список всех возможных визуализаций и их конфигураций
    const allVisualizations = [
        {
            id: 'saturation-profiles',
            name: 'saturation_profiles',
            config: { responsive: true }
        },
        {
            id: 'saturation-evolution',
            name: 'saturation_evolution',
            config: { responsive: true }
        },
        {
            id: 'saturation-difference',
            name: 'saturation_difference',
            config: { responsive: true }
        },
        {
            id: 'recovery-factor',
            name: 'recovery_factor',
            config: { responsive: true }
        },
        {
            id: 'breakthrough-time',
            name: 'breakthrough_time',
            config: { responsive: true }
        },
        {
            id: 'capillary-pressure',
            name: 'capillary_pressure',
            config: { responsive: true }
        },
        {
            id: 'fractional-flow',
            name: 'fractional_flow',
            config: { responsive: true }
        },
        {
            id: 'relative-permeability',
            name: 'relative_permeability',
            config: { responsive: true }
        }
    ];

    // Загружаем все доступные визуализации
    allVisualizations.forEach(viz => {
        if (enhancedContainsVisualization(visualizations, viz.name)) {
            loadVisualization(viz.id, projectId, viz.name, viz.config);
        } else {
            console.log(`Визуализация ${viz.name} недоступна или не найдена.`);
        }
    });

    // Добавляем обработчики событий для табов
    const tabs = container.querySelectorAll('.nav-link');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', event => {
            // Перерисовываем графики при переключении табов для корректного отображения
            const tabId = event.target.getAttribute('data-bs-target').substring(1);
            const tabPane = document.getElementById(tabId);
            if (tabPane) {
                const visualizationContainers = tabPane.querySelectorAll('.visualization-container');
                visualizationContainers.forEach(vizContainer => {
                    if (vizContainer.id) {
                        // Триггерим resize event для корректного обновления размеров Plotly графиков
                        window.dispatchEvent(new Event('resize'));
                    }
                });
            }
        });
    });
}

// Вспомогательная функция для проверки наличия визуализации
function containsVisualization(visualizations, vizName) {
    // Проверяем все возможные варианты наличия визуализации
    return (visualizations === true ||
            visualizations[vizName] === true ||
            visualizations[vizName] === 1 ||
            visualizations[vizName] === "true" ||
            (typeof visualizations === 'object' && Object.keys(visualizations).includes(vizName)));
}

// Функция для создания сводной таблицы результатов
function createResultsSummaryTable(containerId, results) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Контейнер с id ${containerId} не найден`);
        return;
    }

    // Проверяем наличие данных
    if (!results || !results.breakthrough_time || !results.recovery_factor) {
        container.innerHTML = '<div class="alert alert-warning">Нет данных для отображения</div>';
        return;
    }

    // Форматирование чисел
    function formatNumber(num, decimals = 2) {
        if (num === undefined || num === null || isNaN(num) || num === -1) {
            return "N/A";
        }
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

    // Получаем параметры фронта, если они есть
    let velocityWithCap = 0;
    let velocityWithoutCap = 0;
    let transitionWidthWithCap = 0;
    let transitionWidthWithoutCap = 0;

    if (results.front_parameters) {
        velocityWithCap = results.front_parameters.velocity.with_cap || 0;
        velocityWithoutCap = results.front_parameters.velocity.without_cap || 0;
        transitionWidthWithCap = results.front_parameters.transition_width.with_cap || 0;
        transitionWidthWithoutCap = results.front_parameters.transition_width.without_cap || 0;
    }

    // Получаем объемные метрики, если они есть
    let producedOilWithCap = 0;
    let producedOilWithoutCap = 0;
    let injectedWaterWithCap = 0;
    let injectedWaterWithoutCap = 0;
    let waterOilRatioWithCap = 0;
    let waterOilRatioWithoutCap = 0;

    if (results.volume_metrics && results.volume_metrics.produced_oil) {
        producedOilWithCap = results.volume_metrics.produced_oil.with_cap || 0;
        producedOilWithoutCap = results.volume_metrics.produced_oil.without_cap || 0;
        injectedWaterWithCap = results.volume_metrics.injected_water?.with_cap || 0;
        injectedWaterWithoutCap = results.volume_metrics.injected_water?.without_cap || 0;
        waterOilRatioWithCap = results.volume_metrics.water_oil_ratio?.with_cap || 0;
        waterOilRatioWithoutCap = results.volume_metrics.water_oil_ratio?.without_cap || 0;
    }

    // Получаем временные метрики, если они есть
    let timeTo50WithCap = -1;
    let timeTo50WithoutCap = -1;
    let timeToCompleteWithCap = -1;
    let timeToCompleteWithoutCap = -1;

    if (results.time_metrics) {
        if (results.time_metrics.time_to_50_percent) {
            timeTo50WithCap = results.time_metrics.time_to_50_percent.with_cap;
            timeTo50WithoutCap = results.time_metrics.time_to_50_percent.without_cap;
        }

        if (results.time_metrics.estimated_completion_time) {
            timeToCompleteWithCap = results.time_metrics.estimated_completion_time.with_cap;
            timeToCompleteWithoutCap = results.time_metrics.estimated_completion_time.without_cap;
        }
    }

    // Получаем физические параметры, если они есть
    let maxCapillaryPressureDiff = 0;
    let capillaryNumber = 0;
    let mobilityRatio = 0;

    if (results.physical_parameters) {
        maxCapillaryPressureDiff = results.physical_parameters.max_capillary_pressure_difference || 0;
        capillaryNumber = results.physical_parameters.capillary_number || 0;
        mobilityRatio = results.physical_parameters.mobility_ratio || 0;
    }

    // Получаем параметры для карбонатной модели, если они есть
    let matrixRecovery = -1;
    let fractureRecovery = -1;
    let exchangeIntensity = -1;

    if (results.carbonate_metrics) {
        matrixRecovery = results.carbonate_metrics.matrix_recovery || -1;
        fractureRecovery = results.carbonate_metrics.fracture_recovery || -1;
        exchangeIntensity = results.carbonate_metrics.matrix_fracture_exchange || -1;
    }

    // Создаем таблицу с улучшенным визуальным представлением
    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-bordered table-hover">
                <thead class="table-light">
                    <tr class="bg-primary text-white">
                        <th>Параметр</th>
                        <th>Без капиллярных эффектов</th>
                        <th>С капиллярными эффектами</th>
                        <th>Разница</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Блок 1: Основные параметры -->
                    <tr class="table-primary">
                        <td colspan="4" class="fw-bold">
                            <i class="fas fa-info-circle me-2"></i>Основные параметры
                        </td>
                    </tr>
                    <tr>
                        <td>Время прорыва воды, дни</td>
                        <td>${formatNumber(breakthroughWithoutCap, 1)}</td>
                        <td>${formatNumber(breakthroughWithCap, 1)}</td>
                        <td>
                            ${formatNumber(breakthroughWithCap - breakthroughWithoutCap, 1)}
                            <span class="badge ${(breakthroughWithCap - breakthroughWithoutCap) > 0 ? 'bg-success' : 'bg-danger'}">
                                ${formatNumber((breakthroughWithCap - breakthroughWithoutCap) / breakthroughWithoutCap * 100, 1)}%
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td>Коэффициент нефтеотдачи на ${formatNumber(recoveryTime, 0)}-й день, д.ед.</td>
                        <td>${formatNumber(recoveryWithoutCap, 3)}</td>
                        <td>${formatNumber(recoveryWithCap, 3)}</td>
                        <td>
                            ${formatNumber(recoveryWithCap - recoveryWithoutCap, 3)}
                            <span class="badge ${(recoveryWithCap - recoveryWithoutCap) > 0 ? 'bg-success' : 'bg-danger'}">
                                ${formatNumber((recoveryWithCap - recoveryWithoutCap) / recoveryWithoutCap * 100, 1)}%
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td>Скорость движения фронта, м/день</td>
                        <td>${formatNumber(velocityWithoutCap, 2)}</td>
                        <td>${formatNumber(velocityWithCap, 2)}</td>
                        <td>
                            ${formatNumber(velocityWithCap - velocityWithoutCap, 2)}
                            <span class="badge ${(velocityWithCap - velocityWithoutCap) > 0 ? 'bg-success' : 'bg-danger'}">
                                ${formatNumber((velocityWithCap - velocityWithoutCap) / velocityWithoutCap * 100, 1)}%
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td>Ширина переходной зоны, м</td>
                        <td>${formatNumber(transitionWidthWithoutCap, 1)}</td>
                        <td>${formatNumber(transitionWidthWithCap, 1)}</td>
                        <td>
                            ${formatNumber(transitionWidthWithCap - transitionWidthWithoutCap, 1)}
                            <span class="badge ${(transitionWidthWithCap - transitionWidthWithoutCap) > 0 ? 'bg-success' : 'bg-danger'}">
                                ${formatNumber((transitionWidthWithCap - transitionWidthWithoutCap) / transitionWidthWithoutCap * 100, 1)}%
                            </span>
                        </td>
                    </tr>`;

    // Добавляем объемные показатели, если они есть
    if (results.volume_metrics) {
        tableHTML += `
                    <!-- Блок 2: Объемные показатели -->
                    <tr class="table-success">
                        <td colspan="4" class="fw-bold">
                            <i class="fas fa-flask me-2"></i>Объемные показатели
                        </td>
                    </tr>
                    <tr>
                        <td>Объем добытой нефти, м³</td>
                        <td>${formatNumber(producedOilWithoutCap, 2)}</td>
                        <td>${formatNumber(producedOilWithCap, 2)}</td>
                        <td>
                            ${formatNumber(producedOilWithCap - producedOilWithoutCap, 2)}
                            <span class="badge ${(producedOilWithCap - producedOilWithoutCap) > 0 ? 'bg-success' : 'bg-danger'}">
                                ${formatNumber((producedOilWithCap - producedOilWithoutCap) / producedOilWithoutCap * 100, 1)}%
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td>Объем закачанной воды, м³</td>
                        <td>${formatNumber(injectedWaterWithoutCap, 2)}</td>
                        <td>${formatNumber(injectedWaterWithCap, 2)}</td>
                        <td>
                            ${formatNumber(injectedWaterWithCap - injectedWaterWithoutCap, 2)}
                            <span class="badge ${(injectedWaterWithCap - injectedWaterWithoutCap) > 0 ? 'bg-success' : 'bg-danger'}">
                                ${formatNumber((injectedWaterWithCap - injectedWaterWithoutCap) / injectedWaterWithoutCap * 100, 1)}%
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td>Водонефтяной фактор</td>
                        <td>${formatNumber(waterOilRatioWithoutCap, 2)}</td>
                        <td>${formatNumber(waterOilRatioWithCap, 2)}</td>
                        <td>
                            ${formatNumber(waterOilRatioWithCap - waterOilRatioWithoutCap, 2)}
                            <span class="badge ${(waterOilRatioWithCap - waterOilRatioWithoutCap) > 0 ? 'bg-danger' : 'bg-success'}">
                                ${formatNumber((waterOilRatioWithCap - waterOilRatioWithoutCap) / waterOilRatioWithoutCap * 100, 1)}%
                            </span>
                        </td>
                    </tr>`;
    }

    // Добавляем временные показатели, если они есть
    if (results.time_metrics) {
        tableHTML += `
                    <!-- Блок 3: Временные показатели -->
                    <tr class="table-info">
                        <td colspan="4" class="fw-bold">
                            <i class="fas fa-clock me-2"></i>Временные показатели
                        </td>
                    </tr>
                    <tr>
                        <td>Время достижения 50% нефтеотдачи, дни</td>
                        <td>${formatNumber(timeTo50WithoutCap, 1)}</td>
                        <td>${formatNumber(timeTo50WithCap, 1)}</td>
                        <td>
                            ${formatNumber(timeTo50WithCap - timeTo50WithoutCap, 1)}
                            <span class="badge ${(timeTo50WithCap - timeTo50WithoutCap) < 0 ? 'bg-success' : 'bg-danger'}">
                                ${formatNumber((timeTo50WithCap - timeTo50WithoutCap) / timeTo50WithoutCap * 100, 1)}%
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td>Прогнозируемое время полного истощения, дни</td>
                        <td>${formatNumber(timeToCompleteWithoutCap, 1)}</td>
                        <td>${formatNumber(timeToCompleteWithCap, 1)}</td>
                        <td>
                            ${timeToCompleteWithCap !== -1 && timeToCompleteWithoutCap !== -1 ? 
                              `${formatNumber(timeToCompleteWithCap - timeToCompleteWithoutCap, 1)}
                              <span class="badge ${(timeToCompleteWithCap - timeToCompleteWithoutCap) < 0 ? 'bg-success' : 'bg-danger'}">
                                  ${formatNumber((timeToCompleteWithCap - timeToCompleteWithoutCap) / timeToCompleteWithoutCap * 100, 1)}%
                              </span>` : 
                              "N/A"}
                        </td>
                    </tr>`;
    }

    // Добавляем физические показатели, если они есть
    if (results.physical_parameters) {
        tableHTML += `
                    <!-- Блок 4: Физические показатели -->
                    <tr class="table-warning">
                        <td colspan="4" class="fw-bold">
                            <i class="fas fa-atom me-2"></i>Физические показатели
                        </td>
                    </tr>
                    <tr>
                        <td>Максимальный перепад капиллярного давления, МПа</td>
                        <td colspan="2" class="text-center">${formatNumber(maxCapillaryPressureDiff, 3)}</td>
                        <td class="text-center">-</td>
                    </tr>
                    <tr>
                        <td>Число капиллярности (x10⁻⁷)</td>
                        <td colspan="2" class="text-center">${formatNumber(capillaryNumber * 10000000, 3)}</td>
                        <td class="text-center">-</td>
                    </tr>
                    <tr>
                        <td>Коэффициент подвижности флюидов</td>
                        <td colspan="2" class="text-center">${formatNumber(mobilityRatio, 2)}</td>
                        <td class="text-center">-</td>
                    </tr>`;
    }

    // Добавляем показатели для карбонатной модели, если они есть
    if (results.carbonate_metrics) {
        tableHTML += `
                    <!-- Блок 5: Карбонатные показатели -->
                    <tr class="table-secondary">
                        <td colspan="4" class="fw-bold">
                            <i class="fas fa-cubes me-2"></i>Показатели для карбонатной модели
                        </td>
                    </tr>
                    <tr>
                        <td>Эффективность вытеснения в матрице, д.ед.</td>
                        <td colspan="2" class="text-center">${formatNumber(matrixRecovery, 3)}</td>
                        <td class="text-center">-</td>
                    </tr>
                    <tr>
                        <td>Эффективность вытеснения в трещинах, д.ед.</td>
                        <td colspan="2" class="text-center">${formatNumber(fractureRecovery, 3)}</td>
                        <td class="text-center">-</td>
                    </tr>
                    <tr>
                        <td>Интенсивность обмена между матрицей и трещинами</td>
                        <td colspan="2" class="text-center">${formatNumber(exchangeIntensity, 3)}</td>
                        <td class="text-center">-</td>
                    </tr>`;
    }

    tableHTML += `
                </tbody>
            </table>
        </div>`;

    container.innerHTML = tableHTML;
}

// Функция для создания сводки параметров модели с улучшенным дизайном
function createModelParametersSummary(containerId, parameters) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Контейнер с id ${containerId} не найден`);
        return;
    }

    // Проверяем наличие данных
    if (!parameters) {
        container.innerHTML = '<div class="alert alert-warning">Нет данных для отображения</div>';
        return;
    }

    // Определяем категории параметров с иконками
    const categories = [
        {
            name: 'Параметры пласта',
            icon: 'fas fa-layer-group',
            color: 'primary',
            params: ['length', 'porosity']
        },
        {
            name: 'Параметры флюидов',
            icon: 'fas fa-tint',
            color: 'info',
            params: ['mu_oil', 'mu_water', 'initial_water_saturation', 'residual_oil_saturation']
        },
        {
            name: 'Капиллярные параметры',
            icon: 'fas fa-compress-arrows-alt',
            color: 'danger',
            params: ['entry_pressure', 'pore_distribution_index', 'wettability_factor']
        },
        {
            name: 'Параметры карбонатной модели',
            icon: 'fas fa-cubes',
            color: 'secondary',
            params: ['fracture_porosity', 'matrix_porosity', 'fracture_permeability', 'matrix_permeability', 'shape_factor']
        }
    ];

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

    // Создаем улучшенное представление параметров в карточках
    let html = `<div class="row g-4">`;

    for (const category of categories) {
        const categoryParams = category.params.filter(param => param in parameters);

        if (categoryParams.length > 0) {
            html += `
                <div class="col-md-6 col-lg-6">
                    <div class="card shadow-sm h-100">
                        <div class="card-header bg-${category.color} text-white py-3">
                            <h5 class="card-title mb-0"><i class="${category.icon} me-2"></i>${category.name}</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-bordered table-hover mb-0">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Параметр</th>
                                            <th>Значение</th>
                                            <th>Ед. изм.</th>
                                        </tr>
                                    </thead>
                                    <tbody>
            `;

            for (const param of categoryParams) {
                const info = paramInfo[param] || { unit: '', description: param };
                html += `
                    <tr>
                        <td><span class="fw-medium">${info.description}</span></td>
                        <td class="text-center">${formatNumber(parameters[param])}</td>
                        <td class="text-center">${info.unit}</td>
                    </tr>
                `;
            }

            html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            `;
        }
    }

    html += `</div>`;

    container.innerHTML = html;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Стили для плавных анимаций и красивых переходов
    const globalStyles = document.createElement('style');
    globalStyles.textContent = `
        /* Глобальные улучшения дизайна */
        .card {
            transition: all 0.3s ease;
            border: none;
            border-radius: 0.5rem;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        
        .card-header {
            border-top-left-radius: 0.5rem !important;
            border-top-right-radius: 0.5rem !important;
            border-bottom: none;
        }
        
        .table {
            border-collapse: separate;
            border-spacing: 0;
        }
        
        .table-bordered {
            border-radius: 0.5rem;
            overflow: hidden;
        }
        
        .nav-tabs .nav-link {
            border-top-left-radius: 0.5rem;
            border-top-right-radius: 0.5rem;
            font-weight: 500;
            padding: 0.75rem 1.25rem;
        }
        
        .badge {
            padding: 0.35em 0.65em;
            font-weight: 500;
        }
    `;
    document.head.appendChild(globalStyles);

    // Проверяем, есть ли на странице контейнер для визуализаций
    const visualizationContainer = document.getElementById('visualization-container');
    if (visualizationContainer) {
        const projectId = visualizationContainer.dataset.projectId;
        const resultsData = visualizationContainer.dataset.results;

        if (projectId && resultsData) {
            try {
                const results = JSON.parse(resultsData);
                console.log("Данные результатов:", results);

                // Создаем визуализации
                if (results.visualizations) {
                    createVisualizationDashboard('visualization-container', projectId, results.visualizations);
                } else {
                    console.error("Нет данных визуализаций в результатах");
                }

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
                console.error('Ошибка при разборе данных результатов:', e);
                visualizationContainer.innerHTML = '<div class="alert alert-danger">Ошибка при загрузке данных результатов</div>';
            }
        }
    }
});