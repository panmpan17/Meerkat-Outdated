import cherrypy
import logging, logging.config
import os
import re
import json

from app.email_html import Email
from app.model import ErrMsg, User, Question, Answer, Post
from app.model import Teacher, TeacherInfo, AdArea, Classroom, AdClass
from app.model import Activity, Report
from uuid import uuid1 as uuid
from datetime import datetime, timedelta
from datetime import date as Date
from datetime import time as Time
from requests import get as http_get
from requests import post as http_post
from _thread import start_new_thread

from sqlalchemy import desc, not_
from sqlalchemy.sql import select, update, and_, or_, join, outerjoin
from sqlalchemy.exc import IntegrityError

PY_FILE_RE = r"(test|hw)1?[0-9]-[0-9]{1,2}\.py"

ADVERTISE_LIMIT = 5
RECAPTCHA_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_SERCRET = "6LcSMwoUAAAAAEIO6z5s2FO4QNjz0pZqeD0mZqRZ"

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

def GMT(t):
    # G = timezone("GMT")
    # utc = t.utcnow()
    t += timedelta(hours=8)
    fmt = '%Y / %m / %d %H:%M'
    return t.strftime(fmt)

def count_page(r):
    if (r % 10) == 0:
        return (r // 10)
    return (r // 10) + 1

def find_host(url):
    return url[:url.find("/", 10)]

def send_email_valid(key, addr, userid):
    url = cherrypy.url()
    url = url[url.find("//") + 2:]
    url = url[:url.find("/")]
    cnt = Email.REGIST_VALID.format(url=url, code=key)
    http_post(Email.URL, params={
        "addrs": [addr],
        "sub": "Email 認證 - " + userid,
        "cnt": cnt})

def path_join(path1, path2):
    return os.path.join(path1, path2)

class ErrMsg(ErrMsg):
    NOT_LIST = "'{}' must be a list"
    NOT_BOOL = "'{}' must be Boolen"
    NOT_TIME = "'{}' time format wrong"

    UNKNOWN_ID = "Id '{}' is not found"
    WRONG_PASSWORD = "Username or password wrong"
    DISABLED_USER = "User '{}' have been disable by admin"
    NEED_ACTIVE = "User is not active"

    USERID_REPEAT = "This userid repeat"
    NOT_HUMAN = "You are not human"

    WRONG_WRITER = "Question's writer id is not '{}'"
    A_WRONG_WRITER = "Answer's writer id is not '{}'"
    SOLVED_QUESTION = "Question '{}' already solved"

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
        "tools.filetool.on": True,
        "tools.encode.encoding": "utf-8"
        }

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

        if not row:
            key_mgr.drop_key(json["key"])
            raise cherrypy.HTTPError(401)
        if row["disabled"]:
            key_mgr.drop_key(json["key"])
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

        if not row:
            key_mgr.drop_key(json["tkey"])
            raise cherrypy.HTTPError(401)
        if row["disabled"]:
            key_mgr.drop_key(json["tkey"])
            raise cherrypy.HTTPError(401)
        return Teacher.mk_dict(row)

    def check_login_teacher2(self, json):
        if "key" not in json:
            raise cherrypy.HTTPError(401)
        key_mgr = cherrypy.request.key
        key_valid = key_mgr.get_key(json["key"])
        if not key_valid[0]:
           raise cherrypy.HTTPError(401)

        meta, conn = cherrypy.request.db
        users = meta.tables[User.TABLE_NAME]
        teacherinfos = meta.tables[TeacherInfo.TABLE_NAME]

        ss = select([
            users,
            teacherinfos.c.name,
            teacherinfos.c.phone,
            teacherinfos.c.ext_area,
            teacherinfos.c.whole_city,
            teacherinfos.c.class_permission,
            teacherinfos.c.contact_link,
            teacherinfos.c.summary,
            ])\
            .select_from(join(teacherinfos, users, teacherinfos.c.id==users.c.id))\
            .where(teacherinfos.c.id==key_valid[1])
        rst = conn.execute(ss)
        row = rst.fetchone()
        if row["disabled"]:
            key_mgr.drop_key(json["key"])
            raise cherrypy.HTTPError(401)
        return User.mk_dict_teacher(row)

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
    _cp_config = View._cp_config.copy()
    _cp_config["tools.emailvalidtool.on"] = True

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        email_valid = cherrypy.request.email_valid
        users = meta.tables[User.TABLE_NAME]

        # get user info
        if cherrypy.request.method == "GET":
            user = self.check_login_u(kwargs)

            if "id" in kwargs:
                try:
                    q_uid = int(kwargs["id"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format(kwargs["id"]))

                if q_uid == user["id"]:
                    if not user["active"]:
                        user["email_valid"] = email_valid.get_status(user["id"])
                    return user

                # get user info
                ss = select([users]).where(users.c.id == q_uid)
                rst = conn.execute(ss)
                row = rst.fetchone()

                if not row:
                    raise cherrypy.HTTPError(400)

                # user who asking info is same user or admin return all info
                if q_uid == user["id"] or user["admin"]:
                    return User.mk_dict(row)

                # otherwise return part of info
                return User.mk_info(row)
            elif "nicknames[]" in kwargs:
                if not user["admin"]:
                    raise cherrypy.HTTPError(401)

                ss = select([
                    users.c.id,
                    users.c.nickname,
                    users.c.userid]).where(
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
                    upper = kwargs["userid"].upper()
                    lower = kwargs["userid"].lower()
                    ss = ss.where(or_(
                        users.c.userid.like(upper + "%"),
                        users.c.userid.like(lower + "%")))

                ss = ss.order_by(users.c.id)
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

            ins = users.insert().returning(users.c.id)
            try:
                rst = conn.execute(ins, usersjson)
            except IntegrityError:
                raise cherrypy.HTTPError(400, ErrMsg.USERID_REPEAT)

            if rst.is_insert:
                cherrypy.response.status = 201
                key = str(uuid())
                uid = rst.fetchone()["id"]

                key_mgr.update_key(key, uid)
                ekey = email_valid.new_mail(uid)
                send_email_valid(ekey,
                    usersjson[0]["email"], usersjson[0]["userid"])

                return {
                    "key": key,
                    "lastrowid": uid,
                    "userid": usersjson[-1]["userid"]
                    }
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
            send_email_valid(ekey, row["email"], user["userid"])

            cherrypy.response.status = 201
            return {"success": True}
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            self.check_key(data, ("ekey", ))

            r = email_valid.check_mail(user["id"], data["ekey"])
            if not r:
                raise cherrypy.HTTPError(400)

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
                key_mgr.drop_key(data["key"])

                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(400, ErrMsg.WRONG_PASSWORD)
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def changemail(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        emailvalid = cherrypy.request.email_valid
        users = meta.tables[User.TABLE_NAME]
        changeemails = emailvalid.changeemails

        if cherrypy.request.method == "GET":
            user = self.check_login_u(kwargs)

            if user["id"] not in changeemails:
                raise cherrypy.HTTPError(400)

            return {"stage": changeemails[user["id"]].stage}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            if user["id"] not in changeemails:
                code = emailvalid.new_change(user["id"], user["email"])

                send_email_valid(code, user["email"], user["userid"])

            return {"stage": changeemails[user["id"]].stage}
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            if user["id"] not in changeemails:
                raise cherrypy.HTTPError(400)

            if "code" in data:
                if data["code"] != changeemails[user["id"]].code:
                    raise cherrypy.HTTPError(400)

                if changeemails[user["id"]].new != None:
                    new_email = changeemails[user["id"]].new

                    stmt = update(users).where(users.c.id==user["id"]).values(
                        {"email": new_email})
                    rst = conn.execute(stmt)

                    if rst.rowcount != 0:
                        changeemails.pop(user["id"])

                        return {"passed": True}
                    else:
                        raise cherrypy.HTTPError(503)
                else:
                    changeemails[user["id"]].stage = 2
                    return {"passed": False,
                        "stage": changeemails[user["id"]].stage}
            elif "email" in data:
                if changeemails[user["id"]].new != None:
                    raise cherrypy.HTTPError(400)

                changeemails[user["id"]].new = data["email"]
                changeemails[user["id"]].newcode()

                changeemails[user["id"]].stage = 3

                send_email_valid(
                    changeemails[user["id"]].code,
                    changeemails[user["id"]].new,
                    user["userid"])
                return {
                    "passed": False,
                    "stage": changeemails[user["id"]].stage}
            else:
                raise cherrypy.HTTPError(400)
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def forget(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        emailvalid = cherrypy.request.email_valid
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "POST":
            # new forget password
            pass
        elif cherrypy.request.method == "PUT":
            # comfirm code
            pass
        else:
            raise cherrypy.HTTPError(404)

class QuestionRestView(View):
    _root = rest_config["url_root"] + "question/"
    _cp_config = View._cp_config

    def send_new_question_email(self, addrs, qid, title, content):
        title = "Coding 4 Fun 討論區 新問題: " + title
        
        url = "http://coding4fun.tw/question?q=" + str(qid)
        content = Email.NEWQUESTION.format(title=title,
            content=content,
            url=url)
        r = http_post(Email.URL, params={
            "addrs": addrs,
            "sub": title,
            "cnt": content})

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

            ss = select([questions, users.c.nickname.label("writer_nickname")]).select_from(join(questions, users)).where(
                users.c.id==questions.c.writer)
            if "writer" in kwargs:
                try:
                    uid = int(kwargs["writer"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format(kwargs["writer"]))

                ss = ss.where(questions.c.writer == uid)
            elif "solved" in kwargs:
                solved = False
                if ((kwargs["solved"] != "True") and
                    (kwargs["solved"] != "False")):
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_BOOL.format(kwargs["solved"]))
                elif kwargs["solved"] == "True":
                    solved = True

                ss = ss.where(questions.c.solved == solved)
            elif "answer" in kwargs:
                try:
                    uid = int(kwargs["answer"])
                except:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.NOT_INT.format(kwargs["answer"]))

                a_ss = select([answers.c.answer_to]).where(
                    answers.c.writer == uid)

                ss = ss.where(questions.c.id.in_(a_ss))

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

            questions_list = []
            for row in question_l:
                ss = select([users.c.nickname,
                    answers.c.create_at]).select_from(join(answers, users)).where(
                    answers.c.answer_to==row["id"]).order_by(answers.c.create_at).limit(1)
                rst = conn.execute(ss)
                answer_row = rst.fetchone()
                questions_list.append(Question.mk_info(row, answer_row))
            return {"questions": questions_list, "pages":count_page(len(rows))}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            self.check_key(data, (
                "title",
                "content",
                "type",
                ))

            if not user["active"]:
                raise cherrypy.HTTPError(400, ErrMsg.NEED_ACTIVE)

            ins = questions.insert().returning(questions.c.id)
            rst = conn.execute(ins, {
                "title": data["title"],
                "content": data["content"],
                "type": data["type"],
                "writer": user["id"],
                })

            if rst.is_insert:
                cherrypy.response.status = 201

                qid = rst.fetchone()["id"]
                title = data["title"]
                content = data["content"]

                addrs = [
                    "panmpan@gmail.com",
                    "shalley.tsay@gmail.com",
                    "joanie0610@gmail.com",
                    "jskblack@gmail.com",
                    "chienhsiang.chang@gmail.com",
                    ]

                self.send_new_question_email(addrs, qid, title, content)

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
            user = self.check_login_u(data)

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
                questions.c.writer == user["id"]
                )).values(a)
            ins = conn.execute(stmt)

            if ins.rowcount == 0:
                raise cherrypy.HTTPError(400,
                    ErrMsg.WRONG_WRITER.format(str(user["id"])))
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
            self.check_login_u(data)

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
                raise cherrypy.HTTPError(400, ErrMsg.SOLVED_QUESTION.format(data["answer_to"]))

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
            ins = answers.insert().returning(answers.c.id)
            rst = conn.execute(ins, data)

            if rst.is_insert:
                cherrypy.response.status = 201
                return {"answer_id": rst.fetchone()["id"]}
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
            user = self.check_login_u(data)

            self.check_key(data, ("filepath", ))
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
                answers.c.id == aid, answers.c.writer == user["id"])).values(a)
            ins = conn.execute(stmt)

            if ins.rowcount == 0:
                raise cherrypy.HTTPError(400,
                    ErrMsg.A_WRONG_WRITER.format(str(user["id"])))
            else:
                cherrypy.response.status = 201
                return a

        else:
            raise cherrypy.HTTPError(404)

    def sendrelative(self, rows, content):
        for row in rows:
            title = "Coding 4 Fun 討論區 新回應"

            params = {
                "addrs": row["email"],
                "sub": title,
                "cnt": content
                }
            http_post(Email.URL, params=params)

