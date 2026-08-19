-- @Time    : 2026/8/19 10:00
-- @Author  : Jason Huan
-- @Email   : 549473121@qq.com
-- @File    : init.sql
-- @Project : intelligent-jet

-- ============================================================
-- RBAC 权限管理系统 - 数据库初始化脚本
-- 使用方式: mysql -u root -p < init.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS rbac_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rbac_db;

-- -----------------------------------------------------------
-- 用户表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(64) NOT NULL UNIQUE,
  `password_hash` VARCHAR(256) NOT NULL,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- 角色表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `roles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(64) NOT NULL UNIQUE,
  `description` VARCHAR(256) DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- 权限表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `permissions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `code` VARCHAR(64) NOT NULL UNIQUE,
  `name` VARCHAR(64) NOT NULL,
  `description` VARCHAR(256) DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- 用户-角色关联表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_roles` (
  `user_id` INT NOT NULL,
  `role_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`),
  CONSTRAINT `fk_user_roles_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_roles_role` FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- 角色-权限关联表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `role_permissions` (
  `role_id` INT NOT NULL,
  `permission_id` INT NOT NULL,
  PRIMARY KEY (`role_id`, `permission_id`),
  CONSTRAINT `fk_role_permissions_role` FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_role_permissions_permission` FOREIGN KEY (`permission_id`) REFERENCES `permissions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 预置数据
-- ============================================================

-- 权限 (6 条)
INSERT INTO `permissions` (`code`, `name`, `description`) VALUES
  ('user:read',       '查看用户', '查看用户列表和详情'),
  ('user:write',      '管理用户', '创建、编辑、删除用户及分配角色'),
  ('role:read',       '查看角色', '查看角色列表和详情'),
  ('role:write',      '管理角色', '创建、编辑、删除角色及分配权限'),
  ('permission:read', '查看权限', '查看权限列表'),
  ('permission:write','管理权限', '创建和删除权限');

-- 角色 (2 条)
INSERT INTO `roles` (`name`, `description`) VALUES
  ('admin',  '超级管理员'),
  ('viewer', '只读用户');

-- 角色-权限: admin 拥有全部 6 个权限
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
  SELECT r.id, p.id FROM `roles` r, `permissions` p
  WHERE r.name = 'admin';

-- 角色-权限: viewer 只有 read 权限 (1, 3, 5)
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
  SELECT r.id, p.id FROM `roles` r, `permissions` p
  WHERE r.name = 'viewer' AND p.code IN ('user:read', 'role:read', 'permission:read');

-- 管理员用户 (密码: admin123, werkzeug scrypt hash)
INSERT INTO `users` (`username`, `password_hash`, `email`) VALUES
  ('admin', 'scrypt:32768:8:1$gnmtAeDEE1rV42eO$8ebffd305b3bbc108ed91ec4888c05029602ca275abb69b575e24c0cd1bc07699f1d52bf48f31bf3d7a4b8653b9356ed2740734951b1926921d169233fa8f885', 'admin@example.com');

-- 用户-角色: admin 用户 -> admin 角色
INSERT INTO `user_roles` (`user_id`, `role_id`)
  SELECT u.id, r.id FROM `users` u, `roles` r
  WHERE u.username = 'admin' AND r.name = 'admin';
