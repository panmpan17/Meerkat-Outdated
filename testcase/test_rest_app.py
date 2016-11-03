import unittest
import os
import requests
import threading
import time
import hashlib
import random

import cherrypy
from app.rest import rest_config, ErrMsg
from main import App
from app.model import User, Question, Answer
from sqlalchemy.sql import select

from pprint import pprint

serverthread = None
cherryserver = None

def hash256(string):
    return hashlib.sha256(string.encode()).hexdigest()

class CharryTestInfo:
    HOSTNAME = "localhost"
    PORT = 8080
    DB_FILE = ":memory:"

def setUpModule():
    global serverthread, cherryserver

    if os.path.isfile(CharryTestInfo.DB_FILE):
        os.remove(CharryTestInfo.DB_FILE)

    cherryserver = App()
    def begin():
        cherryserver.start()

    serverthread = threading.Thread(target=begin)
    serverthread.start()

    time.sleep(1)
    print("Complete setup...............")

def tearDownMoudle():
    global serverthread, cherryserver
    cherrypy.engine.exit()
    if os.path.isfile(CharryTestInfo.DB_FILE):
        os.remove(CharryTestInfo.DB_FILE)

    serverthread.join()
    serverthread = None
    cherryserver = None

def http_errmsg(http_str):
    p1 = http_str.find("<p>") + len("<p>")
    return http_str[p1:http_str.find("</p>", p1)]

