import cherrypy
import jinja2
import os
import json
import requests
import json
import random

from cherrypy.process import plugins

jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader("offline/template"))
abs_cwd = os.path.join(os.getcwd(), os.path.dirname(__file__))

def render(src, params={}):
    t = jinja_env.get_template(src)
    return t.render(params)

class AdminUserPlugin(plugins.SimplePlugin):
    def __init__(self, bus, username, password):
        plugins.SimplePlugin.__init__(self, bus)
        self.username = username
        self.password = password
        self.code = ''.join([random.choice('0123456789ABCDEF') for x in range(6)])

class AdminUserTool(cherrypy.Tool):
    def __init__(self, adminuser):
        cherrypy.Tool.__init__(self, "on_start_resource",
            self.get_class_mgr,
            priority=10)
        self.adminuser = adminuser

    def get_plugin(self):
        return self.adminuser

    def get_class_mgr(self):
        cherrypy.request.adminuser = self.adminuser

class Handler(object):
    _root = "/"
    _cp_config = {
        "tools.classestool.on": True,
        "tools.adminuser.on": True,
        }

    @cherrypy.expose
    def index(self):
        classes = cherrypy.request.classes

        return render("index.html", {"classes": classes.get_class_all_info()})

    @cherrypy.expose
    def admin(self, *args, **kwargs):
        if cherrypy.request.method == "GET":
            return render("admin.html")
        elif cherrypy.request.method == "POST":
            admin = cherrypy.request.adminuser

            if "username" not in kwargs:
                return render("admin.html")
            if "password" not in kwargs:
                return render("admin.html")
            if kwargs["username"] != admin.username:
                return render("admin.html")
            if admin.password not in kwargs["password"]:
                return render("admin.html")

            return render("admin.html", {"code": admin.code})

    @cherrypy.expose
    def classes(self, *args, **kwargs):
        if len(args) < 1:
            raise cherrypy.HTTPRedirect("/")

        if cherrypy.request.method == "GET":
            return render("class.html")
        elif cherrypy.request.method == "POST":
            admin = cherrypy.request.adminuser
            classes = cherrypy.request.classes

            if "code" not in kwargs:
                return render("class.html")
            if kwargs["code"] != admin.code:
                print(2)
                return render("class.html")

            class_ = classes.get_class(args[0])

            return render("class.html", {"class": class_})

class App():
    SITE_CONF = {
        "server.socket_host": "0.0.0.0",
        "server.socket_port": 80,
        "server.thread_pool": 5,
        "server.max_request_body_size": 0, # no size limitation of body for chunked/streaming
        "server.socket_timeout": 3, # set socket timeout to 3 seconds    }
    }
    def __init__(self):
        self.render_config = {
            "/html": {
                "tools.staticdir.root": os.getcwd(),
                "tools.staticdir.on": True,
                "tools.staticdir.dir": "html",
            },
            "/downloads": {
                "tools.staticdir.root": "",
                "tools.staticdir.on": True,
                "tools.staticdir.dir": ".",
            },
        }

    def subsribe_plugin(self, path):
        from cherryplugin.classes_load import ClassesTool

        classes_plugin = App.loadClasses(path)
        classes_plugin.subscribe()
        cherrypy.tools.classestool = ClassesTool(classes_plugin)

        with open("offline/admin.json") as file:
            j = json.loads(file.read())
            print(j)

        adminuser = AdminUserPlugin(cherrypy.engine,
            j["username"],
            j["password"])
        adminuser.subscribe()
        cherrypy.tools.adminuser = AdminUserTool(adminuser)

    def mount(self, handler, config):
        cherrypy.tree.mount(
            handler(),
            handler._root,
            config=config,
            )

    def start(self):
        self.site_conf = App.SITE_CONF

        self.render_config["/downloads"]["tools.staticdir.root"] = "/downloads"

        self.mount(Handler, self.render_config)

        self.subsribe_plugin("/downloads")

        cherrypy.config.update(self.site_conf)
        cherrypy.engine.start()
        cherrypy.engine.block()

    @classmethod
    def loadClasses(cls, path):
        from cherryplugin.classes_load import ClassesPlugin

        classes = ClassesPlugin(cherrypy.engine, path)

        dirname = "classes"
        files = ["scratch_1.json", "teacher_1.json", "python_01.json"]

        for f in files:
            file = open(dirname + "/" + f, "r")
            read = file.read()
            file.close()

            read = read.replace("'", "\"")

            class_ = json.loads(read)
            classes.new_class(class_["id"], class_)
        return classes

if __name__ == "__main__":
    web = App()
    web.start()
