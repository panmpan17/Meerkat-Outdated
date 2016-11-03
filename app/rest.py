import cherrypy
import logging, logging.config
from app.model import ErrMsg, User, Question, Answer, Post, Opinion
from uuid import uuid1 as uuid
from datetime import datetime
from requests import get as http_get

from sqlalchemy import desc
from sqlalchemy.sql import select, update, and_
from sqlalchemy.exc import IntegrityError

class ErrMsg(ErrMsg):
    NOT_LIST = "'{}' must be a list"
    NOT_BOOL = "'{}' must be Boolen"
    UNKNOWN_ID = "Id '{}' is not found"
    WRONG_PASSWORD = "Username or password wrong"
    USERID_REPEAT = "This userid repeat"
    WRONG_CLASS = "Class '{}' not exist"
    WRONG_WRITER = "Question's writer id is not '{}'"
    A_WRONG_WRITER = "Answer's writer id is not '{}'"
    SOLVED_QUESTION = "Question '{}' alredy solved"
    NEED_ADMIN = "User '{}' is not admin"
    NOT_HUMAN = "You are not human"

RECAPTCHA_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_SERCRET = "6LcSMwoUAAAAAEIO6z5s2FO4QNjz0pZqeD0mZqRZ"

rest_config = {
    "url_root":"/rest/1/",
    "db_connstr":"sqlite:///db",
    }

def count_page(r):
    # print(r)
    if (r % 10) == 0:
        return (r // 10)
    return (r // 10) + 1

class SessionKeyView(object):
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
        }
    _root = rest_config["url_root"] + "logon/"

    def __init__(self):
        self.key_log = logging.getLogger("key")

    @cherrypy.expose
    def index(self, *args, **kwargs):
        key_mgr = cherrypy.request.key
        if cherrypy.request.method == "POST":
            data = cherrypy.request.json
            if len(data) > 0:
                if ("userid" in data) and ("password" in data):
                    meta, conn = cherrypy.request.db
                    users = meta.tables[User.TABLE_NAME]
                    ss = select([users.c.id]).where(and_(users.c.userid == data["userid"],
                        users.c.password == data["password"]))
                    rst = conn.execute(ss)
                    rows = rst.fetchall()

                    if len(rows) <= 0:
                        raise cherrypy.HTTPError(400, ErrMsg.WRONG_PASSWORD)
                    else:
                        # create session key and return it
                        key = str(uuid())
                        key_mgr.update_key(key, rows[0]["id"])

                        return {"key":key, "lastrowid": rows[0]["id"], "userid": data["userid"]}

                else:
                    raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("userid or password"))
            else:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("userid or password"))
        else:
            raise cherrypy.HTTPError(404)

class UserRestView(object):
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
        }
    _root = rest_config["url_root"] + "user/"

    def __init__(self):
        self.app_logger = logging.getLogger("app")
        self.db_logger = logging.getLogger("db")
        self.error_logger = logging.getLogger("error")
        self.key_log = logging.getLogger("key")

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        users = meta.tables[User.TABLE_NAME]
        # no param than get all
        if cherrypy.request.method == "GET":

            if len(kwargs) > 0:
                if "key" not in kwargs:
                    raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("key"))
                    # check session key

                key_valid = key_mgr.get_key(kwargs["key"])
                if not key_valid[0]:
                    self.key_log.debug(key_valid)
                    raise cherrypy.HTTPError(401)
                
                if "id" in kwargs:
                    try:
                        uid = int(kwargs["id"])
                    except:
                        raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format(kwargs["id"]))

                    ss = select([users]).where(users.c.id == uid)
                    rst = conn.execute(ss)
                    rows = rst.fetchall()
                    if len(rows) <= 0:
                        raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(uid))

                    # update
                    if uid == key_valid[1]:
                        return User.mk_dict(rows[0])
                    else:
                        return User.mk_info(rows[0])
                else:
                    ss = select([users.c.admin]).where(users.c.id == key_valid[1])
                    rst = conn.execute(ss)
                    rows = rst.fetchall()
                    if len(rows) < 1:
                        raise cherrypy.HTTPError(401, ErrMsg.NEED_ADMIN.format(key_valid[1]))
                    if not rows[0]:
                        raise cherrypy.HTTPError(401, ErrMsg.NEED_ADMIN.format(key_valid[1]))

                    ss = select([users])
                    rst = conn.execute(ss)
                    rows = rst.fetchall()

                    return [User.mk_dict(u) for u in rows]
  
            else:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("key"))

        # create user
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            if len(args) > 0:
                raise cherrypy.HTTPError(404)
            else:
                if "recapcha" not in data.keys():
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_HUMAN)

                r = http_get(RECAPTCHA_URL, params={"secret": RECAPTCHA_SERCRET, "response": data["recapcha"]})
                if not r.json()["success"]:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_HUMAN)

                # check create user json
                if "users" not in data.keys():
                    raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("users"))
                usersjson = data["users"]
                if not isinstance(usersjson, list) or len(usersjson) <= 0:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_LIST.format("users"))

                for user in usersjson:
                    u = User()
                    result = u.validate_json(user)
                    if isinstance(result, Exception):
                        raise(result)
                
                ins = users.insert()
                try:
                    rst = conn.execute(ins, usersjson)
                except IntegrityError:
                    raise cherrypy.HTTPError(400, ErrMsg.USERID_REPEAT)

                if rst.is_insert:
                    cherrypy.response.status = 201
                    key = str(uuid())
                    key_mgr.update_key(key, rst.lastrowid)
                    return {"key": key, "lastrowid": rst.lastrowid,
                        "userid": usersjson[-1]["userid"]}
                else:
                    raise cherrypy.HTTPError(503) 

        #  update user attributes
        elif cherrypy.request.method == "PUT":
            return {"update_user":True}

        else:
            raise cherrypy.HTTPError(404)

