from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy import Boolean, DateTime, Text, ARRAY, JSON, Time, Date
from datetime import datetime, timedelta
from cherrypy import HTTPError as httperror
from uuid import uuid1
from hashlib import sha256
import os
# from pytz import timezone

def GMT(t):
    # G = timezone("GMT")
    # utc = t.utcnow()
    t += timedelta(hours=8)
    fmt = '%Y / %m / %d %H:%M'
    return t.strftime(fmt)

def hash(v):
    return sha256(v.encode()).hexdigest()

class ErrMsg:
    NOT_DICT = "Must be a dictionary"
    UNKNOWN_PARAM = "Unknown parameter '{}'"
    MISS_PARAM = "The '{}' is missing."
    NOT_INT = "'{}' must be a integer"
    CANT_INPUT = "This param is autoincrement '{}'"

class User(object):
    TABLE_NAME = "tb_user"
    user_t = None

    def __init__(self):
        # require attributesf
        self.userid = None
        self.password = None
        self.birth_year = None
        self.nickname = None
        self.email = None
        # nullable attributes
        self.job = ""

    @classmethod
    def create_schema(cls, db_engine, db_meta, euf=None):
        cls.user_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("userid", String, nullable=False, autoincrement=False, unique=True),
            Column("password", String, nullable=False, autoincrement=False),
            Column("email", String, nullable=False, autoincrement=False),
            Column("birth_year", Integer, nullable=False, autoincrement=False),
            Column("nickname", String, nullable=False, autoincrement=False),
            Column("job", String, nullable=True, autoincrement=False),
            Column("point", Integer, default=0, nullable=True, autoincrement=True),
            Column("admin", Boolean, default=False, nullable=True, autoincrement=True),
            Column("expert", Integer, default=0, nullable=True, autoincrement=True),
            Column("create_at", DateTime, default=datetime.utcnow, autoincrement=True),
            Column("last_login", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                autoincrement=True),
            Column("active", Boolean, default=False, nullable=True, autoincrement=True),
            Column("disabled", Boolean, default=False, nullable=True, autoincrement=True),
            )
        cls.user_t.create(db_engine, checkfirst=True)
        cls.creat_user(db_meta, db_engine)
        if euf:
            cls.creat_user(db_meta, db_engine, filename=euf)
        return cls.user_t

    @classmethod
    def creat_user(cls, meta, engine, filename="user.txt"):
        f = open(filename)
        r = f.read()
        f.close()
        l = r.split("[\SPLIT/]")

        users_ = []
        for u in l:
            ujson = u.split("\n")
            ujson.remove("")
            j = {"admin": False}
            for i in ujson:
                key = i[:i.find("=")]
                value = i[i.find("=") + 1:]
                if key == "birth_year":
                    j[key] = int(value)
                elif key == "password":
                    if len(value) > 32:
                        j[key] = value
                        continue
                    j[key] = hash(value)
                elif key == "admin":
                    j[key] = bool(value)
                else:
                    j[key] = value
            users_.append(j)

        users = meta.tables[cls.TABLE_NAME]
        conn = engine.connect()
        ins = users.insert()

        for u in users_:
            try:
                rst = conn.execute(ins, u)
            except:
                pass

    @classmethod
    def mk_dict(cls, row):
        return {
            "id": row["id"],
            "userid": row["userid"],
            "email": row["email"],
            "birth_year": row["birth_year"],
            "nickname": row["nickname"],
            "job": row["job"],
            "point": row["point"],
            "admin": row["admin"], 
            "expert": row["expert"],
            "create_at": GMT(row["create_at"]),
            "last_login": GMT(row["last_login"]),
            "active": row["active"],
            "disabled": row["disabled"],
            }

    @classmethod
    def mk_dict_classes(cls, row):
        d = {
            "id": row["id"],
            "userid": row["userid"],
            "email": row["email"],
            "birth_year": row["birth_year"],
            "nickname": row["nickname"],
            "job": row["job"],
            "point": row["point"],
            "admin": row["admin"], 
            "expert": row["expert"],
            "create_at": GMT(row["create_at"]),
            "last_login": GMT(row["last_login"]),
            "active": row["active"],
            "disabled": row["disabled"],
            }
        for c in row["class_access"]:
            d[c] = True
        return d

    @classmethod
    def mk_info(cls, row):
        return {
            "id": row["id"],
            "userid": row["userid"],
            "email": row["email"],
            "nickname": row["nickname"],
            "create_at": GMT(row["create_at"]),
            "disabled": row["disabled"],
            }

    def validate_json(self, json):
        if (not isinstance(json, dict)) or (json == {}):
            return httperror(400, ErrMsg.NOT_DICT)
        for attr, val in json.items():
            if hasattr(self, attr):
                self.__setattr__(attr, val)
            else:
                return httperror(400, ErrMsg.UNKNOWN_PARAM.format(attr))
        for col in User.user_t.columns:
            if (not col.nullable) and (not col.autoincrement):
                val = self.__getattribute__(col.name)
                if val == None:
                    return httperror(400, ErrMsg.MISS_PARAM.format(col.name))
                if isinstance(col.type, String):
                    val = val.strip("\t\n\r")
                    # regular expression
                    self.__setattr__(col.name, val)
                elif isinstance(col.type, Integer):
                    try:
                        val = int(self.__getattribute__(col.name))
                        self.__setattr__(col.name, val)
                    except:
                        return httperror(400, ErrMsg.NOT_INT.format(col.name))
            # elif col.nullable == True:
                # check nullable attributes

