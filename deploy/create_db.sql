-- Ejecutar en el MySQL 8.0 compartido como root: sudo mysql < create_db.sql
-- Base y usuario PROPIOS: no se toca nada de RAINAU ni Ruteame.
CREATE DATABASE IF NOT EXISTS gestion_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'gestion_app'@'127.0.0.1' IDENTIFIED BY 'CAMBIAR';
CREATE USER IF NOT EXISTS 'gestion_app'@'localhost' IDENTIFIED BY 'CAMBIAR';
GRANT ALL PRIVILEGES ON gestion_app_db.* TO 'gestion_app'@'127.0.0.1';
GRANT ALL PRIVILEGES ON gestion_app_db.* TO 'gestion_app'@'localhost';
FLUSH PRIVILEGES;
-- Opcional (solo si se crea un entorno de pruebas tipo ruteame-test): repetir con gestion_test_db / gestion_test.