class QuestionRestView(object):
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
        }
    _root = rest_config["url_root"] + "question/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        questions = meta.tables[Question.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if "id" in kwargs:
                try:
                    qid = int(kwargs["id"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format(kwargs["id"]))

                ss = select([questions]).where(questions.c.id == qid)
                rst = conn.execute(ss)
                rows = rst.fetchall()
                if len(rows) < 1:
                    raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(qid))

                result = Question.mk_dict(rows[0])

                ss = select([users.c.nickname]).where(users.c.id == rows[0]["writer"])
                rst = conn.execute(ss)
                rows = rst.fetchall()
                if len(rows) < 1:
                    result["writer"] = ""
                    # TODO: if writer don't exist, then delete question
                else:
                    result["writer"] = rows[0]["nickname"]

                return result

            ss = None
            if "writer" in kwargs:
                try:
                    uid = int(kwargs["writer"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format(kwargs["writer"]))


                ss = select([questions]).where(questions.c.writer == uid)
            elif "solved" in kwargs:
                solved = False
                if (kwargs["solved"] != "True") and (kwargs["solved"] != "False"):
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_BOOL.format(kwargs["solved"]))
                elif kwargs["solved"] == "True":
                    solved = True


                ss = select([questions]).where(questions.c.solved == solved)
            elif "type" in kwargs:
                try:
                    type_ = int(kwargs["type"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("type"))

                ss = select([questions]).where(questions.c.type == type_)
            elif "answer" in kwargs:
                answers = meta.tables[Answer.TABLE_NAME]
                try:
                    uid = int(kwargs["answer"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format(kwargs["answer"]))

                ss = select([answers.c.answer_to]).where(answers.c.writer == uid)\
                    .order_by(desc(answers.c.create_at))
                rst = conn.execute(ss)
                rows = rst.fetchall()
                if len(rows) <= 0:
                    raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(uid))

                qids = {i[0] for i in rows}
                
                ss = select([questions]).where(questions.c.id.in_(qids))
            else:
                ss = select([questions])
                
            try:
                page = int(kwargs["page"])
            except:
                page = 0

            ss = ss.order_by(desc(questions.c.create_at))
            rst = conn.execute(ss)
            rows = rst.fetchall()
            if (len(rows) / 10) < page:
                page = 0

            page *= 10

            try:
                question_l = rows[page:page + 10]
            except:
                # print(2)
                question_l = rows[page:-1]

            question_l = [Question.mk_info(row) for row in question_l]
            return {"questions":question_l, "pages":count_page(len(rows))}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            if len(args) > 0:
                raise cherrypy.HTTPError(404)

            #check session key
            if "key" not in data.keys():
               raise cherrypy.HTTPError(401)

            key_valid = key_mgr.get_key(data["key"])
            if not key_valid[0]:
               raise cherrypy.HTTPError(401)
            key = data["key"]


            if "question_json" not in data.keys():
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("question_json"))
            question_json = data["question_json"]
            if not isinstance(question_json, dict):
                raise cherrypy.HTTPError(400, ErrMsg.NOT_DICT)
            
            q = Question()
            result = q.validate_json(question_json)
            if isinstance(result, Exception):
                raise (result)

            # check user id exist
            ss = select([users.c.id]).where(users.c.id == int(question_json["writer"]))
            rst = conn.execute(ss)
            rows = rst.fetchall()
            if len(rows) <= 0:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(question_json["writer"]))

            ins = questions.insert()
            rst = conn.execute(ins, question_json)

            if rst.is_insert:
                cherrypy.response.status = 201
                
                ss = select([questions.c.id]).order_by(desc(questions.c.id))
                row = conn.execute(ss)

                return {"question_id": row.first()["id"]}
            else:
                raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            if len(args) > 0:
                raise cherrypy.HTTPError(404)

            if "solved" in data:
                if "key" not in data.keys():
                    raise cherrypy.HTTPError(401)

                key_valid = key_mgr.get_key(data["key"])
                if not key_valid[0]:
                    raise cherrypy.HTTPError(401)
                uid = key_valid[1]

                try:
                    qid = int(data["qid"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

                solved = False
                if (data["solved"] != "True") and (data["solved"] != "False"):
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_BOOL.format(data["solved"]))
                elif data["solved"] == "True":
                    solved = True

                stmt = update(questions).where(and_(questions.c.id == qid,
                    questions.c.writer == uid)).values({"solved": solved})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("solved"))
        elif cherrypy.request.method == "DELETE":
            if "key" not in kwargs:
               raise cherrypy.HTTPError(401)

            key_valid = key_mgr.get_key(kwargs["key"])
            if not key_valid[0]:
               raise cherrypy.HTTPError(401)
            uid = key_valid[1]

            ss = select([users.c.admin]).where(and_(users.c.id == key_valid[1],
                users.c.admin == True))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) < 1:
                raise cherrypy.HTTPError(401)

            answers = meta.tables[Answer.TABLE_NAME]
            
            if "id" not in kwargs:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("id"))

            # delete answer
            ds = answers.delete().where(answers.c.answer_to == kwargs["id"])
            rst = conn.execute(ds)

            # delete question
            ds = questions.delete().where(questions.c.id == kwargs["id"])
            rst = conn.execute(ds)

            return {"delete": True}
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def fileattach(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        questions = meta.tables[Question.TABLE_NAME]

        if cherrypy.request.method == "POST":
            data = cherrypy.request.json
            if len(args) > 0:
                raise cherrypy.HTTPError(404)

            # check session key
            if "key" not in data.keys():
                raise cherrypy.HTTPError(401)

            key_valid = key_mgr.get_key(data["key"])
            if not key_valid[0]:
                raise cherrypy.HTTPError(401)
            uid = key_valid[1]

            if ("qid" not in data) or ("filepath" not in data):
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("qid ot filepath"))
            try:
                qid = int(data["qid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

            file_path = data["filepath"]
            if not isinstance(file_path, list):
                raise cherrypy.HTTPError(400, ErrMsg.NOT_LIST.format("filepath"))
            if len(file_path) == 0:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_LIST.format("filepath"))

            # check is same writer
            # ss = select([questions]).where(and_(questions.c.id == qid, questions.c.writer == uid))
            # rst = conn.execute(ss)
            # rows = rst.fetchall()
            # if len(rows) <= 0:
            #     # if this happend the file upload will be delete
            #     raise cherrypy.HTTPError(400, ErrMsg.WRONG_WRITER.format(str(uid)))

            # TODO: if file already exist then the file upload THIS TIME will be delete

            # TODO: check file exist
            file_string = ("file1", "file2", "file3")
            a = dict(zip(file_string, data["filepath"]))

            stmt = update(questions).where(and_(questions.c.id == qid, questions.c.writer == uid)).values(a)
            ins = conn.execute(stmt)

            if ins.rowcount == 0:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_WRITER.format(str(uid)))
            else:
                cherrypy.response.status = 201
                return a

        else:
            raise cherrypy.HTTPError(404)

