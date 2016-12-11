from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy import Boolean, DateTime, Text, ARRAY, JSON
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
    fmt = '%Y.%m.%d %H:%M'
    return t.strftime(fmt)

def hash(v):
    return sha256(v.encode()).hexdigest()

class ErrMsg:
    NOT_DICT = "Must be a dictionary"
    UNKNOWN_PARAM = "Unknown parameter '{}'"
    MISS_PARAM = "The '{}' is missing."
    NOT_INT = "'{}' must be a integer"
    CANT_INPUT = "This param is autoincrement '{}'"

class Base(object):
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

class User(Base):
    TABLE_NAME = "tb_user"
    user_t = None

    def __init__(self):
        # require attributesf
        self.userid = None
        self.password = None
        self.email = None
        self.birth_year = None
        self.nickname = None
        # nullable attributes
        self.job = ""

    @classmethod
    def create_schema(cls, db_engine, db_meta, euf=None):
        cls.user_t = Table(User.TABLE_NAME, db_meta,
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
            Column("last_login", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, autoincrement=True),
            # Column("disabled", Boolean, default=False, nullable=True, autoincrement=True)
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

        users = meta.tables[User.TABLE_NAME]
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
            }

class Question(Base):
    TABLE_NAME = "tb_question"
    question_t = None

    def __init__(self):
        self.title = None
        self.content = None
        self.type = None
        self.writer = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.question_t = Table(Question.TABLE_NAME, db_meta,
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
        if j["file1"] != "":
            if not os.path.isfile(j["file1"]):
                j["file1"] = "檔案不存在"
        if j["file2"] != "":
            if not os.path.isfile(j["file2"]):
                j["file2"] = "檔案不存在"
        if j["file3"] != "":
            if not os.path.isfile(j["file3"]):
                j["file3"] = "檔案不存在"
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

class Answer(Base):
    TABLE_NAME = "tb_comment"
    answer_t = None

    def __init__(self):
        self.content = None
        self.writer = None
        self.answer_to = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.answer_t = Table(Answer.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("content", Text, nullable=False, autoincrement=False),
            Column("writer", Integer, ForeignKey("tb_user.id"), nullable=False, autoincrement=False),
            Column("answer_to", Integer, ForeignKey("tb_question.id"), nullable=False, autoincrement=False),
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
        if j["file1"] != "":
            if not os.path.isfile(j["file1"]):
                j["file1"] = "檔案不存在"
        if j["file2"] != "":
            if not os.path.isfile(j["file2"]):
                j["file2"] = "檔案不存在"
        if j["file3"] != "":
            if not os.path.isfile(j["file3"]):
                j["file3"] = "檔案不存在"
        return j

class Post(Base):
    TABLE_NAME = "tb_post"
    post_t = None

    def __init__(self):
        self.content = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.post_t = Table(Post.TABLE_NAME, db_meta,
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

class Opinion(Base):
    TABLE_NAME = "tb_opinion"
    opinion_t = None

    def __init__(self):
        self.content = None
        self.writer = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.opinion_t = Table(Opinion.TABLE_NAME, db_meta,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("content", Text, nullable=False, autoincrement=False),
            Column("create_at", DateTime, default=datetime.utcnow, autoincrement=True),
            Column("writer", Integer, ForeignKey("tb_user.id"), nullable=False, autoincrement=False),
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

class ClassManage(Base):
    TABLE_NAME = "tb_classmanage"
    classmanage_t = None

    def __init__(self):
        self.uid = None

    @classmethod
    def create_schema(cls, db_engine, db_meta):
        cls.classmanage_t = Table(ClassManage.TABLE_NAME, db_meta,
            Column("uid", Integer, ForeignKey("tb_user.id"), nullable=False, autoincrement=False),
            Column("class_access", ARRAY(String), nullable=True, default=[], autoincrement=True),
            Column("class_record", JSON, nullable=True, default={}, autoincrement=True)
            )
        cls.classmanage_t.create(db_engine, checkfirst=True)
        return cls.classmanage_t


