# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : response.py
# @Project : intelligent-jet

"""
统一响应格式模块 - 提供 success_response 和 error_response 工具函数
"""


from flask import jsonify


def success_response(data=None, message="success", code=200):
    response = jsonify({
        "code": code,
        "message": message,
        "data": data,
    })
    response.status_code = code
    return response


def error_response(message="error", code=400, data=None):
    response = jsonify({
        "code": code,
        "message": message,
        "data": data,
    })
    response.status_code = code
    return response


def paginate_query(query, page=1, per_page=20):
    """Paginate a SQLAlchemy query and return standardized response data."""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [item.to_dict() for item in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
    }