class Question(object):
    TABLE_NAME = "tb_question"
    question_t = None

    def __init__(self):
        self.title = None
        self.content = None
        self.type = None
        self.writer = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.question_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("title", String, nullable=False, autoincrement=False),
            Column("content", Text, nullable=False, autoincrement=False),
            Column("type", Integer, nullable=False, autoincrement=False),
            Column("solved", Boolean, default=False, nullable=True, autoincrement=True),
            Column("last_reply", DateTime, default=datetime.utcnow, autoincrement=True),
            Column("create_at", DateTime, default=datetime.utcnow, autoincrement=True),
            Column("writer", Integer, ForeignKey("tb_user.id"), nullable=False, autoincrement=False),
            Column("file1", String, nullable=True, autoincrement=False, default=""),
            Column("file2", String, nullable=True, autoincrement=False, default=""),
            Column("file3", String, nullable=True, autoincrement=False, default=""),
            )
        cls.question_t.create(db_engine, checkfirst=True)
        return cls.question_t

    @classmethod
    def mk_dict(cls, row):
        j = {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "type": row["type"],
            "solved": row["solved"],
            "last_reply": GMT(row["last_reply"]),
            "create_at": GMT(row["create_at"]),
            "writer_id": row["writer"],
            "file1": row["file1"],
            "file2": row["file2"],
            "file3": row["file3"],
            }
        return j

    @classmethod
    def mk_dict_user(cls, row):
        j = {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "type": row["type"],
            "solved": row["solved"],
            "last_reply": GMT(row["last_reply"]),
            "create_at": GMT(row["create_at"]),
            "writer_id": row["writer"],
            "file1": row["file1"],
            "file2": row["file2"],
            "file3": row["file3"],
            "writer": row["nickname"],
            }
        return j

    @classmethod
    def mk_info(cls, row):
        return {
            "id": row["id"],
            "title": row["title"],
            "type": row["type"],
            "solved": row["solved"],
            "last_reply": GMT(row["last_reply"]),
            "create_at": GMT(row["create_at"]),
            }


    def validate_json(self, json):
        if (not isinstance(json, dict)) or (json == {}):
            return httperror(400, ErrMsg.NOT_DICT)

        for attr, val in json.items():
            if hasattr(self, attr):
                self.__setattr__(attr, val)
            else:
                return httperror(400, ErrMsg.UNKNOWN_PARAM.format(attr))

        for col in Question.question_t.columns:
            if (not col.nullable) and (not col.autoincrement):
                val = self.__getattribute__(col.name)
                if val == None:
                    return httperror(400, ErrMsg.MISS_PARAM.format(col.name))
                if isinstance(col.type, String):
                    val = val.strip("\t\n\r")
                    self.__setattr__(col.name, val)
                elif isinstance(col.type, Integer):
                    try:
                        val = int(self.__getattribute__(col.name))
                        self.__setattr__(col.name, val)
                    except:
                        return httperror(400, ErrMsg.NOT_INT.format(col.name))

