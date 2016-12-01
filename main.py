import cherrypy
import logging, logging.config
import os
import json

class Function:

    @classmethod
    def loadClasses(cls, path):
        from cherryplugin.classes_load import ClassesPlugin

        classes = ClassesPlugin(cherrypy.engine, path)

        dirname = "classes"
        files = ["scratch_1.json", "hourofcode.json", "teacher_1.json", "python_01.json"]

        for f in files:
            file = open(dirname + "/" + f, "r")
            read = file.read()
            file.close()

            read = read.replace("'", "\"")

            class_ = json.loads(read)
            classes.new_class(class_["id"], class_)

        return classes

class App():
    SITE_CONF = {
        "server.socket_host": "0.0.0.0",
        "server.socket_port": 80,
        "server.thread_pool": 5,
        "server.max_request_body_size": 0, # no size limitation of body for chunked/streaming
        "server.socket_timeout": 3, # set socket timeout to 3 seconds    }
    }
    LOG_CONF = {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "void": {
                "format": "%(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "cherrypy_console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "void",
                "stream": "ext://sys.stdout"
            },
            "db_log": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": "db.log",
                "maxBytes": 1485760,
                "backupCount": 10,
                "encoding": "utf8"
            },
            "error_log": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": "error.log",
                "maxBytes": 1485760,
                "backupCount": 10,
                "encoding": "utf8"
            },
            "key_log": {
                "level": "NOTSET",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": "key.log",
                "maxBytes": 1485760,
                "backupCount": 10,
                "encoding": "utf8"
            },
            "loggers": {
                "": {
                    "handlers": ["cherrypy_console"],
                    "level": "NOTSET",
                },
                "app": {
                    "handlers": ["default"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "db": {
                    "handlers": ["db_log"],
                    "level": "INFO",
                    "propagate": False,
                },
                "error": {
                    "handlers": ["error_log"],
                    "level": "ERROR",
                    "propagate": False,
                },
                "key": {
                    "handlers": ["key_log"],
                    "level": "INFO",
                    "propagate": False,
                }
            }
        },

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

    def subsribe_plugin(self, path, euf):
        from cherryplugin.cherrpy_sa import SAPlugin, SATool
        from cherryplugin.session_mgr import KeyMgrPlugin, KeyMgrTool
        from cherryplugin.classes_load import ClassesTool
        from cherryplugin.email_mgr import EmailPlugin, EmailTool

        from app.model import User, Question, Answer, Post, Opinion, ClassManage

        tables = [
            (User, euf),
            Question,
            Answer,
            Post,
            Opinion,
            ClassManage,
            ]

        sa_plugin = SAPlugin(cherrypy.engine, db_str=db_str, tables=tables)
        sa_plugin.subscribe()
        cherrypy.tools.dbtool = SATool(sa_plugin)

        key_plugin = KeyMgrPlugin(cherrypy.engine)
        key_plugin.subscribe()
        cherrypy.tools.keytool = KeyMgrTool(key_plugin)

        classes_plugin = Function.loadClasses(path)
        classes_plugin.subscribe()
        cherrypy.tools.classestool = ClassesTool(classes_plugin)

        email_plugin = EmailPlugin(cherrypy.engine)
        email_plugin.subscribe()
        cherrypy.tools.emailtool = EmailTool(email_plugin)

    def start(self, db_str, path, euf):
        from app.rest import rest_config, UserRestView, SessionKeyView, AnswerRestView
        from app.rest import QuestionRestView, ClassesRestView, PostRestView, OpinionRestView
        from app.render import UserCaseHandler, ClassHandler
        from app.admin import AdminHandler

        self.site_conf = App.SITE_CONF
        # self.log_conf = App.LOG_CONF

        if not path:
            path = os.getcwd() + "/downloads/"

        if not db_str:
            db_str = rest_config["db_connstr"]

        self.render_config["/downloads"]["tools.staticdir.root"] = path
        cherrypy.tree.mount(SessionKeyView(), SessionKeyView._root, config={"/":rest_config})
        cherrypy.tree.mount(QuestionRestView(), QuestionRestView._root, config={"/":rest_config})
        cherrypy.tree.mount(AnswerRestView(), AnswerRestView._root, config={"/":rest_config})
        cherrypy.tree.mount(ClassesRestView(), ClassesRestView._root, 
            config={"/":rest_config})
        cherrypy.tree.mount(UserRestView(), UserRestView._root, config={"/":rest_config})
        cherrypy.tree.mount(PostRestView(), PostRestView._root, config={"/": rest_config})
        cherrypy.tree.mount(OpinionRestView(), OpinionRestView._root, config={"/": rest_config})

        cherrypy.tree.mount(UserCaseHandler(), UserCaseHandler._root, 
            config=self.render_config)
        cherrypy.tree.mount(ClassHandler(), ClassHandler._root, 
            config=self.render_config)
        cherrypy.tree.mount(AdminHandler(), AdminHandler._root,
            config=self.render_config)

        self.subsribe_plugin(path, euf)

        cherrypy.config.update(self.site_conf)
        cherrypy.engine.start()
        cherrypy.engine.block()

if __name__ == "__main__":
    import sys, argparse
    class dumy:
        pass
    
    psr = argparse.ArgumentParser(description='Start up demo app of Cherrypy.')
    psr.add_argument('-dbusr')
    psr.add_argument('-dbpsw')
    psr.add_argument('-dbhst')
    psr.add_argument('-dbprt')
    psr.add_argument('-dbname')
    psr.add_argument('-path')
    psr.add_argument('-euf')
    vs = dumy()
    psr.parse_args(sys.argv[1:], namespace=vs)

    if vs.dbusr or vs.dbpsw or vs.dbhst or vs.dbprt or vs.dbname:
        if not(vs.dbusr and vs.dbpsw and vs.dbhst and vs.dbprt and vs.dbname):
            print ("option dbusr, dbpsw, dbhst, dbprt, and dbname must specify altogether!")
            exit(1)
        db_str = "postgresql://{}:{}@{}:{}/{}?client_encoding=utf8".format(
            vs.dbusr, vs.dbpsw, vs.dbhst, vs.dbprt, vs.dbname)
    else:
        db_str = None

    web = App()
    if vs.euf == "/":
        vs.euf = None
    web.start(db_str, vs.path, vs.euf)








