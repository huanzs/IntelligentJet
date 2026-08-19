# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : roles.py
# @Project : intelligent-jet

"""
角色管理 API 模块 - 提供角色 CRUD 和权限分配接口
"""


from flask import Blueprint, request
from app.models.role import Role
from app.models.permission import Permission
from app.utils.auth import require_permission
from app.utils.response import success_response, error_response, paginate_query
from app.extensions import db

roles_bp = Blueprint("roles", __name__, url_prefix="/api/roles")


@roles_bp.route("", methods=["GET"])
@require_permission("role:read")
def list_roles():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    query = Role.query.order_by(Role.id.desc())
    data = paginate_query(query, page, per_page)
    return success_response(data)


@roles_bp.route("/<int:role_id>", methods=["GET"])
@require_permission("role:read")
def get_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return error_response("角色不存在", 404)
    return success_response(role.to_dict(include_permissions=True))


@roles_bp.route("", methods=["POST"])
@require_permission("role:write")
def create_role():
    data = request.get_json()
    if not data:
        return error_response("请求数据不能为空", 400)

    name = data.get("name", "").strip()
    if not name:
        return error_response("角色名称不能为空", 400)

    if Role.query.filter_by(name=name).first():
        return error_response("角色名称已存在", 400)

    role = Role(name=name, description=data.get("description", ""))
    db.session.add(role)
    db.session.commit()

    return success_response(role.to_dict(), "创建成功", 201)


@roles_bp.route("/<int:role_id>", methods=["PUT"])
@require_permission("role:write")
def update_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return error_response("角色不存在", 404)

    data = request.get_json()
    if not data:
        return error_response("请求数据不能为空", 400)

    if "name" in data:
        name = data["name"].strip()
        existing = Role.query.filter(Role.name == name, Role.id != role_id).first()
        if existing:
            return error_response("角色名称已存在", 400)
        role.name = name

    if "description" in data:
        role.description = data["description"]

    db.session.commit()
    return success_response(role.to_dict())


@roles_bp.route("/<int:role_id>", methods=["DELETE"])
@require_permission("role:write")
def delete_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return error_response("角色不存在", 404)

    if role.users.count() > 0:
        return error_response("该角色下还有用户，无法删除", 400)

    db.session.delete(role)
    db.session.commit()
    return success_response(message="删除成功")


@roles_bp.route("/<int:role_id>/permissions", methods=["PUT"])
@require_permission("role:write")
def assign_permissions(role_id):
    role = Role.query.get(role_id)
    if not role:
        return error_response("角色不存在", 404)

    data = request.get_json()
    if not data or "permission_ids" not in data:
        return error_response("请提供权限ID列表", 400)

    permission_ids = data["permission_ids"]
    permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
    role.permissions = permissions
    db.session.commit()
    return success_response(role.to_dict(include_permissions=True))
