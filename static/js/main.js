// main.js - Основные скрипты для приложения

// Функция для отображения/скрытия сообщений
function showMessage(message, type = 'info', duration = 5000) {
    const alertBox = document.createElement('div');
    alertBox.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertBox.style.top = '20px';
    alertBox.style.right = '20px';
    alertBox.style.zIndex = '9999';
    alertBox.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(alertBox);

    // Автоматически скрываем сообщение через указанное время
    setTimeout(() => {
        alertBox.classList.remove('show');
        setTimeout(() => {
            alertBox.remove();
        }, 300);
    }, duration);
}

// Функция для форматирования чисел
function formatNumber(num, decimals = 2) {
    return Number(num).toLocaleString('ru-RU', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Функция для форматирования дат
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Функция для проверки параметров модели
function validateModelParameters(parameters) {
    // Отправляем AJAX-запрос на сервер для проверки параметров
    return fetch('/api/parameters/check', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(parameters)
    })
    .then(response => response.json())
    .then(data => {
        // Отображаем ошибки и предупреждения, если они есть
        const errorFields = Object.keys(data.errors || {});
        const warningFields = Object.keys(data.warnings || {});

        // Сбрасываем классы и сообщения полей
        document.querySelectorAll('.model-param').forEach(field => {
            const inputName = field.querySelector('input').name;
            const feedbackElement = field.querySelector('.invalid-feedback');

            field.classList.remove('has-error', 'has-warning');
            if (feedbackElement) {
                feedbackElement.textContent = '';
            }
        });

        // Отмечаем поля с ошибками
        errorFields.forEach(fieldName => {
            const field = document.querySelector(`.model-param input[name="${fieldName}"]`).parentNode;
            field.classList.add('has-error');
            const feedbackElement = field.querySelector('.invalid-feedback');
            if (feedbackElement) {
                feedbackElement.textContent = data.errors[fieldName];
            }
        });

        // Отмечаем поля с предупреждениями
        warningFields.forEach(fieldName => {
            const field = document.querySelector(`.model-param input[name="${fieldName}"]`).parentNode;
            if (!field.classList.contains('has-error')) {
                field.classList.add('has-warning');
                const feedbackElement = field.querySelector('.invalid-feedback');
                if (feedbackElement) {
                    feedbackElement.textContent = data.warnings[fieldName];
                }
            }
        });

        return data.valid;
    })
    .catch(error => {
        console.error('Ошибка при проверке параметров:', error);
        showMessage('Ошибка при проверке параметров. Пожалуйста, попробуйте еще раз.', 'danger');
        return false;
    });
}

// Функция для предварительного просмотра загруженного файла
function previewFile(file, fileType) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);

    // Добавляем CSRF-токен из meta-тега
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    formData.append('csrf_token', csrfToken);

    return fetch('/api/file/preview', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken  // Добавляем токен также в заголовки
        }
    })
    .then(response => {
        if (!response.ok) {
            console.error(`HTTP ошибка! статус: ${response.status}`);
            return response.text().then(text => {
                console.error(`Содержимое ответа: ${text}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        // Создаем модальное окно для просмотра данных
        const modalId = `preview-modal-${fileType}`;
        let modal = document.getElementById(modalId);

        // Если модальное окно уже существует, удаляем его
        if (modal) {
            modal.remove();
        }

        // Создаем новое модальное окно
        modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal fade';
        modal.tabIndex = '-1';
        modal.setAttribute('aria-hidden', 'true');

        // Формируем заголовок в зависимости от типа файла
        let fileTypeTitle = '';
        switch (fileType) {
            case 'rock_properties':
                fileTypeTitle = 'Свойства породы';
                break;
            case 'capillary_pressure':
                fileTypeTitle = 'Капиллярное давление';
                break;
            case 'relative_perm':
                fileTypeTitle = 'Относительная проницаемость';
                break;
            case 'pvt_data':
                fileTypeTitle = 'PVT-данные';
                break;
            case 'production_data':
                fileTypeTitle = 'Данные добычи';
                break;
            default:
                fileTypeTitle = 'Данные файла';
        }

        // Строим содержимое модального окна
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Предварительный просмотр: ${fileTypeTitle}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        ${data.columns.map(col => `<th>${col}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.preview.map(row => `
                                        <tr>
                                            ${data.columns.map(col => `<td>${row[col] !== null ? row[col] : ''}</td>`).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        <div class="mt-3">
                            <h6>Статистика:</h6>
                            <ul>
                                <li>Всего строк: ${data.total_rows}</li>
                                ${Object.entries(data.stats).map(([col, stat]) => {
                                    if (stat.type === 'numeric') {
                                        return `<li>${col}: мин = ${formatNumber(stat.min)}, макс = ${formatNumber(stat.max)}, среднее = ${formatNumber(stat.mean)}</li>`;
                                    } else {
                                        return `<li>${col}: ${stat.unique} уникальных значений</li>`;
                                    }
                                }).join('')}
                            </ul>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                    </div>
                </div>
            </div>
        `;

        // Добавляем модальное окно на страницу
        document.body.appendChild(modal);

        // Показываем модальное окно
        const modalElement = new bootstrap.Modal(modal);
        modalElement.show();

        return data;
    })
    .catch(error => {
        console.error('Ошибка при предварительном просмотре файла:', error);
        showMessage('Ошибка при загрузке файла. Пожалуйста, проверьте формат файла и попробуйте еще раз.', 'danger');
    });
}

// Функция для валидации загруженного файла
function validateFile(file, fileType) {
    console.log(`Валидация файла: ${file.name}, тип: ${fileType || 'не указан'}`);

    const formData = new FormData();
    formData.append('file', file);

    // Добавляем file_type только если он определен
    if (fileType) {
        formData.append('file_type', fileType);
    }

    // Добавляем CSRF-токен из meta-тега
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    formData.append('csrf_token', csrfToken);

    // Выводим информацию о formData для отладки
    console.log("FormData содержит следующие поля:");
    for (let pair of formData.entries()) {
        console.log(`${pair[0]}: ${pair[1]}`);
    }

    return fetch('/api/file/validate', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken  // Добавляем токен также в заголовки
        }
    })
    .then(response => {
        if (!response.ok) {
            console.error(`HTTP ошибка! статус: ${response.status}`);
            return response.text().then(text => {
                console.error(`Содержимое ответа: ${text}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("Ответ от сервера:", data);
        if (data.valid) {
            showMessage(`Файл успешно проверен: ${data.message}`, 'success');
            return true;
        } else {
            showMessage(`Ошибка в файле: ${data.message}`, 'danger');
            return false;
        }
    })
    .catch(error => {
        console.error('Ошибка при валидации файла:', error);
        showMessage('Ошибка при проверке файла. Пожалуйста, попробуйте еще раз.', 'danger');
        return false;
    });
}

// Функция для загрузки параметров пресета породы
function loadRockPreset(rockType) {
    if (!rockType) return Promise.resolve({});

    return fetch(`/api/rock_presets/${rockType}`)
        .then(response => response.json())
        .then(data => {
            // Заполняем поля формы данными из пресета
            Object.entries(data).forEach(([param, value]) => {
                const input = document.querySelector(`input[name="${param}"]`);
                if (input) {
                    input.value = value;

                    // Обновляем значение ползунка, если он есть
                    const range = document.querySelector(`input[type="range"][data-target="${param}"]`);
                    if (range) {
                        range.value = value;
                    }
                }
            });

            return data;
        })
        .catch(error => {
            console.error('Ошибка при загрузке пресета породы:', error);
            showMessage('Ошибка при загрузке параметров породы. Пожалуйста, попробуйте еще раз.', 'danger');
            return {};
        });
}

// Обработчик изменения типа модели
function handleModelTypeChange() {
    const modelType = document.querySelector('input[name="model_type"]:checked').value;
    const carbonateFields = document.querySelectorAll('.carbonate-only');

    if (modelType === 'carbonate') {
        // Показываем поля для карбонатной модели
        carbonateFields.forEach(field => {
            field.style.display = 'block';
        });
    } else {
        // Скрываем поля для карбонатной модели
        carbonateFields.forEach(field => {
            field.style.display = 'none';
        });
    }
}

// Обработчик изменения типа породы
function handleRockTypeChange() {
    const rockType = document.querySelector('select[name="rock_type"]').value;
    if (rockType) {
        loadRockPreset(rockType);
    }
}

// Инициализация ползунков параметров
function initSliders() {
    document.querySelectorAll('input[type="range"]').forEach(slider => {
        const targetName = slider.dataset.target;
        const targetInput = document.querySelector(`input[name="${targetName}"]`);

        // Синхронизация значения ползунка с полем ввода
        slider.addEventListener('input', () => {
            targetInput.value = slider.value;
        });

        // Синхронизация значения поля ввода с ползунком
        targetInput.addEventListener('input', () => {
            slider.value = targetInput.value;
        });

        // Инициализация значения ползунка
        slider.value = targetInput.value;
    });
}

// Обработчик загрузки файла
function handleFileUpload() {
    document.querySelectorAll('input[type="file"]').forEach(fileInput => {
        // Проверяем наличие атрибута 'name' у элемента fileInput
        const fileType = fileInput.getAttribute('name') || '';
        const previewButton = document.querySelector(`#preview-${fileType}`);

        fileInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                // Показываем имя выбранного файла
                const fileNameElement = document.querySelector(`#${fileType}-filename`);
                if (fileNameElement) {
                    fileNameElement.textContent = file.name;
                }

                // Показываем кнопку предварительного просмотра
                if (previewButton) {
                    previewButton.style.display = 'inline-block';
                }

                // Валидация файла только если fileType определен
                if (fileType) {
                    validateFile(file, fileType);
                }
            }
        });

        // Обработчик нажатия на кнопку предварительного просмотра
        if (previewButton) {
            previewButton.addEventListener('click', () => {
                const file = fileInput.files[0];
                if (file) {
                    previewFile(file, fileType);
                }
            });
        }
    });
}

// Инициализация всех компонентов при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Инициализация ползунков параметров
    initSliders();

    // Инициализация обработчиков изменения типа модели и породы
    const modelTypeInputs = document.querySelectorAll('input[name="model_type"]');
    if (modelTypeInputs.length > 0) {
        modelTypeInputs.forEach(input => {
            input.addEventListener('change', handleModelTypeChange);
        });
        // Вызываем обработчик для инициализации состояния
        handleModelTypeChange();
    }

    const rockTypeSelect = document.querySelector('select[name="rock_type"]');
    if (rockTypeSelect) {
        rockTypeSelect.addEventListener('change', handleRockTypeChange);
    }

    // Инициализация обработчиков загрузки файлов
    handleFileUpload();

    // Обработчик отправки формы создания/редактирования проекта
const projectForm = document.querySelector('#project-form');
if (projectForm) {
    projectForm.addEventListener('submit', (event) => {
        event.preventDefault();

        // Собираем параметры модели
        const modelParams = {};
        document.querySelectorAll('.model-param input').forEach(input => {
            modelParams[input.name] = input.value;
        });

        // Выводим параметры для отладки
        console.log("Отправляемые параметры модели:", modelParams);

        // Получаем CSRF-токен
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

        // Проверяем параметры модели
        fetch('/api/parameters/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(modelParams)
        })
        .then(response => {
            if (!response.ok) {
                console.error(`HTTP ошибка! статус: ${response.status}`);
                return response.text().then(text => {
                    console.error(`Содержимое ответа: ${text}`);
                    throw new Error(`HTTP error! status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Результат проверки параметров:", data);

            if (data.valid) {
                // Если параметры валидны, отправляем форму
                console.log("Параметры прошли валидацию, отправляем форму");
                projectForm.submit();
            } else {
                // Отображаем ошибки на форме
                Object.entries(data.errors || {}).forEach(([param, message]) => {
                    const inputField = document.querySelector(`input[name="${param}"]`);
                    if (inputField) {
                        const formGroup = inputField.closest('.form-group');
                        formGroup.classList.add('has-error');

                        // Добавляем сообщение об ошибке
                        let feedbackElement = formGroup.querySelector('.invalid-feedback');
                        if (!feedbackElement) {
                            feedbackElement = document.createElement('div');
                            feedbackElement.className = 'invalid-feedback';
                            formGroup.appendChild(feedbackElement);
                        }
                        feedbackElement.textContent = message;
                        feedbackElement.style.display = 'block';
                    }
                });

                showMessage('Пожалуйста, исправьте ошибки в параметрах модели.', 'danger');
            }
        })
        .catch(error => {
            console.error('Ошибка при проверке параметров:', error);
            showMessage('Ошибка при проверке параметров модели. Пожалуйста, попробуйте еще раз.', 'danger');
        });
    });
}

    // Инициализация всплывающих подсказок
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});