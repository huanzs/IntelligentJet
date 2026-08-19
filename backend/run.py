# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : run.py
# @Project : intelligent-jet

"""
Flask 应用启动入口 - 创建应用实例并运行开发服务器
"""


from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission

app = create_app()


@app.cli.command("seed")
def seed():
    """Seed the database with initial data."""
    # Create permissions
    perm_defs = [
        ("user:read", "查看用户", "查看用户列表和详情"),
        ("user:write", "管理用户", "创建、编辑、删除用户及分配角色"),
        ("role:read", "查看角色", "查看角色列表和详情"),
        ("role:write", "管理角色", "创建、编辑、删除角色及分配权限"),
        ("permission:read", "查看权限", "查看权限列表"),
        ("permission:write", "管理权限", "创建和删除权限"),
    ]
    perms = {}
    for code, name, desc in perm_defs:
        existing = Permission.query.filter_by(code=code).first()
        if existing:
            perms[code] = existing
        else:
            perm = Permission(code=code, name=name, description=desc)
            db.session.add(perm)
            perms[code] = perm

    db.session.flush()

    # Create admin role
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="超级管理员")
        db.session.add(admin_role)
        db.session.flush()
        admin_role.permissions = list(perms.values())

    # Create viewer role
    viewer_role = Role.query.filter_by(name="viewer").first()
    if not viewer_role:
        viewer_role = Role(name="viewer", description="只读用户")
        db.session.add(viewer_role)
        db.session.flush()
        viewer_role.permissions = [perms["user:read"], perms["role:read"], perms["permission:read"]]

    # Create admin user
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        admin_user = User(username="admin", email="admin@example.com")
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.flush()
        admin_user.roles = [admin_role]

    db.session.commit()
    print("Seed data created successfully!")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
