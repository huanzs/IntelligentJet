# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : permissions.py
# @Project : intelligent-jet

from flask import Blueprint, request
from app.models.permission import Permission
from app.utils.auth import require_permission
from app.utils.response import success_response, error_response, paginate_query
from app.extensions import db

permissions_bp = Blueprint("permissions", __name__, url_prefix="/api/permissions")


@permissions_bp.route("", methods=["GET"])
@require_permission("permission:read")
def list_permissions():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    query = Permission.query.order_by(Permission.id.asc())
    data = paginate_query(query, page, per_page)
    return success_response(data)


@permissions_bp.route("", methods=["POST"])
@require_permission("permission:write")
def create_permission():
    data = request.get_json()
    if not data:
        return error_response("请求数据不能为空", 400)

    code = data.get("code", "").strip()
    name = data.get("name", "").strip()

    if not code or not name:
        return error_response("权限编码和名称不能为空", 400)

    if Permission.query.filter_by(code=code).first():
        return error_response("权限编码已存在", 400)

    permission = Permission(code=code, name=name, description=data.get("description", ""))
    db.session.add(permission)
    db.session.commit()

    return success_response(permission.to_dict(), "创建成功", 201)


@permissions_bp.route("/<int:permission_id>", methods=["DELETE"])
@require_permission("permission:write")
def delete_permission(permission_id):
    permission = Permission.query.get(permission_id)
    if not permission:
        return error_response("权限不存在", 404)

    db.session.delete(permission)
    db.session.commit()
    return success_response(message="删除成功")