class Answer(object):
    TABLE_NAME = "tb_comment"
    answer_t = None

    def __init__(self):
        self.content = None
        self.writer = None
        self.answer_to = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.answer_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("content", Text, nullable=False, autoincrement=False),
            Column("writer", Integer, ForeignKey("tb_user.id"),
                nullable=False, autoincrement=False),
            Column("answer_to", Integer, ForeignKey("tb_question.id"),
                nullable=False, autoincrement=False),
            Column("create_at", DateTime, default=datetime.utcnow, autoincrement=True),
            Column("file1", String, nullable=True, autoincrement=False, default=""),
            Column("file2", String, nullable=True, autoincrement=False, default=""),
            Column("file3", String, nullable=True, autoincrement=False, default=""),
            )
        cls.answer_t.create(db_engine, checkfirst=True)
        return cls.answer_t

    @classmethod
    def mk_dict(cls, row):
        j = {
            "id": row["id"],
            "content": row["content"],
            "writer": row["writer"],
            "answer_to": row["answer_to"],
            "create_at": GMT(row["create_at"]),
            "file1": row["file1"],
            "file2": row["file2"],
            "file3": row["file3"],
            }
        return j

    def validate_json(self, json):
        if (not isinstance(json, dict)) or (json == {}):
            return httperror(400, ErrMsg.NOT_DICT)

        for attr, val in json.items():
            if hasattr(self, attr):
                self.__setattr__(attr, val)
            else:
                return httperror(400, ErrMsg.UNKNOWN_PARAM.format(attr))

        for col in Answer.answer_t.columns:
            if (not col.nullable) and (not col.autoincrement):
                val = self.__getattribute__(col.name)
                if val == None:
                    return httperror(400, ErrMsg.MISS_PARAM.format(col.name))
                if isinstance(col.type, String):
                    val = val.strip("\t\n\r")
                    self.__setattr__(col.name, val)
                elif isinstance(col.type, Integer):
                    try:
                        val = int(self.__getattribute__(col.name))
                        self.__setattr__(col.name, val)
                    except:
                        return httperror(400, ErrMsg.NOT_INT.format(col.name))

class Post(object):
    TABLE_NAME = "tb_post"
    post_t = None

    def __init__(self):
        self.title = None
        self.content = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.post_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("content", Text, nullable=False, autoincrement=False),
            Column("create_at", DateTime, default=datetime.utcnow, autoincrement=True),
            )
        cls.post_t.create(db_engine, checkfirst=True)
        return cls.post_t

    @classmethod
    def mk_dict(cls, row):
        return {
            "id": row["id"],
            # "title": row["title"],
            "content": row["content"],
            "create_at": GMT(row["create_at"]),
            }

class Opinion(object):
    TABLE_NAME = "tb_opinion"
    opinion_t = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.opinion_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("content", Text, nullable=False, autoincrement=False),
            Column("create_at", DateTime, default=datetime.utcnow, autoincrement=True),
            Column("writer", Integer, ForeignKey("tb_user.id"),
                nullable=False, autoincrement=False),
            )
        cls.opinion_t.create(db_engine, checkfirst=True)
        return cls.opinion_t

    @classmethod
    def mk_dict(cls, row):
        return {
            "id": row["id"],
            "content": row["content"],
            "writer": row["writer"],
            "create_at": GMT(row["create_at"]),
            }

class ClassManage(object):
    TABLE_NAME = "tb_classmanage"
    classmanage_t = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.classmanage_t = Table(cls.TABLE_NAME, db_meta,
            Column("uid", Integer, ForeignKey("tb_user.id"), nullable=False, autoincrement=False),
            Column("class_access", ARRAY(String), nullable=True, default=[], autoincrement=True),
            Column("class_record", JSON, nullable=True, default={}, autoincrement=True),
            )
        cls.classmanage_t.create(db_engine, checkfirst=True)
        return cls.classmanage_t

