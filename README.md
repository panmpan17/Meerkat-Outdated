CREATE DATABASE coding4fun_db;
CREATE USER cd4fun_u WITH PASSWORD 'mlmlml';
GRANT ALL PRIVILEGES ON DATABASE coding4fun_db TO cd4fun_u;


ALTER TABLE tb_user ADD active bool DEFAULT FALSE;
ALTER TABLE tb_user ADD disbaled bool DEFAULT FALSE;