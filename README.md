CREATE DATABASE coding4fun_db;
postgres# CREATE USER cd4fun_u WITH PASSWORD 'mlmlml';
postgres# GRANT ALL PRIVILEGES ON DATABASE coding4fun_db TO cd4fun_u;


ALTER TABLE tb_user ADD active bool DEFAULT FLASE;
ALTER TABLE tb_user ADD disbaled bool DEFAULT FLASE;

ALTER TABLE tb_user DROP active;