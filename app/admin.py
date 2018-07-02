import cherrypy
import jinja2
from app.model import User, Post
import os
import requests

#from sqlalchemy import desc
from sqlalchemy.sql import select, and_
#from sqlalchemy.exc import IntegrityError

jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader("html/template"))

def render(src, params={}):
    # print(os.getcwd())
    t = jinja_env.get_template(src)
    return t.render(params)

class AdminHandler(object):
    _root = "/admin/"
    _cp_config = {
        "tools.keytool.on": True,
        "tools.dbtool.on": True,
        "tools.filetool.on": True,
        }
    link_fmt = """<a href="{url}" target="_blank">{string}</a>"""

    def checkadmin(self):
        key_mgr = cherrypy.request.key
        meta, conn = cherrypy.request.db
        users = meta.tables[User.TABLE_NAME]
        cookie = cherrypy.request.cookie

        if "key" not in cookie:
            return False
        key = str(cookie["key"].value)

        key_valid = key_mgr.get_key(key)
        if not key_valid[0]:
            return False

        ss = select([users.c.type]).where(and_(
            users.c.id==key_valid[1],
            users.c.type==User.ADMIN))
        rst = conn.execute(ss)
        row = rst.fetchone()
        if not row:
            return False
        return True

    @cherrypy.expose
    def index(self):
        a = self.checkadmin()
        if not a:
            raise cherrypy.HTTPRedirect("/")

        return render("admin/admin.html")

    @cherrypy.expose
    def news(self, title=None, html=None):
        a = self.checkadmin()
        if not a:
            raise cherrypy.HTTPRedirect("/")

        return render("admin/adminnews.html")

    @cherrypy.expose
    def questions(self):
        a = self.checkadmin()
        if not a:
            raise cherrypy.HTTPRedirect("/")
            
        return render("admin/questions.html")

    @cherrypy.expose
    def files(self, file=None):
        file_mgr = cherrypy.request.file_mgr
        a = self.checkadmin()
        if not a:
            raise cherrypy.HTTPRedirect("/")

        if cherrypy.request.method == "POST":
            os.remove(file_mgr.get_download_path() + file)

        files = {}
        path = os.getcwd()
        if path.endswith("/"):
            path = path[:-1]
        for i, e, g in os.walk(path):
            if ".git" in i:
                continue
            if "__pycache__" in i:
                continue

            filepath = i.replace(path, "")
            if filepath == "":
                filepath = "/"
            files[filepath] = {}
            files[filepath]["dir"] = e
            files[filepath]["files"] = g

        return render("admin/files.html", {"files": files})

    @cherrypy.expose
    def users(self):
        a = self.checkadmin()
        if not a:
            raise cherrypy.HTTPRedirect("/")

        return render("admin/users.html")

    @cherrypy.expose
    def teacher(self):
        a = self.checkadmin()
        if not a:
            raise cherrypy.HTTPRedirect("/")

        return render("admin/teacher.html")

    # @cherrypy.expose
    # def activity(self):
    #     a = self.checkadmin()
    #     if not a:
    #         raise cherrypy.HTTPRedirect("/")

    #     return render("admin/activity.html")

    # @cherrypy.expose
    # def report(self):
    #     a = self.checkadmin()
    #     if not a:
    #         raise cherrypy.HTTPRedirect("/")

    #     return render("admin/report.html")

    # @cherrypy.expose
    # def presentation(self):
    #     a = self.checkadmin()
    #     if not a:
    #         raise cherrypy.HTTPRedirect("/")

    #     return render("admin/presentation.html")

    # @cherrypy.expose
    # def teacherinfo(self):
    #     a = self.checkadmin()
    #     if not a:
    #         raise cherrypy.HTTPRedirect("/")

    #     return render("admin/teacherinfo.html")
