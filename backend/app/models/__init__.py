# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : __init__.py
# @Project : intelligent-jet

"""
数据模型聚合模块 - 统一导出 User/Role/Permission 模型和关联表
"""


from app.models.user import User, user_roles
from app.models.role import Role, role_permissions
from app.models.permission import Permission
