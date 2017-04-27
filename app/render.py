import cherrypy
import os
import jinja2
from uuid import uuid1 as uuid
import requests

# template_dir = os.path.join(os.path.dirname(__file__), 'template')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader("html/template"))
abs_cwd = os.path.join(os.getcwd(), os.path.dirname(__file__))

def render(src, params={}):
    # print(os.getcwd())
    t = jinja_env.get_template(src)
    return t.render(params)

render_config = {
    "url_root":"/",
    }

class UserCaseHandler(object):
    _root = "/"
    _cp_config = {
        "tools.classestool.on": True,
        "tools.keytool.on": True,
        "tools.emailvalidtool.on": True,
        # "tools.caching.on": True,
        # "tools.caching.delay": 3600,
        }

    @staticmethod
    def error_404(status, message, traceback, version):
        return render("404.html")

    @cherrypy.expose
    def index(self):
        return render("index.html")

    @cherrypy.expose
    def question(self, file1=None, file2=None, file3=None, **kwargs):
        if cherrypy.request.method == "POST":
            key_mgr = cherrypy.request.key
            cookie = cherrypy.request.cookie
            try:
                key = str(cookie["key"].value)
            except:
                raise cherrypy.HTTPRedirect("/")

            key_valid = key_mgr.get_key(key)
            if not key_valid[0]:
                raise cherrypy.HTTPRedirect("/")

            if (not file1) and (not file2) and (not file3):
                raise cherrypy.HTTPRedirect("/question")

            classes = cherrypy.request.classes
            path = classes.get_download_path()
            size = 0
            fileformat = path + "{id}_{filename}"

            filesname = []
            try:
                id_ = str(uuid())
                filename = fileformat.format(id=id_, filename=file1.filename)
                filesname.append(filename)

                f = open(filename, "wb")
                while True:
                    data = file1.file.read(8192)
                    if not data:
                        break
                    size += len(data)
                    f.write(data)
                f.close()
            except:
                if os.path.isfile(filename):
                    os.remove(filename)
                filesname.pop()

            try:
                id_ = str(uuid())
                filename = fileformat.format(id=id_, filename=file2.filename)
                filesname.append(filename)

                f2 = open(filename, "wb")
                while True:
                    data = file2.file.read(8192)
                    if not data:
                        break
                    size += len(data)
                    f2.write(data)
                f2.close()
            except:
                if os.path.isfile(filename):
                    os.remove(filename)
                filesname.pop()

            try:
                id_ = str(uuid())
                filename = fileformat.format(id=id_, filename=file3.filename)
                filesname.append(filename)

                f3 = open(filename, "wb")
                while True:
                    data = file3.file.read(8192)
                    if not data:
                        break
                    size += len(data)
                    f3.write(data)
                f3.close()
            except:
                if os.path.isfile(filename):
                    os.remove(filename)
                filesname.pop()

            filesname = [f.replace(path, "/downloads/") for f in filesname]
                    
            # link file to question
            r = None
            cookie = cherrypy.request.cookie
            data = {
                "key":key,
                "filepath":filesname
            }

            if "questionkey" in kwargs:
                id_ = int(kwargs["questionkey"])
                data["qid"] = id_

                r = requests.post("http://0.0.0.0/rest/1/question/fileattach", json=data)
                print(r.text, id_)
            elif "answerkey" in kwargs:
                id_ = str(kwargs["answerkey"])
                data["aid"] = id_

                r = requests.post("http://0.0.0.0/rest/1/answer/fileattach", json=data)
            else:
                raise cherrypy.HTTPRedirect("/question")

            if r.status_code == 400:
                for i in filesname:
                    if os.path.isfile(i):
                        os.remove(i)

            raise cherrypy.HTTPRedirect("/question")

        else:
            # return "GET"
            return render("question.html")
        # return cherrypy.request.method

    @cherrypy.expose
    def about(self):
        return render("about.html")

    @cherrypy.expose
    def mission(self):
        return render("mission.html")

    @cherrypy.expose
    def classes(self):
        return render("viewclasses.html")

    @cherrypy.expose
    def news(self):
        return render("news.html")

    # @cherrypy.expose
    # def hourofcode(self):
    #     raise cherrypy.HTTPRedirect("/class/c/hourofcode")

    @cherrypy.expose
    def scratch(self):
        raise cherrypy.HTTPRedirect("/class/c/scratch_1")

    @cherrypy.expose
    def resource(self):
        return render("resource.html")

    @cherrypy.expose
    def classattend(self):
        return render("classattend.html")

    @cherrypy.expose
    def video(self, key, video=None, file="", nextvid="", button="看答案", nextbutton="看問題"):
        access_deny = """
        <head>
            <title>Access Deny</title>
            <style>
                body, html {width: 100%;height: 100%}
                .wrapper {width: 100%;height: 100%;text-align: center}
                .wrapper:after {content: "";height: 100%;
                vertical-align: middle;display: inline-block;margin-right: -10px}
                .container {vertical-align: middle;display: inline-block}
                h1 {font-size: 2.618em;color:white}
            </style>
        </head>
        <body bgcolor="black">
            <section class="wrapper">
                <div class="container">
                    <h1>Access Deny</h1>
                </div>
            </section>
        </body>
        </html>
        """

        key_mgr = cherrypy.request.key

        key_valid = key_mgr.get_key(key)
        if not key_valid[0]:
            return access_deny
        uid = key_valid[1]

        return render("video.html", {
            "video": video,
            "file": file.split(";"),
            "next": nextvid,
            "button": button,
            "nextbutton": nextbutton,
            })

    @cherrypy.expose
    def active(self, ekey):
        cookie = cherrypy.request.cookie
        try:
            key = str(cookie["key"].value)
        except:
            raise cherrypy.HTTPRedirect("/")

        r = requests.put("http://0.0.0.0/rest/1/user/emailvalid", json={
            "key": key, "ekey": ekey})
        if r.status_code != 201:
            raise cherrypy.HTTPRedirect("/")

        return render("active.html")

    @cherrypy.expose
    def mission(self):
        return render("mission.html")

    @cherrypy.expose
    def report(self):
        return render("report.html")

    @cherrypy.expose
    def presentation(self):
        return render("presentation.html")

    @cherrypy.expose
    def newemail(self):
        return render("newemail.html")

class ClassHandler(object):
    _root = "/class/"
    _cp_config = {
        "tools.classestool.on": True,
        }

    @cherrypy.expose
    def c(self, class_id):
        classes = cherrypy.request.classes
        subject = classes.get_subject_name(class_id)
        if not subject:
            raise cherrypy.HTTPError(404)
        return render("class.html", {"class_id": class_id, "subject": subject})

class TeacherHandler(object):
    _root = "/teacher/"
    _cp_config = {
        "tools.classestool.on": True,
        "tools.keytool.on": True,
        }

    @cherrypy.expose
    def index(self):
        return render("teacher/index.html")

    @cherrypy.expose
    def login(self):
        cookie = cherrypy.request.cookie
        try:
            key = str(cookie["teacher-key"].value)
        except:
            key = ""

        key_mgr = cherrypy.request.key

        key_valid = key_mgr.get_key(key)
        if key_valid[0]:
            raise cherrypy.HTTPRedirect("/teacher/")

        return render("teacher/login.html")

    @cherrypy.expose
    def advertise(self):
        return render("teacher/advertise.html")






