import cherrypy
import logging, logging.config
from app.model import ErrMsg, User, Question, Answer, Post, Opinion, ClassManage
from uuid import uuid1 as uuid
from datetime import datetime
from requests import get as http_get
from requests import post as http_post

from sqlalchemy import desc
from sqlalchemy.sql import select, update, and_, join
from sqlalchemy.exc import IntegrityError


EMAIL_REST_URL = "http://restemailserver.appspot.com"
RECAPTCHA_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_SERCRET = "6LcSMwoUAAAAAEIO6z5s2FO4QNjz0pZqeD0mZqRZ"

EMAIL_VALID = """
<html><head>
<style>
div \{
font-size: 24px;
}
div#c4f \{
top: 0px;
left: 0px;
position: absolute;
width:100%;
font-size:36px;
color: white;
background-color:rgb(43,142,183);}
button \{
width:300px;
height:  100px;
font-size: 24px;
color: white;
background-color:rgb(43,142,183);
border: 0px;}
button:hover \{
background-color: rgb(30,105,138);
}</style></head><body>
<center>
<div id="c4f">Codinf For Fun  Email 認證</div><br /><br /><br />
<div>
按下面的按鈕, 來啟動你的帳戶: <br /><br />
<a href="url"><button>啟動我的帳戶</button></a><br /><br />
或使用以下網址:<br><a href="url">url</a></div></body></center></html>
"""

rest_config = {
    "url_root":"/rest/1/",
    "db_connstr":"postgresql://cd4fun_u:mlmlml@localhost:5432/coding4fun_db?client_encoding=utf8",
    }

def count_page(r):
    if (r % 10) == 0:
        return (r // 10)
    return (r // 10) + 1

def send_email_valid(key, addr):
    url = cherrypy.url() + "/active/" + key
    cnt = EMAIL_VALID.replace("url", key)
    http_post(EMAIL_REST_URL, params={"addr": addr, "sub": "Email 認證", "cnt": cnt})

class ErrMsg(ErrMsg):
    NOT_LIST = "'{}' must be a list"
    NOT_BOOL = "'{}' must be Boolen"

    UNKNOWN_ID = "Id '{}' is not found"
    WRONG_PASSWORD = "Username or password wrong"

    USERID_REPEAT = "This userid repeat"
    NOT_HUMAN = "You are not human"

    WRONG_WRITER = "Question's writer id is not '{}'"
    A_WRONG_WRITER = "Answer's writer id is not '{}'"
    SOLVED_QUESTION = "Question '{}' alredy solved"

    NEED_ADMIN = "User '{}' is not admin"

    WRONG_CLASS = "Class '{}' not exist"
    NO_ACCESS_TO_CLASS = "You have permission to watch the class '{}'"
    WRONG_VIDEO = "Videl '{}' is not in any class"

class View(object):
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
        }

    def check_login(self, json, key_mgr):
        if "key" not in json:
            return False

        key_valid = key_mgr.get_key(json["key"])
        if not key_valid[0]:
           return False
        return key_valid[1]

    def check_admin(self, uid, users, conn):
        ss = select([users.c.admin]).where(and_(users.c.id == uid,
                users.c.admin == True))
        rst = conn.execute(ss)
        rows = rst.fetchall()
        if len(rows) < 1:
            return False
        return True

    @staticmethod
    def check_key(_dict, keys):
        for key in keys:
            if key not in _dict:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format(key))

class SessionKeyView(View):
    _root = rest_config["url_root"] + "logon/"

    def __init__(self):
        self.key_log = logging.getLogger("key")

    @cherrypy.expose
    def index(self, *args, **kwargs):
        key_mgr = cherrypy.request.key
        if cherrypy.request.method == "GET":
            View.check_key(kwargs, ("userid", "password"))

            meta, conn = cherrypy.request.db
            users = meta.tables[User.TABLE_NAME]
            ss = select([users.c.id]).where(and_(users.c.userid == kwargs["userid"],
                users.c.password == kwargs["password"]))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) <= 0:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_PASSWORD)
            else:
                # create session key and return it
                key = str(uuid())
                key_mgr.update_key(key, rows[0]["id"])

                return {"key":key, "lastrowid": rows[0]["id"], "userid": kwargs["userid"]}
        else:
            raise cherrypy.HTTPError(404)