########################################
class Teacher(object):
    TABLE_NAME = "tb_teacher"
    teacher_t = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.teacher_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("userid", String, nullable=False, autoincrement=False, unique=True),
            Column("password", String, nullable=False, autoincrement=False),
            Column("name", String, nullable=False, autoincrement=False),
            Column("phone", String, nullable=False, autoincrement=False),
            Column("ext_area", Integer, nullable=True, autoincrement=True, default=0),
            Column("whole_city", Integer, nullable=True, autoincrement=True, default=0),
            Column("disabled", Boolean, default=False, nullable=True, autoincrement=True),
            Column("class_permission", ARRAY(String), nullable=False, autoincrement=False),
            Column("summary", Text, nullable=False, autoincrement=False),
            )
        cls.teacher_t.create(db_engine, checkfirst=True)
        return cls.teacher_t

    @classmethod
    def mk_dict(cls, row):
        return {
            "id": row["id"],
            "userid": row["userid"],
            "name": row["name"],
            "phone": row["phone"],
            "ext_area": row["ext_area"],
            "whole_city": row["whole_city"],
            "disabled": row["disabled"],
            "class_permission": row["class_permission"],
            "summary": row["summary"],
            }

    @classmethod
    def mk_dict_adarea_adclass(cls, row):
        enddate = row["enddate"]
        if enddate != None:
            enddate = row["enddate"].strftime("%Y 年 %m 月 %d 日")
        return {
            "id": row["id"],
            "name": row["name"],
            "phone": row["phone"],
            "summary": row["summary"],

            "city": row["city"],
            "town": row["town"],

            "adclassid": row["adclassid"],
            "address": row["address"],
            "type": row["type"],
            "date": row["date"].strftime("%Y 年 %m 月 %d 日"),
            "enddate": enddate,
            "start_time": row["start_time"].strftime("%I:%M %p"),
            "end_time": row["end_time"].strftime("%I:%M %p"),
            "weekdays": row["weekdays"],
            }

class Classroom(object):
    TABLE_NAME = "tb_classroom"
    classroom_t = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.classroom_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("name", String, nullable=False, autoincrement=False),
            Column("teacher", ForeignKey("tb_teacher.id"), nullable=False, autoincrement=False),
            Column("students_name", ARRAY(String), nullable=False, autoincrement=False),
            Column("students_cid", ARRAY(Integer), nullable=False, autoincrement=False),
            Column("students_sid", ARRAY(String), nullable=False, autoincrement=False),
            Column("folder", String, nullable=True, autoincrement=True, default=""),
            Column("comment", JSON, nullable=True, default={}, autoincrement=True),
            Column("create_at", DateTime, default=datetime.utcnow, autoincrement=True),
            Column("type", String, nullable=True, autoincrement=False),
            )
        cls.classroom_t.create(db_engine, checkfirst=True)
        return cls.classroom_t

    @classmethod
    def mk_dict(cls, row):
        if len(row["students_sid"]) == 0:
            students = dict(zip(row["students_cid"], row["students_name"]))
            return {
                "id": row["id"],
                "name": row["name"],
                "teacher": row["teacher"],
                "students": students,
                "create_at": GMT(row["create_at"]),
                "comment": row["comment"],
                "folder": row["folder"],
                "type": row["type"],
                }
        students = list(zip(row["students_name"], row["students_cid"], row["students_sid"]))
        return {
            "id": row["id"],
            "students": students,
            "teacher": row["teacher"],
            "comment": row["comment"],
            "name": row["name"],
            "create_at": GMT(row["create_at"]),
            "folder": row["folder"],
            "type": row["type"],
            }

    @classmethod
    def mk_info(cls, row, sid):
        if len(row["students_sid"]) == 0:
            return {
                "id": row["id"],
                "name": row["name"],
                "teacher": row["teacher"],
                "create_at": GMT(row["create_at"]),
                "folder": row["folder"],
                "type": row["type"],
                }
        students = dict(zip(row["students_cid"], row["students_sid"]))
        return {
            "id": row["id"],
            "name": row["name"],
            "teacher": row["teacher"],
            "student_cid": students[sid],
            "create_at": GMT(row["create_at"]),
            "folder": row["folder"],
            "type": row["type"],
            }


class AdArea(object):
    TABLE_NAME = "tb_adarea"
    advertise_t = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.advertise_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("teacher", ForeignKey("tb_teacher.id"), nullable=False, autoincrement=False),
            Column("city", Integer, nullable=False, autoincrement=False),
            Column("town", Integer, nullable=False, autoincrement=False),
            )
        cls.advertise_t.create(db_engine, checkfirst=True)
        return cls.advertise_t

    @classmethod
    def mk_dict(cls, row):
        return {
            "id": row["id"],
            "teacher": row["teacher"],
            "city": row["city"],
            "town": row["town"],
            }

