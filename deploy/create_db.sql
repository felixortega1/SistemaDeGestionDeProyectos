-- Ejecutar en el servidor: sudo mysql < create_db.sql   (cambiar CLAVE_LARGA; generar con: openssl rand -base64 24)
-- Base propia: no toca RAINAU ni Ruteame.
CREATE DATABASE IF NOT EXISTS gestion_proyectos_db CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'gestion_proyectos_app'@'localhost' IDENTIFIED BY 'CLAVE_LARGA';
CREATE USER IF NOT EXISTS 'gestion_proyectos_app'@'127.0.0.1' IDENTIFIED BY 'CLAVE_LARGA';
GRANT ALL PRIVILEGES ON gestion_proyectos_db.* TO 'gestion_proyectos_app'@'localhost';
GRANT ALL PRIVILEGES ON gestion_proyectos_db.* TO 'gestion_proyectos_app'@'127.0.0.1';
FLUSH PRIVILEGES;
