# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : auth.py
# @Project : intelligent-jet

from flask import Blueprint, request
from app.models.user import User
from app.models.role import Role
from app.utils.auth import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
    login_required,
    get_current_user_id,
)
from app.utils.response import success_response, error_response
from app.extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return error_response("请求数据不能为空", 400)

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return error_response("用户名、邮箱和密码不能为空", 400)

    if len(password) < 6:
        return error_response("密码长度不能少于6位", 400)

    if User.query.filter_by(username=username).first():
        return error_response("用户名已存在", 400)

    if User.query.filter_by(email=email).first():
        return error_response("邮箱已被注册", 400)

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return success_response(user.to_dict(), "注册成功", 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return error_response("请求数据不能为空", 400)

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error_response("用户名和密码不能为空", 400)

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return error_response("用户名或密码错误", 401)

    if not user.is_active:
        return error_response("账号已被禁用", 403)

    access_token = generate_access_token(user.id)
    refresh_token = generate_refresh_token(user.id)

    return success_response({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(include_permissions=True),
    })


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json()
    if not data:
        return error_response("请求数据不能为空", 400)

    refresh_token = data.get("refresh_token", "")
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return error_response("刷新令牌无效或已过期", 401)

    user = User.query.get(payload.get("sub"))
    if not user or not user.is_active:
        return error_response("用户不存在或已禁用", 401)

    new_access_token = generate_access_token(user.id)
    return success_response({"access_token": new_access_token})


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user_id = get_current_user_id()
    user = User.query.get(user_id)
    return success_response(user.to_dict(include_permissions=True))