class ClassesRestView(View):
    _cp_config = View._cp_config.copy()
    _cp_config["tools.classestool.on"] = True
    _cp_config["tools.clsromtool.on"] = True
    _root = rest_config["url_root"] + "classes/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        classes = cherrypy.request.classes
        meta, conn = cherrypy.request.db
        # users = meta.tables[User.TABLE_NAME]
        classrooms = meta.tables[Classroom.TABLE_NAME]
        clsrom_mgr = cherrypy.request.clsrom

        if cherrypy.request.method == "GET":
            if len(kwargs) > 0:
                self.check_key(kwargs, ("class", ))
                class_ = classes.get_class(kwargs["class"])

                if not class_:
                    raise cherrypy.HTTPError(400,
                        ErrMsg.WRONG_CLASS.format(kwargs["class"]))

                #if class is free
                if class_["permission"] == None:
                    logon = False
                    try:
                        user = self.check_login_u(kwargs)
                        logon = True
                    except:
                        try:
                            teacher = self.check_login_teacher(kwargs)
                            logon = True
                        except:
                            pass

                    try:
                        lesson = int(kwargs["lesson"])
                        if logon:
                            return class_["lessons"][lesson]
                        elif lesson >= len(class_["trial"]):
                            return {"success": False, "reason": "trial key"}
                        else:
                            return class_["lessons"][lesson]
                    except:
                        pass

                    class_ = class_.copy()
                    class_["length"] = len(class_["lessons"])
                    if not logon:
                        class_["key_type"] = "trial"
                    class_.pop("lessons")
                    return class_
                else:
                    progress = None
                    folder = None
                    # check user have been checked before
                    if "cls_per_key" in kwargs:
                        key = kwargs["cls_per_key"]
                        key_info = clsrom_mgr.get_cls_per_key(kwargs["cls_per_key"])
                        if not key_info:
                            raise cherrypy.HTTPError(400)

                    else:
                        clsr_id = None
                        key_type = None
                        try:
                            user = self.check_login_u(kwargs)

                            try:
                                clsr_id = int(kwargs["clsrid"])
                            except:
                                key_type = "trial"
                                clsr_id = None
                                key = str(uuid())
                                clsrom_mgr.update_cls_per_key(key, key_type, clsr_id)

                                class_ = class_.copy()
                                class_["length"] = 1
                                class_.pop("lessons")
                                class_["key"] = key
                                class_["key_type"] = key_type
                                return class_

                            ss = select([
                                classrooms.c.progress,
                                classrooms.c.folder,
                                classrooms.c.students_cid]).where(
                                    classrooms.c.id==clsr_id,
                                    )
                            rst = conn.execute(ss)
                            row = rst.fetchone()

                            if row:
                                if user["id"] not in row["students_cid"]:
                                    raise Exception("not in class")

                                key_type = "user"
                                folder = row["folder"]
                                progress = row["progress"]
                            else:
                                raise Exception("clsrid wrong")

                        except Exception as e:
                            print(e)
                            teacher = self.check_login_teacher(kwargs)
                            if kwargs["class"] not in teacher["class_permission"]:
                                raise cherrypy.HTTPError(400)

                            key_type = "teacher"
                        key = str(uuid())

                        clsrom_mgr.update_cls_per_key(key, key_type, clsr_id)

                    try:
                        lesson = int(kwargs["lesson"])
                        if key_info["type"] != "trial":
                            return class_["lessons"][lesson]
                        elif lesson >= len(class_["trial"]):
                            return {"success": False, "reason": "trial key"}
                        else:
                            return class_["lessons"][lesson]
                    except:
                        pass

                    class_ = class_.copy()
                    class_["length"] = len(class_["lessons"])
                    class_.pop("lessons")
                    class_["key"] = key
                    class_["key_type"] = key_type
                    class_["progress"] = progress
                    class_["folder"] = folder
                    return class_
            else: # return all class info
                raise cherrypy.HTTPError(404)
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def all(self, *args, **kwargs):
        classes = cherrypy.request.classes
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]

        classroom_in = {}
        login_as = None
        
        try:
            # test user login
            user = self.check_login_u(kwargs)
            login_as = "user"

            for cls_type in classes.get_subjects_name():
                ss = select([
                        classrooms.c.id,
                        classrooms.c.name,
                        classrooms.c.students_cid]).where(
                            classrooms.c.type==cls_type
                            )
                rst = conn.execute(ss)
                rows = rst.fetchall()

                if rows:
                    for row in rows:
                        if user["id"] in row["students_cid"]:
                            if cls_type not in classroom_in:
                                classroom_in[cls_type] = {}

                            classroom_in[cls_type][row["id"]] = {
                                "id": row["id"],
                                "name": row["name"],
                                "type": cls_type,
                                }
        except:
            try:
                # user login failed try teacher
                teacher = self.check_login_teacher(kwargs)
                login_as = "teacher"
                classroom_in = teacher["class_permission"]
            except:
                pass

        return {
            "info": classes.get_class_all_info(),
            "classroom": classroom_in,
            "login_as": login_as,
            }

    @cherrypy.expose
    def id(self, *args, **kwargs):
        classes = cherrypy.request.classes
        if cherrypy.request.method == "GET":
            classes_id = []
            for c in classes.classes.values():
                classes_id.append(c["id"])
            return {"classes_id": classes_id}
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def price(self, *args, **kwargs):
        classes = cherrypy.request.classes
        if cherrypy.request.method == "GET":
            paid_class = []
            free_class = []
            for c in classes.classes.values():
                if c["permission"] == None:
                    free_class.append(c["id"])
                else:
                    paid_class.append(c["id"])
            return {"paid": paid_class, "free": free_class}
        else:
            raise cherrypy.HTTPError(404)

