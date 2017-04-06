import cherrypy
import logging, logging.config
import os
import re
import json

from app.model import ErrMsg, User, Question, Answer, Post, Opinion
from app.model import ClassManage, Teacher, AdArea, Classroom, AdClass
from app.model import Activity
from uuid import uuid1 as uuid
from datetime import datetime, timedelta
from datetime import date as Date
from datetime import time as Time
from requests import get as http_get
from requests import post as http_post
from _thread import start_new_thread

from sqlalchemy import desc, not_
from sqlalchemy.sql import select, update, and_, join, or_
from sqlalchemy.exc import IntegrityError

PY_FILE_RE = r"(test|hw)1?[0-9]-[0-9]{1,2}\.py"

ADVERTISE_LIMIT = 5
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


un = "cd4fun_u"
pwd = "mlmlml"
hst = "localhost"
prt = "5432"
db = "coding4fun_db"
DB_STRING = "postgresql://%s:%s@%s:%s/%s?client_encoding=utf8"
rest_config = {
    "url_root": "/rest/1/",
    "db_connstr": DB_STRING % (un, pwd, hst, prt, db),
    }

def count_page(r):
    if (r % 10) == 0:
        return (r // 10)
    return (r // 10) + 1

def find_host(url):
    return url[:url.find("/", 10)]

def send_email_valid(key, addr):
    url = find_host(cherrypy.url()) + "/active/" + key
    cnt = EMAIL_VALID.replace("url", url)
    http_post(EMAIL_REST_URL, params={
        "addr": addr,
        "sub": "Email 認證",
        "cnt": cnt})

class ErrMsg(ErrMsg):
    NOT_LIST = "'{}' must be a list"
    NOT_BOOL = "'{}' must be Boolen"
    NOT_TIME = "'{}' time format wrong"

    UNKNOWN_ID = "Id '{}' is not found"
    WRONG_PASSWORD = "Username or password wrong"
    DISABLED_USER = "User '{}' have been disable by admin"

    USERID_REPEAT = "This userid repeat"
    NOT_HUMAN = "You are not human"

    WRONG_WRITER = "Question's writer id is not '{}'"
    A_WRONG_WRITER = "Answer's writer id is not '{}'"
    SOLVED_QUESTION = "Question '{}' alredy solved"

    NEED_ADMIN = "User '{}' is not admin"

    WRONG_CLASS = "Class '{}' not exist"
    NO_ACCESS_TO_CLASS = "You have permission to watch the class '{}'"
    WRONG_VIDEO = "Videl '{}' is not in any class"

    LIMITED_ADVERTISE = "You reach the limit of advertise number"
    LACK_PERMISSION = "Your class permission not in clude '{}'"
    ADVERTISE_REPEAT = "This advertise repeat"

class View(object):
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
        }

    def check_login(self, json):
        if "key" not in json:
            raise cherrypy.HTTPError(401)
        key_mgr = cherrypy.request.key
        key_valid = key_mgr.get_key(json["key"])
        if not key_valid[0]:
           raise cherrypy.HTTPError(401)

        meta, conn = cherrypy.request.db
        users = meta.tables[User.TABLE_NAME]

        ss = select([users.c.disabled, users.c.id]).where(
            users.c.id == key_valid[1],
            )
        rst = conn.execute(ss)
        row = rst.fetchone()

        if row["disabled"]:
            raise cherrypy.HTTPError(401)
        return row["id"]


    def check_login_u(self, json):
        if "key" not in json:
            raise cherrypy.HTTPError(401)
        key_mgr = cherrypy.request.key
        key_valid = key_mgr.get_key(json["key"])
        if not key_valid[0]:
           raise cherrypy.HTTPError(401)

        meta, conn = cherrypy.request.db
        users = meta.tables[User.TABLE_NAME]

        ss = select([users]).where(
            users.c.id == key_valid[1],
            )
        rst = conn.execute(ss)
        row = rst.fetchone()

        if row["disabled"]:
            raise cherrypy.HTTPError(401)
        return User.mk_dict(row)

    def check_login_teacher(self, json):
        if "tkey" not in json:
            raise cherrypy.HTTPError(401)
        key_mgr = cherrypy.request.key
        key_valid = key_mgr.get_key(json["tkey"])
        if not key_valid[0]:
           raise cherrypy.HTTPError(401)

        meta, conn = cherrypy.request.db
        teachers = meta.tables[Teacher.TABLE_NAME]

        ss = select([teachers]).where(
            teachers.c.id == key_valid[1],
            )
        rst = conn.execute(ss)
        row = rst.fetchone()

        if row["disabled"]:
            raise cherrypy.HTTPError(401)
        return Teacher.mk_dict(row)

    def check_admin(self, uid):
        meta, conn = cherrypy.request.db
        users = meta.tables[User.TABLE_NAME]

        ss = select([users.c.admin]).where(and_(
            users.c.id == uid,
            users.c.admin == True
            ))
        rst = conn.execute(ss)
        row = rst.fetchone()
        if not row:
            return False
        return True

    def check_key(self, _dict, keys):
        for key in keys:
            if key not in _dict:
                raise cherrypy.HTTPError(400, ErrMsg.MISS_PARAM.format(key))

    def parsetime(self, string):
        """
        RIGHT FORM:
        1:30 PM
        11:50 AM
        """
        try:
            _time, apm = string.split()

            hour, min_ = [int(i) for i in _time.split(":")]

            if apm == "PM":
                hour += 12
            if hour == 24:
                hour = 0

            return Time(hour=hour, minute=min_)
        except:
            return False

    def parsedate(self, string):
        """
        RIGHT FORM:
        10/3/2017
        day / moth / year
        """
        try:
            day, month, year = [int(i) for i in string.split("/")]

            return Date(year=year, month=month, day=day)
        except:
            return False

class SessionKeyRestView(View):
    _root = rest_config["url_root"] + "logon/"

    def __init__(self):
        self.key_log = logging.getLogger("key")

    @cherrypy.expose
    def index(self, *args, **kwargs):
        key_mgr = cherrypy.request.key
        meta, conn = cherrypy.request.db

        if cherrypy.request.method == "GET":
            self.check_key(kwargs, ("userid", "password", ))

            users = meta.tables[User.TABLE_NAME]
            ss = select([users.c.id, users.c.disabled]).where(and_(
                users.c.userid == kwargs["userid"],
                users.c.password == kwargs["password"]))
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_PASSWORD)
            else:
                # create session key and return it
                if row["disabled"]:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.DISABLED_USER.format(row["id"]))

                key = str(uuid())
                key_mgr.update_key(key, row["id"])

                return {"key":key,
                    "lastrowid": row["id"],
                    "userid": kwargs["userid"]}
        else:
            raise cherrypy.HTTPError(404)

