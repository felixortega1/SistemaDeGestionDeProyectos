-- Ejecutar en MySQL Workbench (conexion root a 127.0.0.1:3307) sobre el MySQL 8.0.46 local.
-- Solo crea objetos NUEVOS; no toca la base de Ruteame.
CREATE DATABASE IF NOT EXISTS gestion_app_db CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'gestion_app'@'localhost' IDENTIFIED BY 'local-dev-pass';
CREATE USER IF NOT EXISTS 'gestion_app'@'127.0.0.1' IDENTIFIED BY 'local-dev-pass';
GRANT ALL ON gestion_app_db.* TO 'gestion_app'@'localhost';
GRANT ALL ON gestion_app_db.* TO 'gestion_app'@'127.0.0.1';
-- pytest crea y borra test_gestion_app_db
GRANT ALL ON `test\_%`.* TO 'gestion_app'@'localhost';
GRANT ALL ON `test\_%`.* TO 'gestion_app'@'127.0.0.1';
FLUSH PRIVILEGES;
SELECT VERSION();