class AdClass(object):
    TABLE_NAME = "tb_adclass"
    advertise_t = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.advertise_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("teacher", ForeignKey("tb_teacher.id"), nullable=False, autoincrement=False),
            Column("address", String, nullable=False, autoincrement=False),
            Column("type", String, nullable=False, autoincrement=False),
            Column("date", Date, nullable=False, autoincrement=False),
            Column("enddate", Date, nullable=False, autoincrement=False),
            Column("start_time", Time, nullable=False, autoincrement=False),
            Column("end_time", Time, nullable=False, autoincrement=False),
            Column("weekdays", ARRAY(Integer), nullable=False, autoincrement=False)
            )
        cls.advertise_t.create(db_engine, checkfirst=True)
        return cls.advertise_t

    @classmethod
    def mk_dict(cls, row):
        enddate = row["enddate"]
        if enddate != None:
            enddate = row["enddate"].strftime("%Y 年 %m 月 %d 日")
        return {
            "id": row["id"],
            "address": row["address"],
            "type": row["type"],
            "date": row["date"].strftime("%Y 年 %m 月 %d 日"),
            "enddate": enddate,
            "start_time": row["start_time"].strftime("%I:%M %p"),
            "end_time": row["end_time"].strftime("%I:%M %p"),
            "weekdays": row["weekdays"],
            }

class Activity(object):
    TABLE_NAME = "tb_activity"
    activity_t = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.activity_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("name", String, nullable=False, autoincrement=False),
            Column("repeat", Integer, nullable=False, autoincrement=False),
            Column("time", Time, nullable=False, autoincrement=False),
            Column("date", Date, nullable=True, autoincrement=False),
            Column("addr", String, nullable=False, autoincrement=False),
            Column("summary", Text, nullable=False, autoincrement=False),
            Column("present", ARRAY(Integer), nullable=True, autoincrement=True, default=[]),
            Column("participant", ARRAY(Integer), nullable=True, autoincrement=True, default=[]),
            Column("disabled", Boolean, default=False, nullable=True, autoincrement=True),
            Column("point", Integer, nullable=False, autoincrement=False),
            )
        cls.activity_t.create(db_engine, checkfirst=True)
        return cls.activity_t

    @classmethod
    def mk_info(cls, row):
        try:
            date = row["date"].strftime("%Y 年 %m 月 %d 日")
        except:
            date = ""
        return {
            "id": row["id"],
            "name": row["name"],
            "repeat": row["repeat"],
            "time": row["time"].strftime("%I:%M %p"),
            "date": date,
            "addr": row["addr"],
            "summary": row["summary"],
            "participant": row["participant"],
            }

    @classmethod
    def mk_dict(cls, row):
        try:
            date = row["date"].strftime("%Y 年 %m 月 %d 日")
        except:
            date = ""
        return {
            "id": row["id"],
            "name": row["name"],
            "repeat": row["repeat"],
            "time": row["time"].strftime("%I:%M %p"),
            "date": date,
            "addr": row["addr"],
            "summary": row["summary"],
            "participant": row["participant"],
            "present": row["present"],
            "disabled": row["disabled"],
            "point": row["point"],
            }

class Report(object):
    TABLE_NAME = "tb_report"
    report_t = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.report_t = Table(cls.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("title", String, nullable=False, autoincrement=False),
            Column("summary", Text, nullable=False, autoincrement=False),
            Column("file", String, nullable=True, autoincrement=False),
            Column("writer", Integer, ForeignKey("tb_user.id"),
                nullable=False, autoincrement=False),
            Column("status", Integer, nullable=True, default=0, autoincrement=True),
            Column("create_at", DateTime, default=datetime.utcnow, autoincrement=True),
            Column("reply", Text, nullable=True, default="", autoincrement=True),
            )
        cls.report_t.create(db_engine, checkfirst=True)
        return cls.report_t

    @classmethod
    def mk_dict(cls, row):
        return {
            "id": row["id"],
            "title": row["title"],
            "summary": row["summary"],
            "file": row["file"],
            "writer": row["writer"],
            "nickname": row["nickname"],
            "status": row["status"],
            "create_at": GMT(row["create_at"]),
            "reply": row["reply"],
            }

