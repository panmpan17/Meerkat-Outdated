import cherrypy
import logging, logging.config
import os
import json

class App():
    SITE_CONF = {
        # "server.socket_host": "0.0.0.0",
        "server.socket_host": "192.168.50.54",
        "server.socket_port": 80,
        "server.thread_pool": 100,
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

    def subsribe_plugin(self, path, euf, db_str):
        from cherryplugin.cherrpy_sa import SAPlugin, SATool
        from cherryplugin.session_mgr import KeyMgrPlugin, KeyMgrTool
        from cherryplugin.classes_load import ClassesTool
        from cherryplugin.email_valid import EmailValidPlugin, EmailValidTool
        from cherryplugin.file_mgr import FilePlugin, FileTool
        from cherryplugin.classroom_mgr import ClassroomMgrPlugin, ClassroomMgrTool

        import app.model as model

        tables = [
            (model.User, euf),
            model.Question,
            model.Answer,
            model.Post,
            # model.ClassManage,

            model.Teacher,
            model.TeacherInfo,
            model.Classroom,
            model.AdArea,
            model.AdClass,

            model.Activity,
            model.Report,
            ]

        sa_plugin = SAPlugin(cherrypy.engine, db_str=db_str, tables=tables)
        sa_plugin.subscribe()

        key_plugin = KeyMgrPlugin(cherrypy.engine)
        key_plugin.subscribe()

        classes_plugin = App.loadClasses()
        classes_plugin.subscribe()

        email_valid_plugin = EmailValidPlugin(cherrypy.engine)
        email_valid_plugin.subscribe()

        file_plugin = FilePlugin(cherrypy.engine, path)
        file_plugin.subscribe()

        clsrom_plugin = ClassroomMgrPlugin(cherrypy.engine, path)
        clsrom_plugin.subscribe()

        cherrypy.tools.keytool = KeyMgrTool(key_plugin)
        cherrypy.tools.classestool = ClassesTool(classes_plugin)
        cherrypy.tools.dbtool = SATool(sa_plugin)
        cherrypy.tools.emailvalidtool = EmailValidTool(email_valid_plugin)
        cherrypy.tools.filetool = FileTool(file_plugin)
        cherrypy.tools.clsromtool = ClassroomMgrTool(clsrom_plugin)

    def mount(self, handler, config):
        cherrypy.tree.mount(
            handler(),
            handler._root,
            config=config,
            )

    def start(self, db_str, path, euf):
        import app.rest as restapi
        import app.render as render
        import app.admin as admin

        self.site_conf = App.SITE_CONF

        if not path:
            path = os.getcwd() + "/downloads/"
        if not db_str:
            db_str = restapi.rest_config["db_connstr"]

        self.render_config["/downloads"]["tools.staticdir.root"] = path

        restview_config = {"/": restapi.rest_config}
        self.mount(restapi.SessionKeyRestView, restview_config)
        self.mount(restapi.QuestionRestView, restview_config)
        self.mount(restapi.AnswerRestView, restview_config)
        self.mount(restapi.ClassesRestView, restview_config)
        self.mount(restapi.UserRestView, restview_config)
        self.mount(restapi.PostRestView, restview_config)
        # self.mount(restapi.OpinionRestView, restview_config)
        self.mount(restapi.TeacherRestView, restview_config)
        self.mount(restapi.AdAreaRestView, restview_config)
        self.mount(restapi.AdClassRestView, restview_config)
        self.mount(restapi.ClassroomRestView, restview_config)
        self.mount(restapi.FileUploadRestView, restview_config)
        self.mount(restapi.ActivityRestView, restview_config)
        # self.mount(restapi.TeacherMergeView, restview_config)
        # self.mount(restapi.ReportRestView, restview_config)
        # self.mount(restapi.PresentationRestView, restview_config)
        
        self.mount(render.UserCaseHandler, self.render_config)
        self.mount(render.ClassHandler, self.render_config)
        self.mount(render.TeacherHandler, self.render_config)
        self.mount(admin.AdminHandler, self.render_config)

        self.subsribe_plugin(path, euf, db_str)

        cherrypy.config.update(self.site_conf)
        cherrypy.config.update(
            {"error_page.404": render.UserCaseHandler.error_404}
            )
        cherrypy.engine.start()
        cherrypy.engine.block()

    @classmethod
    def loadClasses(cls):
        from cherryplugin.classes_load import ClassesPlugin

        classes = ClassesPlugin(cherrypy.engine)

        dirname = "classes"
        files = ["scratch_1_update.json", "python_01_update.json", "scratch_02.json", "scratch_03.json"]

        for f in files:
            class_ = json.load(open(f"{dirname}/{f}", encoding="utf-8"))
            classes.new_class(class_["id"], class_)
        return classes

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
