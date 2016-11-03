import cherrypy
import jinja2
from app.model import User, Post
import os
import requests

#from sqlalchemy import desc
from sqlalchemy.sql import select, and_
#from sqlalchemy.exc import IntegrityError

jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader("html/template"))

def render(src, params):
    # print(os.getcwd())
    t = jinja_env.get_template(src)
    return t.render(params)

class AdminHandler(object):
    _root = "/admin/"
    _cp_config = {
        "tools.keytool.on": True,
        "tools.dbtool.on": True,
        "tools.classestool.on": True,
        }
    link_fmt = """<a href="{url}" target="_blank">{string}</a>"""

    @cherrypy.expose
    def index(self):
        meta, conn = cherrypy.request.db
        key_mgr = cherrypy.request.key
        users = meta.tables[User.TABLE_NAME]
        cookie = cherrypy.request.cookie

        res = AdminHandler.checkadmin(cookie, key_mgr, users, conn)
        if not res:
            raise cherrypy.HTTPRedirect("/")

        return render("admin/admin.html", {})

    @cherrypy.expose
    def news(self, title=None, html=None):
        meta, conn = cherrypy.request.db
        users = meta.tables[User.TABLE_NAME]
        key_mgr = cherrypy.request.key
        cookie = cherrypy.request.cookie

        res = AdminHandler.checkadmin(cookie, key_mgr, users, conn)
        if not res:
            raise cherrypy.HTTPRedirect("/")

        return render("admin/adminnews.html", {})

    @cherrypy.expose
    def questions(self):
        return render("admin/questions.html", {})

    @cherrypy.expose
    def users(self):
        meta, conn = cherrypy.request.db
        users = meta.tables[User.TABLE_NAME]
        key_mgr = cherrypy.request.key
        cookie = cherrypy.request.cookie
        
        res = AdminHandler.checkadmin(cookie, key_mgr, users, conn)
        if not res:
            raise cherrypy.HTTPRedirect("/")

        return render("admin/users.html", {})

    @classmethod
    def checkadmin(cls, cookie, key_mgr, users, conn):
        if "key" not in cookie:
            return False
        key = str(cookie["key"].value)

        key_valid = key_mgr.get_key(key)
        if not key_valid[0]:
            return False

        ss = select([users.c.admin]).where(and_(users.c.id == key_valid[1],
                users.c.admin == True))
        rst = conn.execute(ss)
        rows = rst.fetchall()
        if len(rows) < 1:
            return False

        if not rows[0]:
            return False
        return True