class AnswerRestView(object):
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
        }
    _root = rest_config["url_root"] + "answer/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        questions = meta.tables[Question.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]
        answers = meta.tables[Answer.TABLE_NAME]

        if cherrypy.request.method == "GET":
            data = kwargs
            if len(args) > 0:
                raise HTTPError(404)

            if "qid" in data:
                try:
                    qid = int(data["qid"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

                ss = select([answers]).where(answers.c.answer_to == qid)\
                    .order_by(desc(answers.c.create_at))
                rst = conn.execute(ss)
                rows = rst.fetchall()
                if len(rows) <= 0:
                    raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(qid))

                answers = []
                user_nickname = {}
                for row in rows:
                    d = Answer.mk_dict(row)

                    if d["writer"] in user_nickname:
                        d["writer"] = user_nickname[d["writer"]]
                    else:
                        ss = select([users.c.nickname]).where(users.c.id == row["writer"])
                        rst = conn.execute(ss)
                        urows = rst.fetchall()
                        if len(urows) < 1:
                            user_nickname[d["writer"]] = ""
                        else:
                            user_nickname[d["writer"]] = urows[0]["nickname"]

                        d["writer"] = user_nickname[d["writer"]]

                    answers.append(d)

                return {"answers": answers}

            else:
                raise cherrypy.HTTPError(400, ErrMsg,MISS_PARAM.format("qid"))

        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            if len(args) > 0:
                raise HTTPError(404)

            # check session key
            if "key" not in data.keys():
                raise cherrypy.HTTPError(401)

            key_valid = key_mgr.get_key(data["key"])
            if not key_valid[0]:
                raise cherrypy.HTTPError(401)
            key = data["key"]

            if "answer_json" not in data.keys():
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("answer_json"))
            answer_json = data["answer_json"]
            if not isinstance(answer_json, dict):
                raise cherrypy.HTTPError(400, ErrMsg.NOT_DICT)
            
            a = Answer()
            result = a.validate_json(answer_json)
            if isinstance(result, Exception):
                raise (result)

            ss = select([users.c.id]).where(users.c.id == int(answer_json["writer"]))
            rst = conn.execute(ss)
            rows = rst.fetchall()
            if len(rows) <= 0:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(answer_json["writer"]))

            ss = select([questions.c.solved]).where(questions.c.id == int(answer_json["answer_to"]))
            rst = conn.execute(ss)
            rows = rst.fetchall()
            if len(rows) <= 0:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(answer_json["answer_to"]))
            if rows[0]["solved"] == True:
                raise cherrypy.HTTPError(400, ErrMsg.SOLVED_QUESTION\
                    .format(answer_json["answer_to"]))

            ins = answers.insert()
            rst = conn.execute(ins, answer_json)

            if rst.is_insert:
                ss = select([answers.c.id]).order_by(desc(answers.c.id))
                row = conn.execute(ss)

                cherrypy.response.status = 201
                # key_mgr.update_key(key, data["answer_json"]["writer"])
                return {"answer_id": row.first()["id"]}
            else:
                raise cherrypy.HTTPError(503)

        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def fileattach(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        answers = meta.tables[Answer.TABLE_NAME]

        if cherrypy.request.method == "POST":
            data = cherrypy.request.json
            if len(args) > 0:
                raise cherrypy.HTTPError(404)

            # check session key
            if "key" not in data.keys():
                raise cherrypy.HTTPError(401)

            key_valid = key_mgr.get_key(data["key"])
            if not key_valid[0]:
                raise cherrypy.HTTPError(401)
            uid = key_valid[1]

            if ("aid" not in data) or ("filepath" not in data):
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("aid ot filepath"))
            try:
                aid = int(data["aid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("aid"))

            file_path = data["filepath"]
            if not isinstance(file_path, list):
                raise cherrypy.HTTPError(400, ErrMsg.NOT_LIST.format("filepath"))
            if len(file_path) == 0:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_LIST.format("filepath"))

            # check is same writer
            # ss = select([questions]).where(and_(questions.c.id == qid, questions.c.writer == uid))
            # rst = conn.execute(ss)
            # rows = rst.fetchall()
            # if len(rows) <= 0:
            #     # if this happend the file upload will be delete
            #     raise cherrypy.HTTPError(400, ErrMsg.WRONG_WRITER.format(str(uid)))

            # TODO: if file already exist then the file upload THIS TIME will be delete

            # TODO: check file exist
            file_string = ("file1", "file2", "file3")
            a = dict(zip(file_string, data["filepath"]))

            stmt = update(answers).where(and_(answers.c.id == aid, answers.c.writer == uid)).values(a)
            ins = conn.execute(stmt)

            if ins.rowcount == 0:
                raise cherrypy.HTTPError(400, ErrMsg.A_WRONG_WRITER.format(str(uid)))
            else:
                cherrypy.response.status = 201
                return a

        else:
            raise cherrypy.HTTPError(404)

class ClassesRestView(object):
    _cp_config = {
        "tools.classestool.on": True,
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
    }
    _root = rest_config["url_root"] + "classes/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        classes = cherrypy.request.classes

        if cherrypy.request.method == "GET":
            if len(kwargs) > 0:
                if "class" not in kwargs:
                    raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("class"))

                class_ = classes.get_class(kwargs["class"])

                if not class_:
                    raise cherrypy.HTTPError(400, ErrMsg.WRONG_CLASS.format(kwargs["class"]))

                # if class_["price"] == 0:
                return class_
                # else:
                #     return "Error"
  
            else:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("class"))

        else:
            raise cherrypy.HTTPError(404)