class UserRestView(View):
    _root = rest_config["url_root"] + "user/"
    _cp_config = View._cp_config
    _cp_config["tools.emailvalidtool.on"] = True

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
                    classmanages = meta.tables[ClassManage.TABLE_NAME]
                    try:
                        uid = int(kwargs["id"])
                    except:
                        raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format(kwargs["id"]))

                    j = join(users, classmanages)
                    ss = select([users, classmanages.c.class_access]).where(users.c.id == uid).select_from(j)
                    rst = conn.execute(ss)
                    rows = rst.fetchall()
                    if len(rows) <= 0:
                        ss = select([users]).where(users.c.id == uid)
                        rst = conn.execute(ss)
                        rows = rst.fetchall()
                        if len(rows) > 0:
                            ins = classmanages.insert()
                            rst = conn.execute(ins, dict(uid=uid))
                        else:
                            raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(uid))

                    # update
                    if uid == key_valid[1]:
                        return User.mk_dict_classes(rows[0])

                    admin = self.check_admin(key_valid[1], users, conn)
                    if admin:
                        return User.mk_dict_classes(rows[0])
                    return User.mk_info(row[0])
                else:
                    admin = self.check_admin(key_valid[1], users, conn)
                    if not admin:
                        raise cherrypy.HTTPError(401)

                    ss = select([users])

                    if "userid" in kwargs:
                        ss = ss.where(users.c.userid.like(kwargs["userid"] + "%"))

                    rst = conn.execute(ss)
                    rows = rst.fetchall()

                    return [User.mk_info(u) for u in rows]
  
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
                    uid = rst.lastrowid
                    key_mgr.update_key(key, rst.lastrowid)

                    # key = cherrypy.request.email_valid.new_mail(uid)
                    # send_email_valid(key, usersjson[0]["email"])

                    return {"key": key, "lastrowid": rst.lastrowid,
                        "userid": usersjson[-1]["userid"]}
                else:
                    raise cherrypy.HTTPError(503) 

        #  update user attributes
        elif cherrypy.request.method == "PUT":
            return {"update_user":True}

        else:
            raise cherrypy.HTTPError(404)

