# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : permission.py
# @Project : intelligent-jet

from app.extensions import db
from datetime import datetime


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
