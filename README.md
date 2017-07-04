CREATE DATABASE coding4fun_db;
CREATE USER cd4fun_u WITH PASSWORD 'mlmlml';
GRANT ALL PRIVILEGES ON DATABASE coding4fun_db TO cd4fun_u;

ALTER TABLE tb_classroom ADD progress Integer DEFAULT 10;
DROP TABLE tb_opinion;

ALTER TABLE tb_classroom REMOVE progress;