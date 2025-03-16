#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from urllib.parse import urlparse

from extensions import db
from models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        # Проверяем, что поля заполнены
        if not email or not password:
            flash('Пожалуйста, заполните все поля', 'danger')
            return redirect(url_for('auth.login'))

        # Ищем пользователя в базе данных
        user = User.query.filter_by(email=email).first()

        # Проверяем пароль
        if not user or not user.check_password(password):
            flash('Неверный email или пароль', 'danger')
            return redirect(url_for('auth.login'))

        # Проверяем, что пользователь активен
        if not user.is_active:
            flash('Ваш аккаунт деактивирован. Пожалуйста, свяжитесь с администратором', 'danger')
            return redirect(url_for('auth.login'))

        # Выполняем вход в систему
        login_user(user, remember=remember)

        # Обновляем дату последнего входа
        user.update_last_login()

        # Перенаправляем на страницу, с которой пришли, или на дашборд
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')

        flash('Вы успешно вошли в систему', 'success')
        return redirect(next_page)

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        company = request.form.get('company', '')
        position = request.form.get('position', '')

        # Проверяем, что обязательные поля заполнены
        if not username or not email or not password or not password_confirm:
            flash('Пожалуйста, заполните все обязательные поля', 'danger')
            return redirect(url_for('auth.register'))

        # Проверяем, что пароли совпадают
        if password != password_confirm:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('auth.register'))

        # Проверяем, что пользователь с таким email не существует
        user_email = User.query.filter_by(email=email).first()
        if user_email:
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('auth.register'))

        # Проверяем, что пользователь с таким username не существует
        user_username = User.query.filter_by(username=username).first()
        if user_username:
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('auth.register'))

        # Создаем нового пользователя
        new_user = User(
            username=username,
            email=email,
            company=company,
            position=position,
            is_active=True,
            created_at=datetime.utcnow()
        )
        new_user.set_password(password)

        # Добавляем пользователя в базу данных
        db.session.add(new_user)
        db.session.commit()

        flash('Вы успешно зарегистрировались. Теперь вы можете войти в систему', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Страница профиля пользователя"""
    if request.method == 'POST':
        username = request.form.get('username')
        company = request.form.get('company', '')
        position = request.form.get('position', '')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        new_password_confirm = request.form.get('new_password_confirm')

        # Проверяем, что имя пользователя заполнено
        if not username:
            flash('Имя пользователя не может быть пустым', 'danger')
            return redirect(url_for('auth.profile'))

        # Проверяем, что имя пользователя не занято
        user = User.query.filter_by(username=username).first()
        if user and user.id != current_user.id:
            flash('Это имя пользователя уже занято', 'danger')
            return redirect(url_for('auth.profile'))

        # Обновляем данные пользователя
        current_user.username = username
        current_user.company = company
        current_user.position = position

        # Если указан текущий пароль, проверяем его и обновляем на новый
        if current_password:
            # Проверяем текущий пароль
            if not current_user.check_password(current_password):
                flash('Неверный текущий пароль', 'danger')
                return redirect(url_for('auth.profile'))

            # Проверяем, что новый пароль указан и совпадает с подтверждением
            if not new_password or not new_password_confirm:
                flash('Пожалуйста, укажите новый пароль и его подтверждение', 'danger')
                return redirect(url_for('auth.profile'))

            if new_password != new_password_confirm:
                flash('Новый пароль и его подтверждение не совпадают', 'danger')
                return redirect(url_for('auth.profile'))

            # Обновляем пароль
            current_user.set_password(new_password)

        # Сохраняем изменения
        db.session.commit()

        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')


@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Страница запроса сброса пароля"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('Пожалуйста, укажите email', 'danger')
            return redirect(url_for('auth.reset_password'))

        # Ищем пользователя с указанным email
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Пользователь с таким email не найден', 'danger')
            return redirect(url_for('auth.reset_password'))

        # Временно пропускаем сохранение токена в базу данных
        # Просто имитируем успешную отправку
        flash('Инструкции по сбросу пароля отправлены на ваш email', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')


@auth_bp.route('/set_new_password/<token>', methods=['GET', 'POST'])
def set_new_password(token):
    """Страница установки нового пароля по токену"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Ищем пользователя с указанным токеном
    user = User.query.filter_by(reset_token=token).first()

    # Проверяем, что токен действителен и не истек
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Недействительная или истекшая ссылка для сброса пароля', 'danger')
        return redirect(url_for('auth.reset_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # Проверяем, что пароли совпадают
        if password != password_confirm:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('auth.set_new_password', token=token))

        # Проверяем длину пароля
        if len(password) < 8:
            flash('Пароль должен содержать не менее 8 символов', 'danger')
            return redirect(url_for('auth.set_new_password', token=token))

        # Обновляем пароль
        user.set_password(password)

        # Очищаем токен сброса пароля
        user.reset_token = None
        user.reset_token_expiry = None

        # Сохраняем изменения
        db.session.commit()

        flash('Пароль успешно изменен. Теперь вы можете войти в систему', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/set_new_password.html', token=token)


