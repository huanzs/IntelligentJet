-- @Time    : 2026/8/19 10:00
-- @Author  : Jason Huan
-- @Email   : 549473121@qq.com
-- @File    : rbac_db.sql
-- @Project : intelligent-jet

/*
 Navicat Premium Dump SQL

 Source Server         : local
 Source Server Type    : MySQL
 Source Server Version : 80016 (8.0.16)
 Source Host           : localhost:3306
 Source Schema         : rbac_db

 Target Server Type    : MySQL
 Target Server Version : 80016 (8.0.16)
 File Encoding         : 65001

 Date: 08/05/2026 00:18:41
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for permissions
-- ----------------------------
DROP TABLE IF EXISTS `permissions`;
CREATE TABLE `permissions`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of permissions
-- ----------------------------
INSERT INTO `permissions` VALUES (1, 'user:read', '查看用户', '查看用户列表和详情', '2026-04-14 22:15:24');
INSERT INTO `permissions` VALUES (2, 'user:write', '管理用户', '创建、编辑、删除用户及分配角色', '2026-04-14 22:15:24');
INSERT INTO `permissions` VALUES (3, 'role:read', '查看角色', '查看角色列表和详情', '2026-04-14 22:15:24');
INSERT INTO `permissions` VALUES (4, 'role:write', '管理角色', '创建、编辑、删除角色及分配权限', '2026-04-14 22:15:24');
INSERT INTO `permissions` VALUES (5, 'permission:read', '查看权限', '查看权限列表', '2026-04-14 22:15:24');
INSERT INTO `permissions` VALUES (6, 'permission:write', '管理权限', '创建和删除权限', '2026-04-14 22:15:24');
INSERT INTO `permissions` VALUES (7, 'operation:read', '查看操作', '', '2026-04-20 16:02:18');

-- ----------------------------
-- Table structure for role_permissions
-- ----------------------------
DROP TABLE IF EXISTS `role_permissions`;
CREATE TABLE `role_permissions`  (
  `role_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`role_id`, `permission_id`) USING BTREE,
  INDEX `fk_role_permissions_permission`(`permission_id` ASC) USING BTREE,
  CONSTRAINT `fk_role_permissions_permission` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_role_permissions_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of role_permissions
-- ----------------------------
INSERT INTO `role_permissions` VALUES (1, 1);
INSERT INTO `role_permissions` VALUES (2, 1);
INSERT INTO `role_permissions` VALUES (1, 2);
INSERT INTO `role_permissions` VALUES (1, 3);
INSERT INTO `role_permissions` VALUES (2, 3);
INSERT INTO `role_permissions` VALUES (1, 4);
INSERT INTO `role_permissions` VALUES (1, 5);
INSERT INTO `role_permissions` VALUES (1, 6);
INSERT INTO `role_permissions` VALUES (1, 7);

-- ----------------------------
-- Table structure for roles
-- ----------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of roles
-- ----------------------------
INSERT INTO `roles` VALUES (1, 'admin', '超级管理员', '2026-04-14 22:15:24');
INSERT INTO `roles` VALUES (2, 'viewer', '只读用户', '2026-04-14 22:15:24');

-- ----------------------------
-- Table structure for user_roles
-- ----------------------------
DROP TABLE IF EXISTS `user_roles`;
CREATE TABLE `user_roles`  (
  `user_id` int(11) NOT NULL,
  `role_id` int(11) NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`) USING BTREE,
  INDEX `fk_user_roles_role`(`role_id` ASC) USING BTREE,
  CONSTRAINT `fk_user_roles_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_user_roles_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_roles
-- ----------------------------
INSERT INTO `user_roles` VALUES (1, 1);
INSERT INTO `user_roles` VALUES (2, 2);

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password_hash` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `email` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'admin', 'scrypt:32768:8:1$gnmtAeDEE1rV42eO$8ebffd305b3bbc108ed91ec4888c05029602ca275abb69b575e24c0cd1bc07699f1d52bf48f31bf3d7a4b8653b9356ed2740734951b1926921d169233fa8f885', 'admin@example.com', 1, '2026-04-14 22:15:24', '2026-04-14 22:15:24');
INSERT INTO `users` VALUES (2, 'user', 'scrypt:32768:8:1$l6FEe7C0OxakyWCr$bd56cdb0203bca30d4f55b8f14a73e821e15b1a7053935a6e45e32ab8b8ef2de2a5fc8bbc5174b155eb72d64292db45ccd2792a095c0947758ee19cd3301f44c', 'user@163.com', 1, '2026-04-14 14:29:17', '2026-04-14 14:29:17');

SET FOREIGN_KEY_CHECKS = 1;