class PostRestView(object):
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
        }
    _root = rest_config["url_root"] + "post/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        posts = meta.tables[Post.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]
        if cherrypy.request.method == "GET":
            ss = select([posts]).order_by(desc(posts.c.create_at))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            return {"posts": [Post.mk_dict(row) for row in rows]}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json

            if len(args) > 0:
                raise cherrypy.HTTPError(404)

            if "key" not in data.keys():
               raise cherrypy.HTTPError(401)

            key_valid = key_mgr.get_key(data["key"])
            if not key_valid[0]:
               raise cherrypy.HTTPError(401)
            uid = key_valid[1]

            ss = select([users.c.admin]).where(and_(users.c.id == key_valid[1],
                users.c.admin == True))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) < 1:
                raise cherrypy.HTTPError(401)

            if ("content" not in data):
                raise cherrypy.HTTPError(400)

            j = {
                "content": PostRestView.turn_url(data["content"]),
                }

            posts = meta.tables[Post.TABLE_NAME]
            ins = posts.insert()
            rst = conn.execute(ins, j)

            if rst.is_insert:
                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(500)
        elif cherrypy.request.method == "DELETE":
            # check admin
            if "key" not in kwargs:
               raise cherrypy.HTTPError(401)

            key_valid = key_mgr.get_key(kwargs["key"])
            if not key_valid[0]:
               raise cherrypy.HTTPError(401)
            uid = key_valid[1]

            ss = select([users.c.admin]).where(and_(users.c.id == key_valid[1],
                users.c.admin == True))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) < 1:
                raise cherrypy.HTTPError(401)

            if "id" not in kwargs:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM("id"))

            # delete post
            ds = posts.delete().where(posts.c.id == kwargs["id"])
            rst = conn.execute(ds)

            return {"delete": True}
        else:
            raise cherrypy.HTTPError(404)

    @classmethod
    def turn_url(cls, string):
        t_s_s = string.find("[#")
        while t_s_s > -1:
            t_s_e = string.find("#]", t_s_s + 2)
            t_l_e = string.find("#}", t_s_e + 2)
            if (t_s_e == -1) or (t_l_e == -1):
                break

            text = string[t_s_s + 2:t_s_e]
            url = string[t_s_e + 2: t_l_e].replace(" ", "")

            link = AdminHandler.link_fmt.format(url=url[2:], string=text)
            if link == "<a href=\"\"></a>":
                t_s_s = string.find("[#", t_l_e + 2)
                continue


            string = string.replace(string[t_s_s:t_l_e+2], link)

            t_s_s = string.find("[#", t_l_e + 2)
        return string

