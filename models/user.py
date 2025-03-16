#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db
from models.project import Project

class User(UserMixin, db.Model):
    """Модель пользователя для аутентификации и управления проектами"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    company = db.Column(db.String(120))
    position = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(32), nullable=True)  # Токен для сброса пароля
    reset_token_expiry = db.Column(db.DateTime, nullable=True)  # Срок действия токена

    # Отношение один-ко-многим с проектами
    projects = db.relationship('Project', backref='owner', lazy='dynamic')

    def set_password(self, password):
        """Устанавливает хеш пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет соответствие пароля хешу"""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Обновляет время последнего входа"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def get_projects_count(self):
        """Возвращает количество проектов пользователя"""
        return self.projects.count()

    def get_recent_projects(self, limit=5):
        """Возвращает последние проекты пользователя"""
        return self.projects.order_by(Project.updated_at.desc()).limit(limit).all()

    def __repr__(self):
        return f'<User {self.username}>'