class QuestionRestView(View):
    _root = rest_config["url_root"] + "question/"
    _cp_config = View._cp_config

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

            if "type" in kwargs:
                try:
                    type_ = int(kwargs["type"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("type"))

                ss = ss.where(questions.c.type == type_)
                
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

            uid = self.check_login(data, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

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

                qid = row.first()["id"]
                title = "新問題: " + data["question_json"]["title"]
                content = data["question_json"]["content"]


                http_post(EMAIL_REST_URL,
                    params={"addr":"panmpan@gmail.com", "sub": title, "cnt": content})
                http_post(EMAIL_REST_URL,
                    params={"addr":"shalley.tsay@gmail.com", "sub": title, "cnt": content})

                return {"question_id": qid}
            else:
                raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            if len(args) > 0:
                raise cherrypy.HTTPError(404)

            if "solved" in data:
                uid = self.check_login(data, key_mgr)
                if not uid:
                    raise cherrypy.HTTPError(401)

                try:
                    qid = int(data["qid"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

                solved = False
                if (data["solved"] != "True") and (data["solved"] != "False"):
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_BOOL.format(data["solved"]))
                elif data["solved"] == "True":
                    solved = True

                admin = self.check_admin(uid, users, conn)
                if admin:
                    stmt = update(questions).where(questions.c.id == qid).values({"solved": solved})
                    ins = conn.execute(stmt)

                    cherrypy.response.status = 201
                    return {"success": True}

                stmt = update(questions).where(and_(questions.c.id == qid,
                    questions.c.writer == uid)).values({"solved": solved})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            elif "type" in data:
                uid = self.check_login(data, key_mgr)
                if not uid:
                    raise cherrypy.HTTPError(401)

                try:
                    qid = int(data["qid"])
                except:
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

                type_ = data["type"]

                admin = self.check_admin(uid, users, conn)
                if admin:
                    stmt = update(questions).where(questions.c.id == qid).values({"type": type_})
                    ins = conn.execute(stmt)

                    cherrypy.response.status = 201
                    return {"success": True}

                stmt = update(questions).where(and_(questions.c.id == qid,
                    questions.c.writer == uid)).values({"type": type_})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("solved"))
        elif cherrypy.request.method == "DELETE":
            uid = self.check_login(kwargs, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

            admin = self.check_admin(uid, users, conn)
            if not admin:
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

            uid = self.check_login(data, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

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

class AnswerRestView(View):
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

            uid = self.check_login(data, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

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

            uid = self.check_login(data, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

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

class ClassesRestView(View):
    _cp_config = View._cp_config
    _cp_config["tools.classestool.on"] = True
    _root = rest_config["url_root"] + "classes/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        classes = cherrypy.request.classes
        key_mgr = cherrypy.request.key
        meta, conn = cherrypy.request.db
        classmanages = meta.tables[ClassManage.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if len(kwargs) > 0:
                if "class" not in kwargs:
                    raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("class"))

                class_ = classes.get_class(kwargs["class"])

                if not class_:
                    raise cherrypy.HTTPError(400, ErrMsg.WRONG_CLASS.format(kwargs["class"]))

                if class_["price"] == 0:
                    return class_
                else:
                    uid = self.check_login(kwargs, key_mgr)
                    if not uid:
                        raise cherrypy.HTTPError(401)

                    ss = select([classmanages.c.class_access]).where(classmanages.c.uid == uid)
                    rst = conn.execute(ss)
                    rows = rst.fetchall()

                    # if user don't have class manage then create one
                    if len(rows) == 0:
                        ins = classmanages.insert()
                        rst = conn.execute(ins, dict(uid=uid))
                        return "create class manage"
                    class_access = rows[0]["class_access"]

                    if kwargs["class"] not in class_access:
                        raise cherrypy.HTTPError(400, ErrMsg.NO_ACCESS_TO_CLASS.format(kwargs["class"]))
                    return class_
            else: # return all class info
                return classes.get_class_all_info()
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            if "class" not in data:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("class"))
            if "uid" not in data:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("uid"))

            uid = self.check_login(data, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

            admin = self.check_admin(uid, users, conn)
            if not admin:
                raise cherrypy.HTTPError(401)

            ss = select([classmanages.c.class_access]).where(classmanages.c.uid == data["uid"])
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) == 0:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(data["uid"]))
            class_access = rows[0]["class_access"]

            if data["class"] not in class_access:
                class_access.append(data["class"])

                stmt = update(classmanages).where(classmanages.c.uid == data["uid"]).\
                    values({"class_access": class_access})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            return {}
        elif cherrypy.request.method == "DELETE":
            if "class" not in kwargs:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("class"))
            if "uid" not in kwargs:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format("uid"))

            uid = self.check_login(kwargs, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

            admin = self.check_admin(uid, users, conn)
            if not admin:
                raise cherrypy.HTTPError(401)

            ss = select([classmanages.c.class_access]).where(classmanages.c.uid == kwargs["uid"])
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) == 0:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(kwargs["uid"]))
            class_access = rows[0]["class_access"]

            if kwargs["class"] in class_access:
                class_access.remove(kwargs["class"])

                stmt = update(classmanages).where(classmanages.c.uid == kwargs["uid"]).\
                    values({"class_access": class_access})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            return {}
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def price(self, *args, **kwargs):
        classes = cherrypy.request.classes
        if cherrypy.request.method == "GET":

            paid_class = []
            free_class = []
            for c in classes.classes.values():
                if c["price"] == 0:
                    free_class.append(c["id"])
                else:
                    paid_class.append(c["id"])
            return {"paid": paid_class, "free": free_class}
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def record(self, *args, **kwargs):
        classes = cherrypy.request.classes
        key_mgr = cherrypy.request.key
        meta, conn = cherrypy.request.db
        classmanages = meta.tables[ClassManage.TABLE_NAME]

        if len(args) > 0:
                raise cherrypy.HTTPError(404)

        if cherrypy.request.method == "GET":
            uid = self.check_login(kwargs, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

            ss = select([classmanages.c.class_record]).where(and_(classmanages.c.uid == uid))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) == 0:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(uid))
            return rows[0]["class_record"]

        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json

            uid = self.check_login(data, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

            if "video" not in data:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM("video"))
            video = data["video"]

            class_name, class_id = classes.video_find_class(video)
            if not class_name:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_VIDEO.format(video))

            ss = select([classmanages.c.class_record]).where(classmanages.c.uid == uid)
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) == 0:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(uid))
            class_record = rows[0]["class_record"]

            if class_id not in class_record:
                class_record[class_id] = {}

            if class_name not in class_record[class_id]:
                class_record[class_id][class_name] = 1
            else:
                class_record[class_id][class_name] += 1

            stmt = update(classmanages).where(classmanages.c.uid == uid).\
                values({"class_record": class_record})
            ins = conn.execute(stmt)

            cherrypy.response.status = 201
            return {"success": True}
        else:
            raise cherrypy.HTTPError(404)

class PostRestView(View):
    _root = rest_config["url_root"] + "post/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        posts = meta.tables[Post.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if len(args) > 0:
            raise cherrypy.HTTPError(404)

        if cherrypy.request.method == "GET":
            ss = select([posts]).order_by(desc(posts.c.create_at))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            return {"posts": [Post.mk_dict(row) for row in rows]}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json

            uid = self.check_login(data, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

            admin = self.check_admin(uid, users, conn)
            if not admin:
                raise cherrypy.HTTPError(401)

            if "content" not in data:
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
            uid = self.check_login(kwargs, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

            admin = self.check_admin(uid, users, conn)
            if not admin:
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

class OpinionRestView(View):
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

            uid = self.check_login(data, key_mgr)
            if not uid:
                raise cherrypy.HTTPError(401)

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

# class ClassManageView(View):