class UserRestView(View):
    _root = rest_config["url_root"] + "user/"
    _cp_config = View._cp_config
    _cp_config["tools.emailvalidtool.on"] = True

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        users = meta.tables[User.TABLE_NAME]
        classmanages = meta.tables[ClassManage.TABLE_NAME]

        # get user info
        if cherrypy.request.method == "GET":
            user = self.check_login_u(kwargs)

            if "id" in kwargs:
                try:
                    q_uid = int(kwargs["id"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format(kwargs["id"]))

                # get user info and class manager
                j = join(users, classmanages)
                ss = select([users, classmanages.c.class_access]).where(
                    users.c.id == q_uid
                    ).select_from(j)
                rst = conn.execute(ss)
                row = rst.fetchone()

                if not row:
                    # if no match and check user exist
                    ss = select([users]).where(users.c.id == q_uid)
                    rst = conn.execute(ss)
                    row = rst.fetchone()

                    if not row:
                        raise cherrypy.HTTPError(400,
                            ErrMsg.UNKNOWN_ID.format(q_uid))
                    else:
                        # if user exist then create class manager
                        ins = classmanages.insert()
                        rst = conn.execute(ins, dict(uid=q_uid))

                # user who asking info is same user or admin return all info
                if q_uid == user["id"] or user["admin"]:
                    try:
                        return User.mk_dict_classes(row)
                    except:
                        return User.mk_dict(row)

                # otherwise return part of info
                return User.mk_info(row)
            elif "nicknames[]" in kwargs:
                if not user["admin"]:
                    raise cherrypy.HTTPError(401)

                ss = select([users.c.id, users.c.nickname, users.c.userid]).where(
                    users.c.id.in_(kwargs["nicknames[]"]))
                rst = conn.execute(ss)
                rows = rst.fetchall()

                id_2_nick = {}
                for row in rows:
                    id_2_nick[row["id"]] = [row["userid"], row["nickname"]]

                return id_2_nick
            else:
                # need admin to access
                if not user["admin"]:
                    raise cherrypy.HTTPError(401)

                ss = select([users])

                if "userid" in kwargs:
                    ss = ss.where(users.c.userid.like(kwargs["userid"] + "%"))

                rst = conn.execute(ss)
                rows = rst.fetchall()

                return [User.mk_info(u) for u in rows]
        # create user
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json

            self.check_key(data, ("recapcha", "users", ))

            # check gogle recaptch, human check
            r = http_get(RECAPTCHA_URL, params={
                "secret": RECAPTCHA_SERCRET,
                "response": data["recapcha"]})
            if not r.json()["success"]:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_HUMAN)

            # check create user json
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

                ekey = cherrypy.request.email_valid.new_mail(uid)
                send_email_valid(ekey, usersjson[0]["email"])

                return {"key": key, "lastrowid": rst.lastrowid,
                    "userid": usersjson[-1]["userid"]}
            else:
                raise cherrypy.HTTPError(503) 
        #  update user attributes
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json

            user = self.check_login_u(data)

            if not user["admin"]:
                raise cherrypy.HTTPError(401)

            try:
                uid = int(data["uid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("uid"))

            if "disabled" in data:
                stmt = update(users).where(
                    users.c.id == uid).values(
                    {"disabled": data["disabled"]})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(400,
                    ErrMsg.MISS_PARAM.format("disabled"))
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def emailvalid(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        email_valid = cherrypy.request.email_valid
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            ss = select([users.c.email]).where(
                users.c.id == user["id"],
                )
            rst = conn.execute(ss)
            row = rst.fetchone()

            ekey = email_valid.new_mail(user["id"])
            send_email_valid(ekey, row["email"])

            cherrypy.response.status = 201
            return {"success": True}
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            self.check_key(data, ("ekey", ))

            r = email_valid.check_mail(user["id"], data["ekey"])
            if not r:
                raise cherrypy.HTTPRedirect("/")

            stmt = update(users).where(
                users.c.id == user["id"]).values(
                    {"active": True})
            conn.execute(stmt)

            cherrypy.response.status = 201
            return {"success": True}
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def password(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            self.check_key(data, ("password", "newpassword", ))

            stmt = update(users).where(
                and_(users.c.id == user["id"],
                    users.c.password == data["password"])).values(
                        {"password": data["newpassword"]})
            ins = conn.execute(stmt)

            if ins.rowcount != 0:
                key_mgr.pop(data["key"])

                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_PASSWORD)
        else:
            raise cherrypy.HTTPError(404)

class QuestionRestView(View):
    _root = rest_config["url_root"] + "question/"
    _cp_config = View._cp_config

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        questions = meta.tables[Question.TABLE_NAME]
        answers = meta.tables[Answer.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if "id" in kwargs:
                try:
                    qid = int(kwargs["id"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format(kwargs["id"]))

                j = join(questions, users)
                ss = select([questions, users.c.nickname]).where(
                    questions.c.id == qid
                    ).select_from(j)
                rst = conn.execute(ss)
                row = rst.fetchone()
                if not row:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.UNKNOWN_ID.format(qid))

                return Question.mk_dict_user(row)

            ss = None
            if "writer" in kwargs:
                try:
                    uid = int(kwargs["writer"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format(kwargs["writer"]))

                ss = select([questions]).where(questions.c.writer == uid)
            elif "solved" in kwargs:
                solved = False
                if ((kwargs["solved"] != "True") and
                    (kwargs["solved"] != "False")):
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_BOOL.format(kwargs["solved"]))
                elif kwargs["solved"] == "True":
                    solved = True

                ss = select([questions]).where(questions.c.solved == solved)
            elif "answer" in kwargs:
                try:
                    uid = int(kwargs["answer"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format(kwargs["answer"]))

                a_ss = select([answers.c.answer_to]).where(
                    answers.c.writer == uid)

                ss = select([questions]).where(questions.c.id.in_(a_ss))
            else:
                ss = select([questions])

            if "type" in kwargs:
                try:
                    type_ = int(kwargs["type"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format("type"))

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
                question_l = rows[page:-1]

            question_l = [Question.mk_info(row) for row in question_l]
            return {"questions":question_l, "pages":count_page(len(rows))}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            self.check_login_u(data)

            self.check_key(data, ("question_json", ))

            question_json = data["question_json"]
            if not isinstance(question_json, dict):
                raise cherrypy.HTTPError(400, ErrMsg.NOT_DICT)

            q = Question()
            result = q.validate_json(question_json)
            if isinstance(result, Exception):
                raise result

            # check user id exist
            ss = select([users.c.id]).where(
                users.c.id == int(question_json["writer"]))
            rst = conn.execute(ss)
            row = rst.fetchone()
            if not row:
                raise cherrypy.HTTPError(400,
                    ErrMsg.UNKNOWN_ID.format(question_json["writer"]))

            ins = questions.insert()
            rst = conn.execute(ins, question_json)

            if rst.is_insert:
                cherrypy.response.status = 201

                ss = select([questions.c.id]).order_by(desc(questions.c.id))
                row = conn.execute(ss)

                qid = row.first()["id"]
                title = "Coding 4 Fun 討論區 新問題: " + data["question_json"]["title"]
                content = data["question_json"]["content"]

                params = {
                    "addr":"panmpan@gmail.com",
                    "sub": title,
                    "cnt": content
                    }
                http_post(EMAIL_REST_URL,
                    params=params)
                params["addr"] = "shalley.tsay@gmail.com"
                http_post(EMAIL_REST_URL,
                    params=params)

                return {"question_id": qid}
            else:
                raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json

            user = self.check_login_u(data)
            try:
                qid = int(data["qid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

            if "solved" in data:
                solved = False
                if (data["solved"] != "True") and (data["solved"] != "False"):
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_BOOL.format(data["solved"]))
                elif data["solved"] == "True":
                    solved = True

                if user["admin"]:
                    stmt = update(questions).where(
                        questions.c.id == qid
                        ).values({"solved": solved})
                    ins = conn.execute(stmt)

                    cherrypy.response.status = 201
                    return {"success": True}

                stmt = update(questions).where(and_(
                    questions.c.id == qid,
                    questions.c.writer == user["id"])).values(
                        {"solved": solved})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            elif "type" in data:
                type_ = data["type"]

                if user["admin"]:
                    stmt = update(questions).where(
                        questions.c.id == qid).values({"type": type_})
                    ins = conn.execute(stmt)

                    cherrypy.response.status = 201
                    return {"success": True}

                stmt = update(questions).where(and_(
                    questions.c.id == qid,
                    questions.c.writer == user["id"])).values({"type": type_})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(400,
                    ErrMsg.MISS_PARAM.format("solved"))
        elif cherrypy.request.method == "DELETE":
            self.check_key(kwargs, ("id", ))

            user = self.check_login_u(kwargs)

            if not user["admin"]:
                raise cherrypy.HTTPError(401)

            answers = meta.tables[Answer.TABLE_NAME]

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
        questions = meta.tables[Question.TABLE_NAME]

        if cherrypy.request.method == "POST":
            data = cherrypy.request.json

            self.check_key(data, ("qid", "filepath", ))
            uid = self.check_login(data)

            try:
                qid = int(data["qid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

            file_path = data["filepath"]
            if not isinstance(file_path, list):
                raise cherrypy.HTTPError(400,
                    ErrMsg.NOT_LIST.format("filepath"))
            if len(file_path) == 0:
                raise cherrypy.HTTPError(400,
                    ErrMsg.NOT_LIST.format("filepath"))

            # TODO: if file exist then the file upload THIS TIME will be delete

            # TODO: check file exist
            file_string = ("file1", "file2", "file3")
            a = dict(zip(file_string, data["filepath"]))

            stmt = update(questions).where(and_(
                questions.c.id == qid,
                questions.c.writer == uid
                )).values(a)
            ins = conn.execute(stmt)

            if ins.rowcount == 0:
                raise cherrypy.HTTPError(400,
                    ErrMsg.WRONG_WRITER.format(str(uid)))
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
        questions = meta.tables[Question.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]
        answers = meta.tables[Answer.TABLE_NAME]

        if cherrypy.request.method == "GET":
            try:
                qid = int(kwargs["qid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

            ss = select([answers]).where(answers.c.answer_to == qid).\
                order_by(desc(answers.c.create_at))
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
                    ss = select([users.c.nickname]).where(
                        users.c.id == row["writer"])
                    rst = conn.execute(ss)
                    urow = rst.fetchone()
                    if not urow:
                        user_nickname[d["writer"]] = ""
                    else:
                        user_nickname[d["writer"]] = urow["nickname"]

                    d["writer"] = user_nickname[d["writer"]]
                answers.append(d)

            return {"answers": answers}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            uid = self.check_login(data)

            self.check_key(data, (
                "content",
                "writer",
                "answer_to", ))

            # ss = select([users.c.id]).where(
            #     users.c.id == int(answer_json["writer"]))
            # rst = conn.execute(ss)
            # row = rst.fetchone()
            # if not row:
            #     raise cherrypy.HTTPError(400,
            #         ErrMsg.UNKNOWN_ID.format(answer_json["writer"]))

            # check question is solved
            ss = select([questions.c.solved]).where(
                questions.c.id == int(data["answer_to"]))
            rst = conn.execute(ss)
            row = rst.fetchone()
            if not row:
                raise cherrypy.HTTPError(400,
                    ErrMsg.UNKNOWN_ID.format(data["answer_to"]))
            elif row["solved"]:
                raise cherrypy.HTTPError(400, ErrMsg.SOLVED_QUESTION.\
                    format(data["answer_to"]))

            # send email to relative user
            j1 = join(users, questions)
            ss1 = select([users.c.email, users.c.id]).select_from(j1).where(
                questions.c.id==2).group_by(users.c.id)
            j2 = join(users, answers)
            ss2 = select([users.c.email, users.c.id]).select_from(j2).where(
                answers.c.answer_to==2).group_by(users.c.id)

            ss = ss1.union(ss2)
            rst = conn.execute(ss)
            rows = rst.fetchall()

            start_new_thread(self.sendrelative, (rows, data["content"], ))

            data.pop("key")
            ins = answers.insert()
            rst = conn.execute(ins, data)

            if rst.is_insert:
                ss = select([answers.c.id]).order_by(desc(answers.c.id))
                row = conn.execute(ss)

                cherrypy.response.status = 201
                return {"answer_id": row.first()["id"]}
            else:
                raise cherrypy.HTTPError(503)
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def fileattach(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        answers = meta.tables[Answer.TABLE_NAME]

        if cherrypy.request.method == "POST":
            data = cherrypy.request.json
            uid = self.check_login(data)

            self.check_login(data, ("filepath", ))
            try:
                aid = int(data["aid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("aid"))

            file_path = data["filepath"]
            if not isinstance(file_path, list):
                raise cherrypy.HTTPError(400,
                    ErrMsg.NOT_LIST.format("filepath"))
            if len(file_path) == 0:
                raise cherrypy.HTTPError(400,
                    ErrMsg.NOT_LIST.format("filepath"))

            # TODO: if file exist the delete file which upload THIS TIME

            # TODO: check file exist
            file_string = ("file1", "file2", "file3")
            a = dict(zip(file_string, data["filepath"]))

            stmt = update(answers).where(and_(
                answers.c.id == aid, answers.c.writer == uid)).values(a)
            ins = conn.execute(stmt)

            if ins.rowcount == 0:
                raise cherrypy.HTTPError(400,
                    ErrMsg.A_WRONG_WRITER.format(str(uid)))
            else:
                cherrypy.response.status = 201
                return a

        else:
            raise cherrypy.HTTPError(404)

    def sendrelative(self, rows, content):
        for row in rows:
            title = "Coding 4 Fun 討論區 新回應"

            params = {
                "addr": row["email"],
                "sub": title,
                "cnt": content
                }
            http_post(EMAIL_REST_URL, params=params)

class ClassesRestView(View):
    _cp_config = View._cp_config
    _cp_config["tools.classestool.on"] = True
    _root = rest_config["url_root"] + "classes/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        classes = cherrypy.request.classes
        meta, conn = cherrypy.request.db
        classmanages = meta.tables[ClassManage.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if len(kwargs) > 0:
                self.check_key(kwargs, ("class", ))
                class_ = classes.get_class(kwargs["class"])

                if not class_:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.WRONG_CLASS.format(kwargs["class"]))

                if class_["price"] == 0:
                    try:
                        return class_["info"][int(kwargs["lesson"])]
                    except:
                        pass

                    class_ = class_.copy()
                    class_["length"] = len(class_["info"])
                    class_.pop("info")
                    return class_
                else:
                    uid = self.check_login(kwargs)

                    ss = select([classmanages.c.class_access]).where(
                        classmanages.c.uid == uid)
                    rst = conn.execute(ss)
                    row = rst.fetchone()

                    # if user don't have class manage then create one
                    if not row:
                        ins = classmanages.insert()
                        rst = conn.execute(ins, dict(uid=uid))
                        raise cherrypy.HTTPError(400,
                            ErrMsg.NO_ACCESS_TO_CLASS.format(kwargs["class"]))
                    class_access = row["class_access"]

                    if kwargs["class"] not in class_access:
                        raise cherrypy.HTTPError(400,
                            ErrMsg.NO_ACCESS_TO_CLASS.format(kwargs["class"]))

                    try:
                        return class_["info"][int(kwargs["lesson"])]
                    except:
                        pass

                    class_ = class_.copy()
                    class_["length"] = len(class_["info"])
                    class_.pop("info")
                    return class_
            else: # return all class info
                return classes.get_class_all_info()
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            uid = self.check_login(data)
            admin = self.check_admin(uid)
            if not admin:
                raise cherrypy.HTTPError(401)

            self.check_key(data, ("class", "uid", ))

            ss = select([classmanages.c.class_access]).where(
                classmanages.c.uid == data["uid"])
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(400,
                    ErrMsg.UNKNOWN_ID.format(data["uid"]))
            class_access = row["class_access"]

            if data["class"] not in class_access:
                class_access.append(data["class"])

                stmt = update(classmanages).where(
                    classmanages.c.uid == data["uid"]).values(
                    {"class_access": class_access})
                ins = conn.execute(stmt)

                cherrypy.response.status = 201
                return {"success": True}
            return {}
        elif cherrypy.request.method == "DELETE":
            uid = self.check_login(kwargs)
            admin = self.check_admin(uid)
            if not admin:
                raise cherrypy.HTTPError(401)

            self.check_key(kwargs, ("class", "uid", ))

            ss = select([classmanages.c.class_access]).where(
                classmanages.c.uid == kwargs["uid"])
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(400,
                    ErrMsg.UNKNOWN_ID.format(kwargs["uid"]))
            class_access = row["class_access"]

            if kwargs["class"] in class_access:
                class_access.remove(kwargs["class"])

                stmt = update(classmanages).where(
                    classmanages.c.uid == kwargs["uid"]).values(
                    {"class_access": class_access})
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
        meta, conn = cherrypy.request.db
        classmanages = meta.tables[ClassManage.TABLE_NAME]

        if len(args) > 0:
                raise cherrypy.HTTPError(404)

        if cherrypy.request.method == "GET":
            uid = self.check_login(kwargs)

            ss = select([classmanages.c.class_record]).where(and_(
                classmanages.c.uid == uid))
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(uid))
            return row["class_record"]

        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            uid = self.check_login(data)

            self.check_key(data, ("video", ))
            video = data["video"]

            class_name, class_id = classes.video_find_class(video)
            if not class_name:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_VIDEO.format(video))

            ss = select([classmanages.c.class_record]).where(
                classmanages.c.uid == uid)
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(400, ErrMsg.UNKNOWN_ID.format(uid))
            class_record = row["class_record"]

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
            uid = self.check_login(data)
            admin = self.check_admin(uid)
            if not admin:
                raise cherrypy.HTTPError(401)

            self.check_key(data, ("content", ))

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
            uid = self.check_login(kwargs)

            admin = self.check_admin(uid)
            if not admin:
                raise cherrypy.HTTPError(401)

            self.check_key(data, ("id", ))

            # delete post
            ds = posts.delete().where(posts.c.id == kwargs["id"])
            conn.execute(ds)

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
            uid = self.check_login(data)

            self.check_key(data, ("content", ))

            ss = select([users.c.id]).where(users.c.id == uid)
            rst = conn.execute(ss)
            row = rst.fetchone()
            if len(row) <= 0:
                raise cherrypy.HTTPError(400,
                    ErrMsg.UNKNOWN_ID.format(question_json["writer"]))

            ins = opinions.insert()
            rst = conn.execute(ins, {"writer":uid, "content":data["content"]})

            if rst.is_insert:
                cherrypy.response.status = 201

                ss = select([opinions.c.id]).order_by(desc(opinions.c.id))
                row = conn.execute(ss)

                return {"opinions_id": row.fetchone()["id"]}
            else:
                raise cherrypy.HTTPError(503)

        else:
            raise cherrypy.HTTPError(404)

class TeacherRestView(View):
    _root = rest_config["url_root"] + "teacher/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        teachers = meta.tables[Teacher.TABLE_NAME]

        if cherrypy.request.method == "GET":
            # if "tid" in kwargs:
            #     try:
            #         tid = int(kwargs["tid"])
            #     except:
            #         pass

            #     ss = select([teachers]).where(teachers.c.id==tid)
            #     rst = conn.execute(ss)
            #     row = rst.fetchone()

            #     return {tid: Teacher.mk_dict(row)}
            if "tkey" in kwargs:
                teacher = self.check_login_teacher(kwargs)
                return teacher
            else:
                uid = self.check_login(kwargs)
                admin = self.check_admin(uid)
                if not admin:
                    raise cherrypy.HTTPError(401)

                ss = select([teachers])
                rst = conn.execute(ss)
                rows = rst.fetchall()

                return {"teachers": [Teacher.mk_dict(row) for row in rows]}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json

            uid = self.check_login(data)
            admin = self.check_admin(uid)
            if not admin:
                raise cherrypy.HTTPError(401)

            self.check_key(data, ("userid",
                "password",
                "name",
                "phone",
                "class_permission", ))

            j = {
                "userid": data["userid"],
                "password": data["password"],
                "name": data["name"],
                "phone": data["phone"],
                "class_permission": data["class_permission"]
                }
            ins = teachers.insert()
            rst = conn.execute(ins, j)

            if rst.is_insert:
                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json

            if "ext_area" in data:
                uid = self.check_login(data)
                admin = self.check_admin(uid)
                if not admin:
                    raise cherrypy.HTTPError(401)

                try:
                    tid = int(data["tid"])
                    ext_area = int(data["ext_area"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format("tid"))

                stmt = teachers.update().where(
                    teachers.c.id==tid).values(
                    ext_area=teachers.c.ext_area+ext_area)
                conn.execute(stmt)
                return {"success": True}
            elif "whole_city" in data:
                uid = self.check_login(data)
                admin = self.check_admin(uid)
                if not admin:
                    raise cherrypy.HTTPError(401)

                try:
                    tid = int(data["tid"])
                    whole_city = int(data["whole_city"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format("tid"))

                stmt = teachers.update().where(
                    teachers.c.id==tid).values(
                    whole_city=teachers.c.whole_city+whole_city)
                conn.execute(stmt)
                return {"success": True}
            elif "summary" in data:
                teacher = self.check_login_teacher(data)

                stmt = teachers.update().where(
                    teachers.c.id==teacher["id"]).values(
                    summary=data["summary"])
                conn.execute(stmt)
                return {"success": True}
            else:
                raise cherrypy.HTTPError(404)
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def login(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        teachers = meta.tables[Teacher.TABLE_NAME]
        key_mgr = cherrypy.request.key

        if cherrypy.request.method == "GET":
            self.check_key(kwargs, ("userid", "password", ))

            ss = select([teachers.c.id, teachers.c.disabled]).where(and_(
                teachers.c.userid == kwargs["userid"],
                teachers.c.password == kwargs["password"]))
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_PASSWORD)
            else:
                # create session key and return it
                if row["disabled"]:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.DISABLED_USER.format(row["id"]))

                key = str(uuid())
                key_mgr.update_key(key, row["id"])

                return {"key":key, "id": row["id"], "userid": kwargs["userid"]}
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def user(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        teachers = meta.tables[Teacher.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            teacher = self.check_login_teacher(kwargs)

            self.check_key(kwargs, ("users[]", ))

            ss = select([users.c.userid]).where(
                users.c.userid.in_(kwargs["users[]"]))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            for row in rows:
                kwargs["users[]"].remove(row.userid)

            return {"none": kwargs["users[]"]}
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def password(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        teachers = meta.tables[Teacher.TABLE_NAME]

        if cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            teacher = self.check_login_teacher(data)

            self.check_key(data, ("password", "newpassword", ))

            stmt = update(teachers).where(
                and_(teachers.c.id == teacher["id"],
                    teachers.c.password == data["password"])).values(
                        {"password": data["newpassword"]})
            ins = conn.execute(stmt)

            if ins.rowcount != 0:
                key_mgr.pop(data["tkey"])

                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_PASSWORD)
        else:
            raise cherrypy.HTTPError(404)

class AdAreaRestView(View):
    _root = rest_config["url_root"] + "adarea/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        adareas = meta.tables[AdArea.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if "tkey" in kwargs:
                teacher = self.check_login_teacher(kwargs)

                ss = select([adareas]).where(
                    adareas.c.teacher == teacher["id"]
                    )
                rst = conn.execute(ss)
                rows = rst.fetchall()

                if len(rows) == 0:
                    return {"advertise": []}
                json = {
                    "adareas": [AdArea.mk_dict(row) for row in rows],
                    }
                return json
            else:
                teachers = meta.tables[Teacher.TABLE_NAME]
                adclasses = meta.tables[AdClass.TABLE_NAME]

                ss = select([
                    teachers.c.name,
                    teachers.c.id,
                    teachers.c.phone,
                    teachers.c.summary,

                    adareas.c.city,
                    adareas.c.town,

                    adclasses.c.id.label("adclassid"),
                    adclasses.c.address,
                    adclasses.c.type,
                    adclasses.c.date,
                    adclasses.c.start_time,
                    adclasses.c.end_time,
                    adclasses.c.weekdays,
                    ])

                j1 = teachers.join(
                    adareas, teachers.c.id==adareas.c.teacher).join(
                    adclasses, teachers.c.id==adclasses.c.teacher)
                ss = ss.select_from(j1)
                rst = conn.execute(ss)
                rows = rst.fetchall()

                if len(rows) == 0:
                    return []

                return [Teacher.mk_dict_adarea_adclass(row) for row in rows]
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            teacher = self.check_login_teacher(data)

            self.check_key(data, ("city", "town", ))

            try:
                city = int(data["city"])
                town = int(data["town"])
            except:
                raise cherrypy.NOT_INT.format("city or town")

            ss = select([adareas.c.id]).where(
                adareas.c.teacher==teacher["id"]
                )
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) >= ADVERTISE_LIMIT + teacher["ext_area"]:
                raise cherrypy.HTTPError(400, ErrMsg.LIMITED_ADVERTISE)

            ss = select([adareas.c.id]).where(and_(
                adareas.c.city==city,
                adareas.c.town==town,
                adareas.c.teacher==teacher["id"]))
            rst = conn.execute(ss)
            row = rst.fetchone()

            if row:
                raise cherrypy.HTTPError(400, ErrMsg.ADVERTISE_REPEAT)

            j = {
                "teacher": teacher["id"],
                "city": city,
                "town": town,
                }

            ins = adareas.insert()
            rst = conn.execute(ins, j)
            if rst.is_insert:
                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "DELETE":
            teacher = self.check_login_teacher(kwargs)

            try:
                aid = int(kwargs["aid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format(aid))

            # delete answer
            ds = adareas.delete().where(and_(
                adareas.c.id == aid,
                adareas.c.teacher == teacher["id"]))
            rst = conn.execute(ds)

            return {"success": True}
        else:
            raise cherrypy.HTTPError(404)

class AdClassRestView(View):
    _root = rest_config["url_root"] + "adclass/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        adclasses = meta.tables[AdClass.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if "tkey" in kwargs:
                teacher = self.check_login_teacher(kwargs)

                ss = select([adclasses]).where(
                    adclasses.c.teacher == teacher["id"]
                    )
                rst = conn.execute(ss)
                rows = rst.fetchall()

                if len(rows) == 0:
                    return {"adclasses": []}
                json = {
                    "adclasses": [AdClass.mk_dict(row) for row in rows],
                    }
                return json
        if cherrypy.request.method == "POST":
            data = cherrypy.request.json
            teacher = self.check_login_teacher(data)

            self.check_key(data, (
                "address",
                "type",
                "date",
                "start_time",
                "end_time",
                "weekdays",))

            date_ = self.parsedate(data["date"])

            if not date_:
                raise cherrypy.HTTPError(400, "Date format wrong")

            start_time = self.parsetime(data["start_time"])
            end_time = self.parsetime(data["end_time"])

            if (not start_time) or (not end_time):
                raise cherrypy.HTTPError(400, "Time format wrong")
            if end_time < start_time:
                raise cherrypy.HTTPError(400, "End time over start time.")

            if not isinstance(data["weekdays"], list):
                raise cherrypy.HTTPError(400, ErrMsg.NOT_LIST("weekdays"))

            json = {
                "teacher": teacher["id"],
                "address": data["address"],
                "type": data["type"],
                "date": date_,
                "start_time": start_time,
                "end_time": end_time,
                "weekdays": data["weekdays"],
                }

            ins = adclasses.insert()
            rst = conn.execute(ins, json)

            if rst.is_insert:
                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "DELETE":
            teacher = self.check_login_teacher(kwargs)

            try:
                aid = int(kwargs["aid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format(aid))

            # delete answer
            ds = adclasses.delete().where(and_(
                adclasses.c.id == aid,
                adclasses.c.teacher == teacher["id"]))
            rst = conn.execute(ds)

            return {"success": True}
        else:
            raise cherrypy.HTTPError(404)

class ClassroomRestView(View):
    _root = rest_config["url_root"] + "classroom/"
    _cp_config = {
        "tools.json_out.on": True,
        "tools.json_in.on": True,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8",
        "tools.classestool.on": True,
        }

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if "tkey" in kwargs:
                teacher = self.check_login_teacher(kwargs)

                ss = select([classrooms]).where(
                    classrooms.c.teacher==teacher["id"])
                rst = conn.execute(ss)
                rows = rst.fetchall()

                return [Classroom.mk_dict(row) for row in rows]
            elif "key" in kwargs:
                user = self.check_login_u(kwargs)

                ss = select([classrooms]).where(
                    classrooms.c.students_cid.any(user["id"]))
                rst = conn.execute(ss)
                rows = rst.fetchall()

                return [Classroom.mk_info(row, user["id"]) for row in rows]
            else:
                raise cherrypy.HTTPError(404)
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            teacher = self.check_login_teacher(data)

            self.check_key(data, ("name",
                "students_name",
                "students_cid",
                "students_sid",
                "type"))

            if not isinstance(data["students_name"], list):
                raise ErrMsg.NOT_LIST.format("students_name")
            if not isinstance(data["students_cid"], list):
                raise ErrMsg.NOT_LIST.format("students_cid")
            if not isinstance(data["students_sid"], list):
                raise ErrMsg.NOT_LIST.format("students_sid")

            ss = select([users.c.id, users.c.userid]).where(
                users.c.userid.in_(data["students_cid"]))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            for row in rows:
                userid = data["students_cid"].index(row.userid)
                data["students_cid"][userid] = row.id

            json = {
                "teacher": teacher["id"],
                "name": data["name"],
                "students_name": data["students_name"],
                "students_cid": data["students_cid"],
                "students_sid": data["students_sid"],
                "type": data["type"],
                }
            if json["type"] == "python_01":
                classes = cherrypy.request.classes

                folder = uuid()
                os.mkdir(classes.get_download_path() + "/" + str(folder))
                json["folder"] = folder

            ins = classrooms.insert()
            rst = conn.execute(ins, json)

            if rst.is_insert:
                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(503)
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def check_folder(self, *args, **kwargs):
        classes = cherrypy.request.classes
        if cherrypy.request.method == "GET":
            self.check_key(kwargs, ("folder", ))

            path = classes.get_download_path() + "/" + kwargs["folder"]

            files = []
            if "cid" in kwargs:
                for *_, fs in os.walk(path):
                    for f in fs:
                        if f.startswith(kwargs["cid"]):
                            files.append(f)
            else:
                for *_, fs in os.walk(path):
                    for f in fs:
                        files.append(f)

            return files
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def comment(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]

        if cherrypy.request.method == "GET":
            self.check_key(kwargs, ("cls_id", ))

            ss = select([classrooms.c.comment,
                classrooms.c.students_cid]).where(
                classrooms.c.id == kwargs["cls_id"])
            rst = conn.execute(ss)
            row = rst.fetchone()

            return row["comment"]
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            self.check_login_teacher(data)

            self.check_key(data, ("cls_id", "student", "hw", "comment" ))

            if len(data["comment"]) > 100:
                raise cherrypy.HTTPError(400, "Comment too long")

            ss = select([classrooms.c.comment,
                classrooms.c.students_cid]).where(
                classrooms.c.id == data["cls_id"])
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(400)

            try:
                student = int(data["student"])
            except:
                raise cherrypy.HTTPError(400,
                    ErrMsg.NOT_INT.format(data["student"]))
            if student not in row["students_cid"]:
                raise cherrypy.HTTPError(400)

            student = str(student)
            if student not in row["comment"]:
                row["comment"][student] = {}
            row["comment"][student][data["hw"]] = data["comment"]

            stmt = update(classrooms).where(
                classrooms.c.id == data["cls_id"]).values(
                {"comment": row["comment"]})
            conn.execute(stmt)

            cherrypy.response.status = 201
            return {"success": True}
        else:
            raise cherrypy.HTTPError(404)

class FileUploadRestView(View):
    _root = rest_config["url_root"] + "upload/"
    _cp_config = {
        "tools.json_out.on": False,
        "tools.json_in.on": False,
        "tools.dbtool.on": True,
        "tools.keytool.on": True,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8",
        "tools.classestool.on": True,
        }

    @cherrypy.expose
    def homework(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]
        classes = cherrypy.request.classes
        # users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "POST":
            user = self.check_login_u(kwargs)

            self.check_key(kwargs, ("homwork",
                "clsroomid", ))

            ss = select([classrooms.c.folder]).where(and_(
                classrooms.c.id==kwargs["clsroomid"],
                classrooms.c.students_cid.any(user["id"])))
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(400)

            path = classes.get_download_path()
            fileformat = path + "{folder}/{uid}_{filename}"

            if isinstance(kwargs["homwork"], list):
                for file in kwargs["homwork"]:
                    try:
                        if not re.fullmatch(PY_FILE_RE, file.filename):
                            continue

                        filename = file.filename
                        print(filename)
                        filename.replace("test", "")

                        filename = fileformat.format(
                            folder=row["folder"],
                            uid=user["id"],
                            filename=filename)

                        f = open(filename, "wb")
                        while True:
                            data = file.file.read(8192)
                            if not data:
                                break
                            f.write(data)
                        f.close()
                    except:
                        if os.path.isfile(filename):
                            os.remove(filename)
            else:
                try:
                    file = kwargs["homwork"]
                    if not re.fullmatch(PY_FILE_RE, file.filename):
                        raise cherrypy.HTTPRedirect("/classattend")

                    filename = file.filename
                    print(filename)
                    filename.replace("test", "")

                    filename = fileformat.format(
                        folder=row["folder"],
                        uid=user["id"],
                        filename=filename)

                    f = open(filename, "wb")
                    while True:
                        data = file.file.read(8192)
                        if not data:
                            break
                        f.write(data)
                    f.close()
                except:
                    if os.path.isfile(filename):
                        os.remove(filename)

            raise cherrypy.HTTPRedirect("/classattend")
        else:
            raise cherrypy.HTTPError(404)

class ActivityRestView(View):
    _root = rest_config["url_root"] + "activity/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        activities = meta.tables[Activity.TABLE_NAME]

        if cherrypy.request.method == "GET":
            user = self.check_login_u(kwargs)

            if "participant" in kwargs:
                ss = select([activities])

                if kwargs["participant"] == "True":
                    ss = ss.where(activities.c.participant.any(user["id"]))
                else:
                    ss = """SELECT * FROM tb_activity
                        WHERE NOT %i = ANY(participant);""" % user["id"]

                rst = conn.execute(ss)
                rows = rst.fetchall()

                return [Activity.mk_info(row) for row in rows]
            elif "present" in kwargs:
                ss = select([activities])

                if kwargs["present"] == "True":
                    ss = ss.where(activities.c.present.any(user["id"]))
                else:
                    ss = """SELECT * FROM tb_activity
                        WHERE id = ANY(participant)
                        AND NOT id = ANY(present);""".replace("id", str(user["id"]))

                rst = conn.execute(ss)
                rows = rst.fetchall()

                return [Activity.mk_info(row) for row in rows]
            elif "year" in kwargs:
                try:
                    year = int(kwargs["year"])
                except:
                    raise cherrypy.HTTPError(400)

                ss = select([activities]).where(and_(
                    activities.c.date>=Date(year=year, month=1, day=1),
                    activities.c.date<=Date(year=year, month=12, day=31)))
                rst = conn.execute(ss)
                rows = rst.fetchall()

                if user["admin"]:
                    activities_date = [Activity.mk_dict(row) for row in rows]
                else:
                    activities_date = [Activity.mk_info(row) for row in rows]

                ss = select([activities]).where(and_(
                    activities.c.repeat!=0,
                    activities.c.disabled==False))
                rst = conn.execute(ss)
                rows = rst.fetchall()

                if user["admin"]:
                    activities_repeat = [Activity.mk_dict(row) for row in rows]
                else:
                    activities_repeat = [Activity.mk_info(row) for row in rows]

                return {"date": activities_date, "repeat": activities_repeat}
            else:
                raise cherrypy.HTTPError(400)
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            if not user["admin"]:
                raise cherrypy.HTTPError(401)

            self.check_key(data, (
                "name",
                "repeat",
                "time",
                "date",
                "addr",
                "summary",
                "point",
                ))

            try:
                repeat = int(data["repeat"])
            except:
                raise cherrypy.HTTPError(400)

            time = self.parsetime(data["time"])
            if not time:
                raise cherrypy.HTTPError(400)

            try:
                int(data["point"])
            except:
                raise cherrypy.HTTPError(400)

            json = {
                "name": data["name"],
                "repeat": repeat,
                "time": time,
                "addr": data["addr"],
                "summary": data["summary"],
                "point": data["point"],
                }

            if repeat == 0:
                date = self.parsedate(data["date"])
                if not date:
                    raise cherrypy.HTTPError(400)
                json["date"] = date

            ins = activities.insert()
            rst = conn.execute(ins, json)

            if rst.is_insert:
                cherrypy.response.status = 201

                return {"success": True}
            else:
                raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            if "participant" in data:
                self.check_key(data, ("id",))

                ss = select([activities.c.participant]).where(
                    activities.c.id==data["id"])
                rst = conn.execute(ss)
                row = rst.fetchone()

                if user["id"] in row["participant"]:
                    row["participant"].remove(user["id"])
                else:
                    row["participant"].append(user["id"])

                stmt = update(activities).where(
                    activities.c.id == data["id"]).values(
                        {"participant": row["participant"]})
                conn.execute(stmt)

                return {"success": True}
            elif "present" in data:
                if not user["admin"]:
                    raise cherrypy.HTTPError(401)

                if not isinstance(data["present"], dict):
                    raise cherrypy.HTTPError(400, ErrMsg.NOT_DICT)

                for i in  data["present"]:
                    stmt = update(activities).where(
                        activities.c.id==i).values(
                            {"present": data["present"][i]})
                    conn.execute(stmt)

                return {"success": True}
            elif "point":
                if not user["admin"]:
                    raise cherrypy.HTTPError(401)

                self.check_key(data, ("presents", ))

                try:
                    int(data["point"])
                except:
                    raise cherrypy.HTTPError(400)

                if not isinstance(data["presents"], list):
                    raise cherrypy.HTTPError(400)
                users = meta.tables[User.TABLE_NAME]

                stmt = update(users).where(
                    users.c.id.in_(data["presents"])).values(
                        point=users.c.point + data["point"])
                conn.execute(stmt)

                return {"sccuess": True}
            else:
                raise cherrypy.HTTPError(400)
        else:
            raise cherrypy.HTTPError(404)
