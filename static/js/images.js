// images.js - Скрипты для работы с изображениями визуализаций

// Функция для загрузки списка доступных изображений
function loadProjectImages(projectId, format = 'png') {
    // Элемент для отображения изображений
    const imagesContainer = document.getElementById('images-container');
    if (!imagesContainer) {
        console.error('Контейнер для изображений не найден');
        return;
    }

    console.log(`Загрузка изображений для проекта ${projectId} в формате ${format}...`);

    // Показываем индикатор загрузки
    imagesContainer.innerHTML = `
        <div class="d-flex justify-content-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка изображений...</span>
            </div>
        </div>
    `;

    // Добавляем временную метку для предотвращения кэширования
    const timestamp = new Date().getTime();

    // Загружаем список изображений
    fetch(`/api/project/${projectId}/images?t=${timestamp}`)
        .then(response => {
            console.log('Ответ от сервера:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Данные от API изображений:', data);

            // Проверяем наличие изображений указанного формата
            const imagesList = data.images?.[format] || {};
            console.log(`Список изображений формата ${format}:`, imagesList);
            const imageNames = Object.keys(imagesList);
            console.log('Имена изображений:', imageNames);

            if (imageNames.length === 0) {
                imagesContainer.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> Изображения в формате ${format.toUpperCase()} не найдены.
                    </div>
                `;
                return;
            }

            // Создаем содержимое с изображениями
            imagesContainer.innerHTML = `
                <div class="row">
                    ${imageNames.map(name => {
                        // Создаем простой путь только с именем файла
                        const filename = name + '.' + format;
                        const imageUrl = `/project/${projectId}/image/${filename}`;
                        console.log(`Сформированный URL для ${name}: ${imageUrl}`);
                        
                        return `
                        <div class="col-lg-6 mb-4">
                            <div class="card">
                                <div class="card-header d-flex justify-content-between align-items-center">
                                    <h5 class="card-title">${formatImageName(name)}</h5>
                                    <a href="/project/${projectId}/download/image/${format}/${name}" 
                                       class="btn btn-sm btn-outline-primary" download>
                                        <i class="fas fa-download"></i> Скачать
                                    </a>
                                </div>
                                <div class="card-body text-center">
                                    <div class="position-relative">
                                        <img src="${imageUrl}" alt="${formatImageName(name)}" 
                                             class="img-fluid visualization-image" style="max-height: 400px;"
                                             onerror="this.onerror=null; console.error('Ошибка загрузки изображения:', this.src); this.style.display='none'; this.nextElementSibling.style.display='block';">
                                        <div class="alert alert-warning mt-3" style="display:none;">
                                            <i class="fas fa-exclamation-triangle"></i> Не удалось загрузить изображение. 
                                            Проверьте наличие файла на сервере.
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `}).join('')}
                </div>
            `;

            // Добавляем обработчики для увеличения изображений при клике
            document.querySelectorAll('.visualization-image').forEach(img => {
                img.addEventListener('click', function() {
                    if (this.style.display !== 'none') {
                        showFullsizeImage(this.src, this.alt);
                    }
                });
            });
        })
        .catch(error => {
            console.error('Ошибка при загрузке списка изображений:', error);
            imagesContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i> Ошибка при загрузке изображений: ${error.message}
                    <button class="btn btn-sm btn-outline-danger ms-3" 
                            onclick="loadProjectImages(${projectId}, '${format}')">
                        <i class="fas fa-sync"></i> Повторить
                    </button>
                </div>
            `;
        });
}


// Форматирование имени изображения для отображения
function formatImageName(name) {
    // Преобразуем имя_с_подчеркиваниями в "Имя с пробелами"
    const formattedName = name.replace(/_/g, ' ').replace(/-/g, ' ');

    // Делаем первую букву заглавной и добавляем соответствующее название
    switch (formattedName) {
        case 'saturation profiles':
            return 'Профили насыщенности';
        case 'saturation difference':
            return 'Разница в насыщенности';
        case 'saturation evolution':
            return 'Эволюция насыщенности';
        case 'recovery factor':
            return 'Коэффициент нефтеотдачи';
        case 'breakthrough time':
            return 'Время прорыва воды';
        case 'capillary pressure':
            return 'Капиллярное давление';
        case 'fractional flow':
            return 'Функция Баклея-Леверетта';
        case 'relative permeability':
            return 'Относительная проницаемость';
        default:
            return formattedName.charAt(0).toUpperCase() + formattedName.slice(1);
    }
}

// Функция для отображения изображения в полном размере
function showFullsizeImage(src, alt) {
    // Создаем модальное окно для просмотра изображения
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'image-fullsize-modal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-hidden', 'true');

    modal.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${alt}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${src}" alt="${alt}" class="img-fluid">
                </div>
                <div class="modal-footer">
                    <a href="${src}" class="btn btn-primary" download>
                        <i class="fas fa-download"></i> Скачать
                    </a>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                </div>
            </div>
        </div>
    `;

    // Удаляем существующее модальное окно, если оно есть
    const existingModal = document.getElementById('image-fullsize-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Добавляем модальное окно на страницу
    document.body.appendChild(modal);

    // Создаем объект модального окна и показываем его
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();

    // Добавляем обработчик закрытия для удаления модального окна
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
}

// Инициализация компонентов при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем наличие вкладки с изображениями
    const imagesTab = document.getElementById('images-tab');
    if (!imagesTab) return;

    // Получаем ID проекта
    const projectId = document.getElementById('visualization-container')?.dataset.projectId;
    if (!projectId) {
        console.error('ID проекта не найден');
        return;
    }

    // Обработчик для переключения вкладки с изображениями
    imagesTab.addEventListener('shown.bs.tab', function (e) {
        // Определяем активный формат
        const activeFormat = document.getElementById('btn-format-png').classList.contains('active') ? 'png' : 'svg';
        // Загружаем изображения
        loadProjectImages(projectId, activeFormat);
    });

    // Обработчики для кнопок переключения формата
    document.getElementById('btn-format-png')?.addEventListener('click', function() {
        document.getElementById('btn-format-svg').classList.remove('active');
        this.classList.add('active');
        loadProjectImages(projectId, 'png');
    });

    document.getElementById('btn-format-svg')?.addEventListener('click', function() {
        document.getElementById('btn-format-png').classList.remove('active');
        this.classList.add('active');
        loadProjectImages(projectId, 'svg');
    });

    // Если URL содержит хэш #images, активируем вкладку с изображениями
    if (window.location.hash === '#images') {
        const imagesTabObj = new bootstrap.Tab(imagesTab);
        imagesTabObj.show();
    }
});