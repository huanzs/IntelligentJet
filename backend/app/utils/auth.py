# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : auth.py
# @Project : intelligent-jet

import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app
from functools import wraps
from flask import request


def generate_access_token(user_id):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def generate_refresh_token(user_id):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(seconds=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user_id():
    """Extract user_id from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    return payload.get("sub")


def require_permission(permission_code):
    """Decorator that checks if the current user has the required permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.models.user import User
            from app.utils.response import error_response

            user_id = get_current_user_id()
            if not user_id:
                return error_response("认证失败", 401)

            user = User.query.get(user_id)
            if not user or not user.is_active:
                return error_response("用户不存在或已禁用", 401)

            permissions = user.get_permissions()
            if permission_code not in permissions:
                return error_response("权限不足", 403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def login_required(f):
    """Decorator that checks if the user is authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.utils.response import error_response

        user_id = get_current_user_id()
        if not user_id:
            return error_response("认证失败", 401)

        from app.models.user import User
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return error_response("用户不存在或已禁用", 401)

        return f(*args, **kwargs)
    return decorated_function
