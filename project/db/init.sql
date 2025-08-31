-- Init script for Enova project

CREATE DATABASE IF NOT EXISTS enova;

CREATE USER IF NOT EXISTS 'enova_user'@'%' IDENTIFIED BY 'enova_pass';
GRANT ALL PRIVILEGES ON enova.* TO 'enova_user'@'%';
FLUSH PRIVILEGES;

USE enova;

CREATE TABLE IF NOT EXISTS t_enova_analise_eficiencia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dt_analise DATE NOT NULL,
    nr_producao_energia DECIMAL(10,2) NOT NULL,
    nr_consumo_energia DECIMAL(10,2) NOT NULL,
    nr_eficiencia DECIMAL(10,2) NOT NULL
);
