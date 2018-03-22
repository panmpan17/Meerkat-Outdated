CREATE DATABASE coding4fun_db;
CREATE USER cd4fun_u WITH PASSWORD 'mlmlml';
GRANT ALL PRIVILEGES ON DATABASE coding4fun_db TO cd4fun_u;

ALTER TABLE tb_teacher ADD contact_link json DEFAULT '{}';
ALTER TABLE tb_post ADD title varchar;

ALTER TABLE tb_user ADD type integer DEFAULT '0';
UPDATE tb_user SET type='2' where admin=true;
ALTER TABLE tb_user DROP admin;

# need to start server first and close it
INSERT INTO tb_teacherinfo (id, name, phone, ext_area, whole_city, class_permission, summary, contact_link) select id, name, phone, ext_area, whole_city, class_permission, summary, contact_link from tb_teacher;
DORP TABLE tb_adarea, tb_adclass, tb_classroom;