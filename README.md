CREATE DATABASE coding4fun_db;
CREATE USER cd4fun_u WITH PASSWORD 'mlmlml';
GRANT ALL PRIVILEGES ON DATABASE coding4fun_db TO cd4fun_u;

ALTER TABLE tb_classroom ADD links varchar[] DEFAULT array[]::varchar[];
DROP TABLE tb_opinion;

c4fpmlpnmcbkpo