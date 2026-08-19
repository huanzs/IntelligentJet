# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : users.py
# @Project : intelligent-jet

from flask import Blueprint, request
from app.models.user import User
from app.models.role import Role
from app.utils.auth import require_permission, get_current_user_id
from app.utils.response import success_response, error_response, paginate_query
from app.extensions import db

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("", methods=["GET"])
@require_permission("user:read")
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    query = User.query.order_by(User.id.desc())
    data = paginate_query(query, page, per_page)
    return success_response(data)


@users_bp.route("/<int:user_id>", methods=["GET"])
@require_permission("user:read")
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response("用户不存在", 404)
    return success_response(user.to_dict(include_permissions=True))


@users_bp.route("", methods=["POST"])
@require_permission("user:write")
def create_user():
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

    return success_response(user.to_dict(), "创建成功", 201)


@users_bp.route("/<int:user_id>", methods=["PUT"])
@require_permission("user:write")
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response("用户不存在", 404)

    data = request.get_json()
    if not data:
        return error_response("请求数据不能为空", 400)

    if "email" in data:
        email = data["email"].strip()
        existing = User.query.filter(User.email == email, User.id != user_id).first()
        if existing:
            return error_response("邮箱已被使用", 400)
        user.email = email

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            return error_response("密码长度不能少于6位", 400)
        user.set_password(data["password"])

    db.session.commit()
    return success_response(user.to_dict())


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@require_permission("user:write")
def delete_user(user_id):
    current_user_id = get_current_user_id()
    if user_id == current_user_id:
        return error_response("不能删除自己", 400)

    user = User.query.get(user_id)
    if not user:
        return error_response("用户不存在", 404)

    db.session.delete(user)
    db.session.commit()
    return success_response(message="删除成功")


@users_bp.route("/<int:user_id>/roles", methods=["PUT"])
@require_permission("user:write")
def assign_roles(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response("用户不存在", 404)

    data = request.get_json()
    if not data or "role_ids" not in data:
        return error_response("请提供角色ID列表", 400)

    role_ids = data["role_ids"]
    roles = Role.query.filter(Role.id.in_(role_ids)).all()
    user.roles = roles
    db.session.commit()
    return success_response(user.to_dict(include_permissions=True))