class PostRestView(View):
    _root = rest_config["url_root"] + "post/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        posts = meta.tables[Post.TABLE_NAME]

        if len(args) > 0:
            raise cherrypy.HTTPError(404)

        if cherrypy.request.method == "GET":
            ss = select([posts]).order_by(desc(posts.c.create_at))
            rst = conn.execute(ss)
            rows = rst.fetchall()

            return {"posts": [Post.mk_dict(row) for row in rows]}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            if not user["admin"]:
                raise cherrypy.HTTPError(401)

            self.check_key(data, ("title", "content", ))

            j = {
                "title": data["title"],
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
            user = self.check_login_u(kwargs)

            if not user["admin"]:
                raise cherrypy.HTTPError(401)

            self.check_key(kwargs, ("id", ))

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

class TeacherRestView(View):
    _root = rest_config["url_root"] + "teacher/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        teachers = meta.tables[Teacher.TABLE_NAME]
        teacherinfos = meta.tables[TeacherInfo.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if "teacher" in kwargs:
                teacher = self.check_login_teacher2(kwargs)
                return teacher
            else:
                user = self.check_login_u(kwargs)
                if not user["admin"]:
                    raise cherrypy.HTTPError(401)

                ss = select([teachers]).order_by(teachers.c.id)
                rst = conn.execute(ss)
                rows = rst.fetchall()

                return {"teachers": [Teacher.mk_dict(row) for row in rows]}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json

            user = self.check_login_u(data)
            if not user["admin"]:
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
                "class_permission": data["class_permission"],
                "summary": "",
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

            if "teacher" in data:
                user = self.check_login_teacher2(data)

                if "summary" in data:
                    stmt = teacherinfos.update().where(
                        teacherinfos.c.id==user["id"]).values(
                        summary=data["summary"])
                    conn.execute(stmt)
                    return {"success": True}
                elif "contact_link" in data:
                    if not isinstance(data["contact_link"], dict):
                        raise cherrypy.HTTPError(400)

                    stmt = teacherinfos.update().where(
                        teacherinfos.c.id==user["id"]).values(
                        contact_link=data["contact_link"])
                    conn.execute(stmt)
                    return {"success": True}
                else:
                    raise cherrypy.HTTPError(400)
            else:
                user = self.check_login_u(data)
                if not user["admin"]:
                    raise cherrypy.HTTPError(401)

                self.check_key(data, (
                    "userid",
                    "name",
                    "phone",
                    "class_permission",
                    "ext_area",
                    "whole_city",
                    "summary",
                    ))

                try:
                    ext_area = int(data["ext_area"])
                    whole_city = int(data["whole_city"])
                except:
                    raise cherrypy.HTTPError(400)

                json = {
                    "userid": data["userid"],
                    "name": data["name"],
                    "phone": data["phone"],
                    "class_permission": data["class_permission"],
                    "ext_area": ext_area,
                    "whole_city": whole_city,
                    "summary": data["summary"],
                    }

                if "password" in data:
                    json["password"] = data["password"]

                stmt = teachers.update().where(
                    teachers.c.id==data["tid"]).values(json)
                conn.execute(stmt)

                return {"success": True}

        elif cherrypy.request.method == "DELETE":
            user = self.check_login_u(kwargs)

            if not user["admin"]:
                raise cherrypy.HTTPError(401)

            ss = select([teachers.c.id]).where(teachers.c.id==kwargs["tid"])
            rst = conn.execute(ss)
            teacher_id = rst.fetchone()

            if not teacher_id:
                raise cherrypy.HTTPError(400,
                    f"Teacher id {kwargs['tid']} don't exist")

            adareas = meta.tables[AdArea.TABLE_NAME]
            adclasses = meta.tables[AdClass.TABLE_NAME]
            classrooms = meta.tables[Classroom.TABLE_NAME]

            # delete every model use teacher's id
            ds = adareas.delete().where(adareas.c.teacher==kwargs["tid"])
            conn.execute(ds)
            ds = adclasses.delete().where(adclasses.c.teacher==kwargs["tid"])
            conn.execute(ds)
            ds = classrooms.delete().where(classrooms.c.teacher==kwargs["tid"])
            conn.execute(ds)

            ds = teachers.delete().where(teachers.c.id==kwargs["tid"])
            conn.execute(ds)

            return {"success": True}
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
            teacher = self.check_login_teacher2(kwargs)

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

    # @cherrypy.expose
    # def password(self, *args, **kwargs):
    #     meta, conn = cherrypy.request.db
    #     key_mgr = cherrypy.request.key
    #     teachers = meta.tables[Teacher.TABLE_NAME]

    #     if cherrypy.request.method == "PUT":
    #         data = cherrypy.request.json
    #         teacher = self.check_login_teacher2(data)

    #         self.check_key(data, ("password", "newpassword", ))

    #         stmt = update(teachers).where(
    #             and_(teachers.c.id == teacher["id"],
    #                 teachers.c.password == data["password"])).values(
    #                     {"password": data["newpassword"]})
    #         ins = conn.execute(stmt)

    #         if ins.rowcount != 0:
    #             key_mgr.drop_key(data["tkey"])

    #             cherrypy.response.status = 201
    #             return {"success": True}
    #         else:
    #             raise cherrypy.HTTPError(400, ErrMsg.WRONG_PASSWORD)
    #     else:
    #         raise cherrypy.HTTPError(404)

class AdAreaRestView(View):
    _root = rest_config["url_root"] + "adarea/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        adareas = meta.tables[AdArea.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if "teacher" in kwargs:
                user = self.check_login_teacher2(kwargs)
                tid = user["id"]

                if "tid" in kwargs:
                    if user["type"] != User.ADMIN:
                        raise cherrypy.HTTPError(400)
                    try:
                        tid = int(kwargs["id"])
                    except:
                        raise cherrypy.HTTPError(400)

                ss = select([adareas]).where(
                    adareas.c.teacher == tid
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
                teacherinfos = meta.tables[TeacherInfo.TABLE_NAME]
                adclasses = meta.tables[AdClass.TABLE_NAME]

                try:
                    city = int(kwargs["city"])
                except:
                    raise cherrypy.HTTPError(400)

                if city == -1:
                    ss = select([
                        teacherinfos.c.name,
                        teacherinfos.c.id,
                        teacherinfos.c.phone,
                        teacherinfos.c.summary,
                        teacherinfos.c.contact_link,

                        adareas.c.city,
                        adareas.c.town,

                        adclasses.c.id.label("adclassid"),
                        adclasses.c.address,
                        adclasses.c.type,
                        adclasses.c.date,
                        adclasses.c.enddate,
                        adclasses.c.start_time,
                        adclasses.c.end_time,
                        adclasses.c.weekdays,
                        ])
                else:
                    ss = select([
                        teacherinfos.c.name,
                        teacherinfos.c.id,
                        teacherinfos.c.phone,
                        teacherinfos.c.summary,
                        teacherinfos.c.contact_link,

                        adareas.c.city,
                        adareas.c.town,

                        adclasses.c.id.label("adclassid"),
                        adclasses.c.address,
                        adclasses.c.type,
                        adclasses.c.date,
                        adclasses.c.enddate,
                        adclasses.c.start_time,
                        adclasses.c.end_time,
                        adclasses.c.weekdays,
                        ]).where(adareas.c.city==city)

                j1 = teacherinfos.outerjoin(
                    adareas, teacherinfos.c.id==adareas.c.teacher).outerjoin(
                    adclasses, teacherinfos.c.id==adclasses.c.teacher)
                ss = ss.select_from(j1)
                rst = conn.execute(ss)
                rows = rst.fetchall()

                if len(rows) == 0:
                    return []

                path = cherrypy.request.file_mgr.get_download_path()
                return {"teachers": [Teacher.mk_dict_adarea_adclass(row) for row in rows], "avatar": os.listdir(path + "avatar/")}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_teacher2(data)
            tid = user["id"]

            if "tid" in kwargs:
                if user["type"] != User.ADMIN:
                    raise cherrypy.HTTPError(400)
                try:
                    tid = int(kwargs["id"])
                except:
                    raise cherrypy.HTTPError(400)

            self.check_key(data, ("city", "town", ))

            try:
                city = int(data["city"])
                town = int(data["town"])
            except:
                raise cherrypy.NOT_INT.format("city or town")

            ss = select([adareas.c.id]).where(
                adareas.c.teacher==tid
                )
            rst = conn.execute(ss)
            rows = rst.fetchall()

            if len(rows) >= ADVERTISE_LIMIT + user["ext_area"]:
                raise cherrypy.HTTPError(400, ErrMsg.LIMITED_ADVERTISE)

            j = {
                "teacher": tid,
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
            user = self.check_login_teacher2(kwargs)
            tid = user["id"]

            if "tid" in kwargs:
                if user["type"] != User.ADMIN:
                    raise cherrypy.HTTPError(400)
                try:
                    tid = int(kwargs["id"])
                except:
                    raise cherrypy.HTTPError(400)

            try:
                aid = int(kwargs["aid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format(aid))

            # delete answer
            ds = adareas.delete().where(and_(
                adareas.c.id==aid,
                adareas.c.teacher==tid))
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
            if "teacher" in kwargs:
                try:
                    teacher = self.check_login_teacher2(kwargs)
                    tid = teacher["id"]
                except:
                    user = self.check_login_u(kwargs)
                    if not user["admin"]:
                        raise cherrypy.HTTPError(401)

                    self.check_key(kwargs, ("tid", ))
                    tid = kwargs["tid"]

                ss = select([adclasses]).where(
                    adclasses.c.teacher == tid
                    )
                rst = conn.execute(ss)
                rows = rst.fetchall()

                if len(rows) == 0:
                    return {"adclasses": []}
                json = {
                    "adclasses": [AdClass.mk_dict(row) for row in rows],
                    }
                return json
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            teacher = self.check_login_teacher2(data)

            self.check_key(data, (
                "address",
                "type",
                "date",
                "enddate",
                "start_time",
                "end_time",
                "weekdays",))

            date_ = self.parsedate(data["date"])
            enddate = self.parsedate(data["enddate"])

            if not date_:
                raise cherrypy.HTTPError(400, "Date format wrong")
            if not enddate:
                enddate = None

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
                "enddate": enddate,
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
            try:
                teacher = self.check_login_teacher(kwargs)
                tid = teacher["id"]
            except:
                user = self.check_login_u(kwargs)
                if not user["admin"]:
                    raise cherrypy.HTTPError(401)

                self.check_key(kwargs, ("tid", ))
                tid = kwargs["tid"]

            try:
                aid = int(kwargs["aid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("aid"))

            # delete answer
            ds = adclasses.delete().where(and_(
                adclasses.c.id == aid,
                adclasses.c.teacher == tid))
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
        "tools.filetool.on": True,
        "tools.clsromtool.on": True,
        }

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            if "teacher" in kwargs:
                user = self.check_login_teacher2(kwargs)

                if "ids[]" in kwargs:
                    ss = select([users.c.userid, users.c.id]).where(
                        users.c.id.in_(kwargs["ids[]"]))
                    rst = conn.execute(ss)
                    rows = rst.fetchall()

                    userids = {}
                    for row in rows:
                        userids[row["id"]] = row["userid"]
                    return userids

                ss = select([classrooms]).where(
                    classrooms.c.teacher==user["id"])
                rst = conn.execute(ss)
                rows = rst.fetchall()

                return [Classroom.mk_dict(row) for row in rows]
            else:
                user = self.check_login_u(kwargs)

                ss = select([classrooms]).where(
                    classrooms.c.students_cid.any(user["id"]))
                rst = conn.execute(ss)
                rows = rst.fetchall()

                return [Classroom.mk_info(row, user["id"]) for row in rows]

        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            teacher = self.check_login_teacher2(data)

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
                userid = data["students_cid"].index(row["userid"])
                data["students_cid"][userid] = row["id"]

            json = {
                "teacher": teacher["id"],
                "name": data["name"],
                "students_name": data["students_name"],
                "students_cid": data["students_cid"],
                "students_sid": data["students_sid"],
                "type": data["type"],
                }

            folder = uuid()

            clsrm_folder = os.path.join(
                cherrypy.request.file_mgr.get_download_path(),
                str(folder))
            os.mkdir(clsrm_folder)
            os.mkdir(path_join(clsrm_folder, "teacher"))
            os.mkdir(path_join(clsrm_folder, "form"))
            json["folder"] = folder

            ins = classrooms.insert()
            rst = conn.execute(ins, json)

            if rst.is_insert:
                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            teacher = self.check_login_teacher2(data)

            self.check_key(data, ("clsid", ))
                # "name",
                # "students_name",
                # "students_cid",
                # "students_sid",

            json = {}

            if "name" in data:
                json["name"] = data["name"]
            if "students_name" in data:
                self.check_key(data, ("students_cid", "students_sid", ))

                if not isinstance(data["students_name"], list):
                    raise charrypy.HTTPError(400,
                        ErrMsg.NOT_LIST.format("students_name"))
                if not isinstance(data["students_cid"], list):
                    raise charrypy.HTTPError(400,
                        ErrMsg.NOT_LIST.format("students_cid"))
                if not isinstance(data["students_sid"], list):
                    raise charrypy.HTTPError(400,
                        ErrMsg.NOT_LIST.format("students_sid"))

                ss = select([users.c.id, users.c.userid]).where(
                    users.c.userid.in_(data["students_cid"]))
                rst = conn.execute(ss)
                rows = rst.fetchall()

                for row in rows:
                    userid = data["students_cid"].index(row["userid"])
                    data["students_cid"][userid] = row["id"]

                json["students_name"] = data["students_name"],
                json["students_cid"] = data["students_cid"],
                json["students_sid"] = data["students_sid"],
            if "links" in data:
                if not isinstance(data["links"], list):
                    raise charrypy.HTTPError(400,
                        ErrMsg.NOT_LIST.format("links"))

                json["links"] = data["links"]

            if len(json) == 0:
                return {"success": None}

            stmt = update(classrooms).where(and_(
                classrooms.c.id == data["clsid"],
                classrooms.c.teacher == teacher["id"])).values(json)
            rst = conn.execute(stmt)

            if rst.rowcount > 0:
                return {"success": json}
            else:
                raise cherrypy.HTTPError(400)
        elif cherrypy.request.method == "DELETE":
            teacher = self.check_login_teacher2(kwargs)
            self.check_key(kwargs, ("clsid", ))

            ds = classrooms.delete().where(classrooms.c.id == kwargs["clsid"])
            rst = conn.execute(ds)

            return {"success": True}
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def student_permission(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]

        if cherrypy.request.method == "GET":
            self.check_key(kwargs, ("class", ))
            clsr_id = None

            # test user login
            try:
                user = self.check_login_u(kwargs)

                ss = select([classrooms.c.id, classrooms.c.name]).where(and_(
                    classrooms.c.students_cid.any(user["id"]),
                    classrooms.c.type==kwargs["class"]
                    ))
                rst = conn.execute(ss)
                rows = rst.fetchall()
                if rows:
                    return {
                        "class": [{"id": row["id"], "name": row["name"]} 
                            for row in rows],
                        "success": True,
                        "key": "user",
                        }
                return {"success": False, "reason": "not in class"}
            except:
                pass

            #user login failed try teacher
            teacher = self.check_login_teacher(kwargs)
            teachers = meta.tables[Teacher.TABLE_NAME]

            ss = select([teachers.c.class_permission]).where(
                teachers.c.id==teacher["id"])
            rst = conn.execute(ss)
            row = rst.fetchone()

            if kwargs["class"] not in row["class_permission"]:
                return {"success": False, "reason": "no permission"}

            return {
                "permission": row["class_permission"],
                "success": True,
                "key": "teacher",
                }
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def progress(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]
        clsrom_mgr = cherrypy.request.clsrom

        if cherrypy.request.method == "GET":
            cls_per_key = kwargs["cls_per_key"]
            cls_per_key = clsrom_mgr.get_cls_per_key(cls_per_key)
            if not cls_per_key:
                raise cherrypy.HTTPError(400)

            type_ = cls_per_key["type"]
            if type_ == "user":
                clsr_id = cls_per_key["clsr_id"]
                ss = select([classrooms.c.progress]).where(
                    classrooms.c.id==clsr_id)
                rst = conn.execute(ss)
                row = rst.fetchone()
                return row["progress"]
            return None

        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def check_folder(self, *args, **kwargs):
        file_mgr = cherrypy.request.file_mgr

        if cherrypy.request.method == "GET":
            try:
                self.check_login_u(kwargs)
            except:
                self.check_login_teacher(kwargs)

            self.check_key(kwargs, ("folder", ))

            path = cherrypy.request.file_mgr.get_download_path()
            path += kwargs["folder"]

            if not os.path.isdir(path):
                raise cherrypy.HTTPError(400)

            if "student" in kwargs:
                files = {}
                if "cid" in kwargs:
                    for file in os.listdir(path):
                        if file.startswith(kwargs["cid"]):
                            filename = path_join(path, file)
                            try:
                                files[filename] = file_mgr[filename]
                            except:
                                files[filename] = {
                                    "updated_time": None,
                                    "lastupdate": None,
                                    }
                else:
                    for file in os.listdir(path):
                        filename = path_join(path, file)
                        try:
                            files[filename] = file_mgr[filename]
                        except:
                            files[filename] = {
                                "updated_time": None,
                                "lastupdate": None,
                                }
                return files
            else:
                return os.listdir(path + "/teacher")
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

    @cherrypy.expose
    def form(self, *args, **kwargs):
        clsrom_mgr = cherrypy.request.clsrom

        if cherrypy.request.method == "GET":
            teacher = self.check_login_teacher2(kwargs)

            self.check_key(kwargs, ("folder", ))

            # if ("answer" in kwargs) and ("type" in kwargs):
            #     return cherrypy.request.classes.get_answer(kwargs["type"])
            if ("evaluation" in kwargs) and ("type" in kwargs):
                return cherrypy.request.classes.get_evals(kwargs["type"])
            return clsrom_mgr.get_classroom(kwargs["folder"])
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_u(data)
            
            self.check_key(data, (
                "form",
                "folder",
                "answer",
                ))

            clsrom_mgr.new_answer(
                data["folder"],
                user["id"],
                data["form"],
                data["answer"])

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
        "tools.filetool.on": True,
        }

    @cherrypy.expose
    def homework(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]
        file_mgr = cherrypy.request.file_mgr
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

            path = file_mgr.get_download_path()
            fileformat = path + "{folder}/{uid}_{filename}"

            homework = kwargs["homwork"]
            if not isinstance(homework, list):
                homework = [homework]

            sections = {None: 0}
            for file in homework:
                try:
                    if not re.fullmatch(PY_FILE_RE, file.filename):
                        continue

                    filename = file.filename
                    section = filename[:filename.find("-")]
                    try:
                        sections[section] += 1
                    except:
                        sections[section] = 1

                    filename.replace("test", "")

                    filename = fileformat.format(
                        folder=row["folder"],
                        uid=user["id"],
                        filename=filename)

                    file_mgr.write_file_from_file(filename, file)
                except:
                    if os.path.isfile(filename):
                        os.remove(filename)

            biggest = None
            for section, value in sections.items():
                if value > sections[biggest]:
                    biggest = section
                
            raise cherrypy.HTTPRedirect(
                f"/classattend?class={kwargs['clsroomid']}&section={biggest}")
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def report(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        reports = meta.tables[Report.TABLE_NAME]
        file_mgr = cherrypy.request.file_mgr

        if cherrypy.request.method == "POST":
            user = self.check_login_u(kwargs)

            self.check_key(kwargs, (
                "file",
                "rid",
                ))

            try:
                rid = int(kwargs["rid"])
            except:
                raise cherrypy.HTTPRedirect("/report")

            ss = select([reports.c.id]).where(reports.c.id==kwargs["rid"])
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPRedirect("/report")

            path = file_mgr.get_download_path()
            fileformat = "report/{rid}.{filetype}"

            try:
                if "report" not in os.listdir(path):
                    os.mkdir(path_join(path, "reaport/"))
                file = kwargs["file"]

                filename = file.filename
                filetype = filename[filename.find(".") + 1:]

                filename = fileformat.format(
                    rid=row["id"],
                    filetype=filetype)

                file_mgr.write_file_from_file(filename, file)
            except:
                if os.path.isfile(path + filename):
                    os.remove(path + filename)
                raise cherrypy.HTTPRedirect("/report")

            stmt = update(reports).where(and_(
                reports.c.id == rid,
                reports.c.writer == user["id"]
                )).values(file="downloads/" + filename)
            ins = conn.execute(stmt)

            if ins.rowcount != 0:
                cherrypy.response.status = 201
                raise cherrypy.HTTPRedirect("/report")
            else:
                raise cherrypy.HTTPRedirect("/report")

    @cherrypy.expose
    def teacherfile(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        classrooms = meta.tables[Classroom.TABLE_NAME]
        file_mgr = cherrypy.request.file_mgr

        if cherrypy.request.method == "POST":
            teacher = self.check_login_teacher2(kwargs)

            self.check_key(kwargs, (
                "annoce",
                "clsrid",
                ))
            
            try:
                clsrid = int(kwargs["clsrid"])
            except:
                raise cherrypy.HTTPError(404)

            ss = select([classrooms.c.folder]).where(and_(
                classrooms.c.id==clsrid,
                classrooms.c.teacher==teacher["id"]))
            rst = conn.execute(ss)
            row = rst.fetchone()

            if not row:
                raise cherrypy.HTTPError(404)

            path = os.path.join(
                file_mgr.get_download_path(),
                row["folder"],
                "teacher"
                )

            try:
                if not os.path.exists(path):
                    os.mkdir(path)

                filename = path + "/" + kwargs["annoce"].filename
                file_mgr.write_file_from_file(filename, kwargs["annoce"])
            except:
                if os.path.isfile(filename):
                    os.remove(filename)
                raise cherrypy.HTTPRedirect("/report")

            raise cherrypy.HTTPRedirect("/teacher")
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
                        AND NOT id = ANY(present);""".replace("id",
                            str(user["id"]))

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

class ReportRestView(View):
    _root = rest_config["url_root"] + "report/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        reports = meta.tables[Report.TABLE_NAME]
        users = meta.tables[User.TABLE_NAME]

        if cherrypy.request.method == "GET":
            j = join(reports, users)
            ss = select([reports, users.c.nickname]).select_from(j)
            rst = conn.execute(ss)
            rows = rst.fetchall()

            return [Report.mk_dict(row) for row in rows]
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            self.check_key(data,(
                "title",
                "summary",
                ))

            json = {
                "title": data["title"],
                "summary": data["summary"],
                "writer": user["id"],
                }
            ins = reports.insert().returning(reports.c.id)
            rst = conn.execute(ins, json)

            if rst.is_insert:
                cherrypy.response.status = 201

                return {"success": True, "rid": rst.fetchone()["id"]}
            else:
                 raise cherrypy.HTTPError(503)
        elif cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            if not user["admin"]:
                raise cherrypy.HTTPError(401)
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def fileattach(self, *args, **kwargs):
        meta, conn = cherrypy.request.db
        reports = meta.tables[Report.TABLE_NAME]

        if cherrypy.request.method == "PUT":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            self.check_key(data, (
                "rid",
                "file",
                ))

            try:
                rid = int(data["rid"])
            except:
                raise cherrypy.HTTPError(400, ErrMsg.NOT_INT.format("qid"))

            # TODO: if file exist then the file upload THIS TIME will be delete

            # TODO: check file exist

            stmt = update(reports).where(and_(
                reports.c.id == rid,
                reports.c.writer == user["id"]
                )).values(file=data["file"])
            ins = conn.execute(stmt)

            if ins.rowcount != 0:
                cherrypy.response.status = 201
                return {"success": True}
            else:
                raise cherrypy.HTTPError(400,
                    ErrMsg.WRONG_WRITER.format(str(uid)))
        else:
            raise cherrypy.HTTPError(404)

class PresentationRestView(View):
    _root = rest_config["url_root"] + "presentation/"

    @cherrypy.expose
    def index(self, *args, **kwargs):
        file_mgr = cherrypy.request.file_mgr

        if cherrypy.request.method == "GET":
            success = file_mgr.read_sys_file("presentation.html")
            return {"success": success}
        elif cherrypy.request.method == "POST":
            data = cherrypy.request.json
            user = self.check_login_u(data)

            if not user["admin"]:
                raise cherrypy.HTTPError(401)

            self.check_key(data, ("presentation", ))

            success = file_mgr.write_sys_file("presentation.html",
                data["presentation"])
            return {"success": success}
        else:
            raise cherrypy.HTTPError(400)

