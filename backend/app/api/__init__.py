# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : __init__.py
# @Project : intelligent-jet

"""
API 蓝图注册模块 - 统一注册 auth/users/roles/permissions 四组 REST API 蓝图
"""


from app.api.auth import auth_bp
from app.api.users import users_bp
from app.api.roles import roles_bp
from app.api.permissions import permissions_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(permissions_bp)