class OpinionRestView(object):
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
        }
    _root = rest_config["url_root"] + "opinion/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        opinions = meta.tables[Opinion.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            ss = select([opinions]).order_by(desc(opinions.c.create_at))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            return [Opinion.mk_dict(i) for i in rows]
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            key_mgr = cherrypy.request.key
            if len(args) > 0:
                raise cherrypy.HTTPError(404)

            if "key" not in data.keys():
               raise cherrypy.HTTPError(401)

            key_valid = key_mgr.get_key(data["key"])
            if not key_valid[0]:
               raise cherrypy.HTTPError(401)
            uid = key_valid[1]

            if "content" not in data.keys():
                raise HTTPError.HTTPError(400, ErrMsg.MISS_PARAM.format("content"))

            ss = select([users.c.id]).where(users.c.id == uid)
            rst = conn.execute(ss)
            rows = rst.fetchall()
            if len(rows) <= 0:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(question_json["writer"]))

            ins = opinions.insert()
            rst = conn.execute(ins, {"writer":uid, "content":data["content"]})

            if rst.is_insert:
                cherrypy.response.status = 201
                
                ss = select([opinions.c.id]).order_by(desc(opinions.c.id))
                row = conn.execute(ss)

                return {"opinions_id": row.first()["id"]}
            else:
                raise cherrypy.HTTPError(503)

        else:
            raise cherrypy.HTTPError(404)







