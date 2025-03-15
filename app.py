#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template
import os
from extensions import db, migrate, login_manager, csrf
from datetime import datetime
from config import Config, ProductionConfig

def create_app(config_class=Config):
    """Функция-фабрика для создания экземпляра Flask-приложения"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Импорт моделей
    from models.user import User
    from models.project import Project, ProjectData, ProjectResult

    # Загрузчик пользователя для Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Контекст-процессор для передачи now в шаблоны
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    # Регистрация blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Обработчик ошибки 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # Обработчик ошибки 500
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Создание директорий для загрузки файлов и базы данных
    create_upload_directories(app)
    with app.app_context():
        db.create_all()

    return app


# Функция для создания директорий для загрузки файлов
def create_upload_directories(app):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
    # Создаем директорию для изображений
    os.makedirs(app.config['IMAGES_FOLDER'], exist_ok=True)


# Для продакшена
if os.environ.get('FLASK_ENV') == 'production':
    app = create_app(ProductionConfig)
else:
    app = create_app()

# Точка входа для запуска приложения
if __name__ == '__main__':
    app.run(debug=True)