class RestfulTestCase(unittest.TestCase):
    def setUp(self):
        self.url = "http://" + CharryTestInfo.HOSTNAME + ":" +\
            str(CharryTestInfo.PORT) + rest_config["url_root"]

    def test_a_user(self):
        meta, conn = cherrypy.tools.dbtool.get_plugin().get_meta_conn()
        users = meta.tables[User.TABLE_NAME]
        
        # r = requests.get(self.url + "user/")
        # self.assertEqual(r.status_code, 200)

        print ("-----------User create test------------")
        # fail

        # no params
        r = requests.post(self.url + "user/", json={})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("users"))

        # 'users' type error
        r = requests.post(self.url + "user/", json={"users":""})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_LIST.format("users"))

        r = requests.post(self.url + "user/", json={"users":123})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_LIST.format("users"))

        # type in 'users' error
        r = requests.post(self.url + "user/", json={"users":[1, 2, 3]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_DICT)

        r = requests.post(self.url + "user/", json={"users":["1", "2", "3"]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_DICT)

        # dict in 'users' wrong params
        r = requests.post(self.url + "user/", json={"users":[{}]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_DICT)

        r = requests.post(self.url + "user/", json={"users":[{"notaparam":1}]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.UNKNOWN_PARAM.format("notaparam"))

        r = requests.post(self.url + "user/", json={"users":[{"a":1}]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.UNKNOWN_PARAM.format("a"))

        # dict's param missing
        r = requests.post(self.url + "user/", json={"users":[{"userid":None}]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("userid"))

        r = requests.post(self.url + "user/", json={"users":[{"userid":"1"}]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("password"))

        # wrong integer
        json = [dict(userid="michaelpan", password="password", email="pan@mail.com",
            birth_year="notInt") ]
        json[0]["password"] = hash256(json[0]["password"])
        r = requests.post(self.url + "user/", json={"users":json})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_INT.format("birth_year"))

        # This one is success example
        json = [dict(userid="michaelpan", password="password", email="pan@mail.com",
            birth_year=2000, nickname="mime_pan")]
        json[0]["password"] = hash256(json[0]["password"])
        r = requests.post(self.url + "user/", json={"users":json})
        self.assertEqual(r.status_code, 201)

        # store it use it latter
        userid = "michaelpan"
        password = json[0]["password"]

        lastid = r.json()['lastrowid']
        ss = select([users]).where(users.c.id == lastid)
        rst = conn.execute(ss)
        rows = rst.fetchall()
        self.assertEqual(len(rows), 1)
        for k, v in json[0].items():
            self.assertEqual(rows[0][k], v)

        # userid can't repeat
        r = requests.post(self.url + "user/", json={"users":json})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.USERID_REPEAT)

        print ("-----------Session key------------")
        r = requests.post(self.url + "logon/", json={})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("userid or password"))

        r = requests.post(self.url + "logon/", json={"userid":userid})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("userid or password"))

        r = requests.post(self.url + "logon/", json={"password":password})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("userid or password"))

        r = requests.post(self.url + "logon/", json={"userid":userid,"password":"wrongpassword"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.WRONG_PASSWORD)

        r = requests.post(self.url + "logon/", json={"userid":userid,"password":password})
        self.assertEqual(r.status_code, 200)
        # print("session key: " + r.json()["key"])

    def test_b_question(self):
        # meta, conn = cherrypy.tools.dbtool.get_plugin().get_meta_conn()
        # users = meta.tables[User.TABLE_NAME]
        # questions = meta.tables[Question.TABLE_NAME]

        userid = "michaelpan"
        password = hash256("password")
        r = requests.post(self.url + "logon/", json={"userid":userid,"password":password})
        self.assertEqual(r.status_code, 200)
        key = r.json()["key"]
        uid = r.json()["lastrowid"]

        print("-----------Question create test------------")
        
        #
        r = requests.post(self.url + "question/", json={})
        self.assertEqual(r.status_code, 401)
        # self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("question_json"))

        r = requests.post(self.url + "question/", json={"key":key, "unknown":1})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("question_json"))

        q_json = {"question_json":{"title":"!"}, "key":key}
        r = requests.post(self.url + "question/", json=q_json)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("content"))

        q_json["question_json"]["content"] = """1\n2\n3\n"""
        r = requests.post(self.url + "question/", json=q_json)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("type"))

        q_json["question_json"]["type"] = 0
        r = requests.post(self.url + "question/", json=q_json)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("writer"))

        q_json["question_json"]["writer"] = -1
        r = requests.post(self.url + "question/", json=q_json)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.UNKNOWN_ID.format("-1"))

        q_json["question_json"]["writer"] = uid
        r = requests.post(self.url + "question/", json=q_json)
        self.assertEqual(r.status_code, 201)

        print("-----------Question get test------------")

        r = requests.get(self.url + "question/", params={"id":"a"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_INT.format("a"))

        r = requests.get(self.url + "question/", params={"id":-1})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.UNKNOWN_ID.format(-1))

        r = requests.get(self.url + "question/", params={"id":"1"})
        self.assertEqual(r.status_code, 200)

        # get all

        for i in range(14):
            q_json["question_json"]["writer"] = uid

            q_json["question_json"]["title"] = str(i)
            q_json["question_json"]["content"] = str(i)

            r = requests.post(self.url + "question/", json=q_json)
            self.assertEqual(r.status_code, 201)

        r = requests.get(self.url + "question/", params={})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 10)
        self.assertEqual(r.json()["pages"], 2)

        r = requests.get(self.url + "question/", params={"page":0})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 10)
        self.assertEqual(r.json()["pages"], 2)

        r = requests.get(self.url + "question/", params={"page":1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 5)
        self.assertEqual(r.json()["pages"], 2)

        r = requests.get(self.url + "question/", params={"page":10000})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 10)
        self.assertEqual(r.json()["pages"], 2)

        # file upload attach testing
        q_json = {
            "title": "File Attach",
            "content": "favicon.ico",
            "writer": uid,
            "type": 0
        }
        r = requests.post(self.url + "question/", json={"question_json": q_json, "key": key})
        self.assertEqual(r.status_code, 201)

        qid = r.json()["question_key"]
        file_path = "/downloads/f81844b4-70cf-11e6-aa56-28cfe91c3f5f_Photo on 10-22-15Thursday at 10.30.png"
        json = {
            "key": key,
            "qid": qid,
            "filepath": [file_path, file_path],
        }
        r = requests.post(self.url + "question/fileattach", json=json)
        self.assertEqual(r.status_code, 201)

        # check file is linked
        r = requests.get(self.url + "question/", params={"id":qid})
        self.assertEqual(r.status_code, 200)
        print(r.json())
        self.assertEqual(r.json()["file1"], file_path)
        self.assertEqual(r.json()["file2"], file_path)

        print("-----------Another User test------------")

        json = [dict(userid="testuser", password="password", email="test@mail.com",
            birth_year=2005, nickname="TEST")]
        json[0]["password"] = hash256(json[0]["password"])
        r = requests.post(self.url + "user/", json={"users":json})
        self.assertEqual(r.status_code, 201)
        uid_2th = r.json()["lastrowid"]
        key_2th = r.json()["key"]

        q_json = {
            "type": 0,
            "writer": uid_2th,
            "title": "Title",
            "content": "Content",
        }

        r = requests.post(self.url + "question/", json={"key": key_2th, "question_json": q_json})
        self.assertEqual(r.status_code, 201)
        qid = r.json()["question_key"]

        for i in range(3):
            q_json["type"] = 1
            q_json["title"] = str(i)
            q_json["content"] = str(i)

            r = requests.post(self.url + "question/", json={"key": key_2th, "question_json": q_json})
            self.assertEqual(r.status_code, 201)

        print("-----------Question update test------------")

        json = {"key": key, "qid": 10, "solved": "True"}
        r = requests.put(self.url + "question/", json=json)
        self.assertEqual(r.status_code, 201)

        json["qid"] = 11
        r = requests.put(self.url + "question/", json=json)
        self.assertEqual(r.status_code, 201)

        json["qid"] = 12
        r = requests.put(self.url + "question/", json=json)
        self.assertEqual(r.status_code, 201)

        json = {"key": key, "qid": 11, "solved": "False"}
        r = requests.put(self.url + "question/", json=json)
        self.assertEqual(r.status_code, 201)

        json = {"key": key, "qid": qid + 2, "solved": "True"}
        r = requests.put(self.url + "question/", json=json)
        self.assertEqual(r.status_code, 201)

        json = {"key": key_2th, "qid": qid + 1, "solved": "True"}
        r = requests.put(self.url + "question/", json=json)
        self.assertEqual(r.status_code, 201)

        print("-----------Question select test------------")

        r = requests.get(self.url + "question/", params = {"writer": uid})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 10)

        r = requests.get(self.url + "question/", params = {"writer": uid, "page": 1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 6)

        r = requests.get(self.url + "question/", params = {"writer": uid_2th})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 4)

        r = requests.get(self.url + "question/", params = {"solved": "True"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 3)
        questions = r.json()["questions"]

        for q in questions:
            self.assertEqual(q["solved"], True)

        r = requests.get(self.url + "question/", params = {"solved": "False"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 10)
        questions = r.json()["questions"]

        r = requests.get(self.url + "question/", params = {"solved": "False", "page": 1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 7)
        questions += r.json()["questions"]
        
        for q in questions:
            self.assertEqual(q["solved"], False)


        r = requests.get(self.url + "question/", params = {"type": 1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 3)
        questions = r.json()["questions"]

        for q in questions:
            self.assertEqual(q["type"], 1)


        r = requests.get(self.url + "question/", params = {"type": 0})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 10)
        questions = r.json()["questions"]

        r = requests.get(self.url + "question/", params = {"type": 0, "page": 1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["questions"]), 7)
        questions += r.json()["questions"]

        for q in questions:
            self.assertEqual(q["type"], 0)



    def test_c_answer(self):
        print ("-----------Answer create test------------")

        userid = "michaelpan"
        password = hash256("password")
        r = requests.post(self.url + "logon/", json={"userid":userid,"password":password})
        key = r.json()["key"]
        uid = r.json()["lastrowid"]

        q_json = {
            "title": "Question",
            "content": "waiting for answer",
            "writer": uid,
            "type": 0
        }
        r = requests.post(self.url + "question/", json={"question_json": q_json, "key": key})
        self.assertEqual(r.status_code, 201)
        qid = r.json()["question_key"]

        r = requests.post(self.url + "answer/", json={})
        self.assertEqual(r.status_code, 401)

        r = requests.post(self.url + "answer/", json={"key": ""})
        self.assertEqual(r.status_code, 401)

        r = requests.post(self.url + "answer/", json={"key": key})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("answer_json"))

        r = requests.post(self.url + "answer/", json={"key": key, "answer_json": ""})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_DICT)

        answer_json = {}
        r = requests.post(self.url + "answer/", json={"key": key, "answer_json": answer_json})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.NOT_DICT)
        
        answer_json = {"content":"answer\nline 2"}
        r = requests.post(self.url + "answer/", json={"key": key, "answer_json": answer_json})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("writer"))
        
        answer_json["writer"] = -1
        r = requests.post(self.url + "answer/", json={"key": key, "answer_json": answer_json})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.MISS_PARAM.format("answer_to"))

        answer_json["answer_to"] = -2
        r = requests.post(self.url + "answer/", json={"key": key, "answer_json": answer_json})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.UNKNOWN_ID.format(-1))

        answer_json["writer"] = uid
        r = requests.post(self.url + "answer/", json={"key": key, "answer_json": answer_json})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(http_errmsg(r.text), ErrMsg.UNKNOWN_ID.format(-2))



        answer_json["answer_to"] = qid
        r = requests.post(self.url + "answer/", json={"key": key, "answer_json": answer_json})
        self.assertEqual(r.status_code, 201)

        answer_json["answer_to"] = qid
        r = requests.post(self.url + "answer/", json={"key": key, "answer_json": answer_json})
        self.assertEqual(r.status_code, 201)

        print ("-----------Answer get test------------")
        r = requests.get(self.url + "answer/", params={"qid": qid})
        self.assertEqual(r.status_code, 201)

        








